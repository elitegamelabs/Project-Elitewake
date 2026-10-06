#include "EWCharacterMovementComponent.h"
#include "EWCharacter.h"
#include "EW.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

namespace
{
    class FEWClientPredictionData : public FNetworkPredictionData_Client_Character
    {
    public:
        explicit FEWClientPredictionData(const UCharacterMovementComponent& Movement)
            : FNetworkPredictionData_Client_Character(Movement) {}
        virtual FSavedMovePtr AllocateNewMove() override { return FSavedMovePtr(new FEWSavedMove()); }
    };
}

FVector UEWCharacterMovementComponent::BodyCenter(const FVector& Location, float HalfHeight) const
{
    // A small floor skin keeps the horizontal body query clear of its supporting surface.
    return Location + FVector(0, 0, ProneCapsuleRadius - HalfHeight + 2.f);
}

FQuat UEWCharacterMovementComponent::BodyRotation(const FQuat& ActorRotation) const
{
    const FVector FloorNormal = CurrentFloor.IsWalkableFloor() ? CurrentFloor.HitResult.ImpactNormal : FVector::UpVector;
    // Keep the floor normal fixed; project facing onto its plane. Keeping X fixed
    // would discard an incline along the facing direction and leave the body flat.
    return FRotationMatrix::MakeFromZX(FloorNormal, ActorRotation.GetAxisX()).ToQuat()
        * FQuat(FVector::YAxisVector, PI * 0.5f);
}

bool UEWCharacterMovementComponent::BodyBlocked(const FVector& Location, const FQuat& Rotation, float HalfHeight) const
{
    const UCapsuleComponent* Capsule = CharacterOwner->GetCapsuleComponent();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWProneClearance), false, CharacterOwner);
    return GetWorld()->OverlapBlockingTestByChannel(BodyCenter(Location, HalfHeight), BodyRotation(Rotation),
        Capsule->GetCollisionObjectType(), FCollisionShape::MakeCapsule(ProneCapsuleRadius, ProneBodyHalfLength),
        Query, FCollisionResponseParams(Capsule->GetCollisionResponseToChannels()));
}

bool UEWCharacterMovementComponent::ResizeStance(bool bProne, bool bStanding, bool bClientSimulation)
{
    if (!HasValidData()) return false;
    AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner);
    if (!Character) return false;
    UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const ACharacter* Defaults = Character->GetClass()->GetDefaultObject<ACharacter>();
    const float DefaultRadius = Defaults->GetCapsuleComponent()->GetUnscaledCapsuleRadius();
    const float DefaultHeight = Defaults->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
    const float Radius = bProne ? ProneCapsuleRadius : DefaultRadius;
    const float HalfHeight = bStanding ? DefaultHeight : FMath::Max(Radius, bProne ? ProneCapsuleRadius : CrouchClearanceHalfHeight);
    const float OldHeight = Capsule->GetUnscaledCapsuleHalfHeight();
    const float Scale = Capsule->GetShapeScale();
    const FVector OldLocation = UpdatedComponent->GetComponentLocation();
    const FVector NewLocation = OldLocation + FVector(0, 0, (HalfHeight - OldHeight) * Scale);

    if (!bClientSimulation)
    {
        FCollisionQueryParams Query(SCENE_QUERY_STAT(EWStanceClearance), false, Character);
        const FCollisionShape Shape = FCollisionShape::MakeCapsule(FMath::Max(1.f, Radius * Scale - 0.5f),
            FMath::Max(1.f, HalfHeight * Scale - 0.5f));
        const bool bCapsuleBlocked = GetWorld()->OverlapBlockingTestByChannel(NewLocation, FQuat::Identity,
            Capsule->GetCollisionObjectType(), Shape, Query, FCollisionResponseParams(Capsule->GetCollisionResponseToChannels()));
        const bool bBodyBlocked = bProne && BodyBlocked(NewLocation, UpdatedComponent->GetComponentQuat(), HalfHeight * Scale);
        if (bCapsuleBlocked || bBodyBlocked)
        {
            UE_LOG(LogEW, Verbose, TEXT("EW stance rejected: capsule=%d body=%d center=%s floorNormal=%s"),
                bCapsuleBlocked, bBodyBlocked, *NewLocation.ToString(), *CurrentFloor.HitResult.ImpactNormal.ToString());
            return false;
        }
    }

    const bool bChanged = !FMath::IsNearlyEqual(OldHeight, HalfHeight)
        || !FMath::IsNearlyEqual(Capsule->GetUnscaledCapsuleRadius(), Radius)
        || Character->IsProne() != bProne || Character->IsCrouched() == bStanding;
    if (!bChanged) return true;

    Capsule->SetCapsuleSize(Radius, HalfHeight, true);
    // Simulated proxies receive their center location through replicated movement.
    if (!bClientSimulation)
        UpdatedComponent->MoveComponent(NewLocation - OldLocation, UpdatedComponent->GetComponentQuat(), false);
    Character->SetIsCrouched(!bStanding);
    Character->SetProneFromMovement(bProne);
    if (bStanding)
        Character->OnEndCrouch(DefaultHeight - OldHeight, (DefaultHeight - OldHeight) * Scale);
    else
        Character->OnStartCrouch(DefaultHeight - HalfHeight, (DefaultHeight - HalfHeight) * Scale);
    bForceNextFloorCheck = true;

    if (bClientSimulation || (GetNetMode() == NM_ListenServer && Character->GetRemoteRole() == ROLE_AutonomousProxy))
    {
        if (FNetworkPredictionData_Client_Character* Data = GetPredictionData_Client_Character())
        {
            Data->MeshTranslationOffset.Z -= (OldHeight - HalfHeight) * Scale;
            Data->OriginalMeshTranslationOffset = Data->MeshTranslationOffset;
        }
    }
    if (StandingStepHeight < 0.f) StandingStepHeight = MaxStepHeight;
    MaxStepHeight = bProne ? 0.f : StandingStepHeight;
    return true;
}

void UEWCharacterMovementComponent::Crouch(bool bClientSimulation)
{
    if (!HasValidData() || (!bClientSimulation && !CanCrouchInCurrentState())) return;
    if (!bClientSimulation && CharacterOwner->GetLocalRole() == ROLE_SimulatedProxy) return;
    const AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner);
    const bool bProne = bClientSimulation ? Character && Character->IsProne() : bWantsToProne;
    if (!ResizeStance(bProne, false, bClientSimulation) && !bClientSimulation)
    {
        // A blocked entry leaves the existing stance intact; it must not play a prone pose.
        bWantsToProne = Character && Character->IsProne();
        bWantsToCrouch = CharacterOwner->IsCrouched();
    }
}

void UEWCharacterMovementComponent::UnCrouch(bool bClientSimulation)
{
    if (CharacterOwner && !bClientSimulation && CharacterOwner->GetLocalRole() == ROLE_SimulatedProxy) return;
    if (!ResizeStance(false, true, bClientSimulation) && !bClientSimulation)
    {
        bWantsToCrouch = true;
        bWantsToProne = CastChecked<AEWCharacter>(CharacterOwner)->IsProne();
    }
}

void UEWCharacterMovementComponent::UpdateCharacterStateBeforeMovement(float DeltaSeconds)
{
    SetCrouchedHalfHeight(CrouchClearanceHalfHeight);
    if (CharacterOwner && CharacterOwner->GetLocalRole() == ROLE_SimulatedProxy)
    {
        // Remote pawns have no local saved-move intent. Only replicated accepted
        // state may select their stance; default false intent must not clear prone.
        RefreshProxyStance();
        return;
    }
    // Prone entry requires supported ground, rather than changing the capsule in midair.
    const AEWCharacter* Owner = Cast<AEWCharacter>(CharacterOwner);
    if (bWantsToProne && !IsMovingOnGround() && (!Owner || !Owner->IsProne()))
    {
        bWantsToProne = false;
        bWantsToCrouch = Owner && Owner->IsCrouched();
    }
    if (HasValidData() && CharacterOwner->IsCrouched() && bWantsToCrouch)
    {
        const AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner);
        if (Character && Character->IsProne() != bWantsToProne)
            Crouch();
    }
    Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);
}

void UEWCharacterMovementComponent::RefreshProxyStance()
{
    const AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner);
    if (Character && Character->GetLocalRole() == ROLE_SimulatedProxy)
        ResizeStance(Character->IsProne(), !Character->IsCrouched() && !Character->IsProne(), true);
}

bool UEWCharacterMovementComponent::MoveUpdatedComponentImpl(const FVector& Delta, const FQuat& NewRotation,
    bool bSweep, FHitResult* OutHit, ETeleportType Teleport)
{
    const AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner);
    if (!Character || !Character->IsProne() || Teleport != ETeleportType::None || (!bSweep && !Delta.IsNearlyZero()))
        return Super::MoveUpdatedComponentImpl(Delta, NewRotation, bSweep, OutHit, Teleport);

    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const FVector Start = UpdatedComponent->GetComponentLocation();
    const FQuat OldRotation = UpdatedComponent->GetComponentQuat();
    const float HalfHeight = Capsule->GetScaledCapsuleHalfHeight();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWProneBodySweep), false, Character);
    FHitResult BodyHit;
    const bool bBodyHit = GetWorld()->SweepSingleByChannel(BodyHit, BodyCenter(Start, HalfHeight),
        BodyCenter(Start + Delta, HalfHeight), BodyRotation(OldRotation), Capsule->GetCollisionObjectType(),
        FCollisionShape::MakeCapsule(ProneCapsuleRadius, ProneBodyHalfLength), Query,
        FCollisionResponseParams(Capsule->GetCollisionResponseToChannels()));
    const float AllowedTime = bBodyHit ? FMath::Max(0.f, BodyHit.Time - 0.001f) : 1.f;
    FQuat AllowedRotation = NewRotation;
    // Rotational sweeps are not provided by the root capsule; check intermediate body orientations.
    const int32 RotationSteps = FMath::Max(1, FMath::CeilToInt(FMath::RadiansToDegrees(OldRotation.AngularDistance(NewRotation)) / 5.f));
    for (int32 Index = 1; Index <= RotationSteps; ++Index)
    {
        if (BodyBlocked(Start + Delta * AllowedTime, FQuat::Slerp(OldRotation, NewRotation, float(Index) / RotationSteps), HalfHeight))
        {
            AllowedRotation = OldRotation;
            break;
        }
    }
    FHitResult RootHit;
    const bool bMoved = Super::MoveUpdatedComponentImpl(Delta * AllowedTime, AllowedRotation, bSweep, &RootHit, Teleport);
    if (OutHit)
    {
        *OutHit = RootHit;
        OutHit->Time *= AllowedTime;
        if (bBodyHit && !RootHit.bBlockingHit)
        {
            *OutHit = BodyHit;
            OutHit->Time = AllowedTime;
            OutHit->Location = Start + Delta * AllowedTime;
            OutHit->TraceStart = Start;
            OutHit->TraceEnd = Start + Delta;
        }
    }
    return bMoved;
}

void UEWCharacterMovementComponent::UpdateFromCompressedFlags(uint8 Flags)
{
    Super::UpdateFromCompressedFlags(Flags);
    bWantsToProne = (Flags & FSavedMove_Character::FLAG_Custom_0) != 0;
    if (AEWCharacter* Character = Cast<AEWCharacter>(CharacterOwner))
    {
        Character->bSprintInputHeld = (Flags & FSavedMove_Character::FLAG_Custom_1) != 0;
        // Match the owning client's jump clearance before server jump processing.
        if ((Flags & FSavedMove_Character::FLAG_JumpPressed) && !bWantsToCrouch && Character->IsCrouched())
            UnCrouch();
    }
}

FNetworkPredictionData_Client* UEWCharacterMovementComponent::GetPredictionData_Client() const
{
    if (!ClientPredictionData)
        const_cast<UEWCharacterMovementComponent*>(this)->ClientPredictionData = new FEWClientPredictionData(*this);
    return ClientPredictionData;
}

void FEWSavedMove::Clear() { Super::Clear(); bSavedWantsToProne = false; bSavedSprintInputHeld = false; }
uint8 FEWSavedMove::GetCompressedFlags() const
{
    return Super::GetCompressedFlags() | (bSavedWantsToProne ? FLAG_Custom_0 : 0)
        | (bSavedSprintInputHeld ? FLAG_Custom_1 : 0);
}
bool FEWSavedMove::CanCombineWith(const FSavedMovePtr& NewMove, ACharacter* Character, float MaxDelta) const
{
    return bSavedWantsToProne == static_cast<const FEWSavedMove*>(NewMove.Get())->bSavedWantsToProne
        && bSavedSprintInputHeld == static_cast<const FEWSavedMove*>(NewMove.Get())->bSavedSprintInputHeld
        && Super::CanCombineWith(NewMove, Character, MaxDelta);
}
void FEWSavedMove::SetMoveFor(ACharacter* Character, float InDeltaTime, const FVector& NewAcceleration,
    FNetworkPredictionData_Client_Character& ClientData)
{
    Super::SetMoveFor(Character, InDeltaTime, NewAcceleration, ClientData);
    bSavedWantsToProne = CastChecked<UEWCharacterMovementComponent>(Character->GetCharacterMovement())->bWantsToProne;
    bSavedSprintInputHeld = CastChecked<AEWCharacter>(Character)->bSprintInputHeld;
}
void FEWSavedMove::PrepMoveFor(ACharacter* Character)
{
    Super::PrepMoveFor(Character);
    CastChecked<UEWCharacterMovementComponent>(Character->GetCharacterMovement())->bWantsToProne = bSavedWantsToProne;
    CastChecked<AEWCharacter>(Character)->bSprintInputHeld = bSavedSprintInputHeld;
}
