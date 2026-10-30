#include "Wildlife/EWAnimal.h"
#include "Wildlife/EWAnimalDefinition.h"
#include "EWCharacter.h"
#include "Ships/EWShip.h"
#include "EWProgressionComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWSound.h"
#include "Gathering/EWHarvestTree.h"
#include "Sound/SoundBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"
#include "World/EWSafeZone.h"

AEWAnimal::AEWAnimal()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicatingMovement(true);
    SetNetUpdateFrequency(10.f);
    Body = CreateDefaultSubobject<USphereComponent>(TEXT("Body"));
    RootComponent = Body;
    // Only aim finds it (to strike or harvest it); nothing walks into it.
    Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Body->SetCollisionObjectType(ECC_WorldDynamic);
    Body->SetCollisionResponseToAllChannels(ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Body->InitSphereRadius(25.f);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Body);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AEWAnimal::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWAnimal, Definition);
    DOREPLIFETIME(AEWAnimal, Health);
    DOREPLIFETIME(AEWAnimal, Rider);
    DOREPLIFETIME(AEWAnimal, Action);
    DOREPLIFETIME(AEWAnimal, bDead);
    DOREPLIFETIME(AEWAnimal, bHarvested);
}

void AEWAnimal::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyDefinition();
}

void AEWAnimal::ApplyDefinition()
{
    if (!Definition) return;
    Visual->SetStaticMesh(Definition->Mesh.LoadSynchronous());
    // The actor stands on its feet; the aiming sphere sits on the body, big enough to hit anywhere along it.
    const float Radius = FMath::Max3(float(Definition->Size.Y * .5f), float(Definition->Size.X * .3f), 15.f);
    Body->SetSphereRadius(Radius);
    Visual->SetRelativeLocation(FVector(0, 0, -Radius + Definition->MeshFootLift));
    Visual->SetRelativeScale3D(FVector(Definition->MeshScale));
    Visual->SetRelativeRotation(Definition->MeshRotation);
}

void AEWAnimal::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
    Home = RoamPoint = GetActorLocation();
    // No hostile creature lives inside a free port.
    if (HasAuthority() && Definition && Definition->bAggressive && AEWSafeZone::KeepsHostilesOut(this, Home))
    {
        Destroy();
        return;
    }
    LastShown = GetActorLocation();
    if (HasAuthority() && Definition) Health = Definition->MaxHealth;
    RestSeconds = FMath::FRandRange(0.f, 4.f);
    if (Definition) CallSeconds = FMath::FRandRange(0.f, Definition->CallInterval.Y);
    OnRep_State();
}

void AEWAnimal::OnRep_State()
{
    Visual->SetVisibility(!bHarvested);
    Body->SetCollisionEnabled(bHarvested ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryOnly);
    Visual->SetCustomPrimitiveDataFloat(2, bDead ? 1.f : 0.f);
    // Dead, it lies on its side.
    Visual->SetRelativeRotation(FQuat(FRotator(0, 0, bDead ? 80.f : 0.f)) * FQuat(Definition ? Definition->MeshRotation : FRotator::ZeroRotator));
}

void AEWAnimal::PostNetReceiveLocationAndRotation()
{
    const FTransform Shown = GetActorTransform();
    Super::PostNetReceiveLocationAndRotation();
    NetPose = GetActorTransform();
    if (!bHasNetPose || FVector::Dist(Shown.GetLocation(), NetPose.GetLocation()) > 600.f)
    {
        bHasNetPose = true;
        return;
    }
    SetActorTransform(Shown);
}

void AEWAnimal::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Rest.IsAwake(this, DeltaSeconds))
    {
        // Resting far from everyone; a body still returns home in its time.
        if (HasAuthority() && bDead && Definition && (DeadSeconds += DeltaSeconds) >= Definition->RespawnSeconds) Respawn();
        return;
    }
    if (HasAuthority()) Think(DeltaSeconds);
    else if (bHasNetPose)
    {
        FTransform Shown;
        Shown.Blend(GetActorTransform(), NetPose, 1.f - FMath::Exp(-8.f * DeltaSeconds));
        SetActorTransform(Shown);
    }
    Animate(DeltaSeconds);
}

void AEWAnimal::Animate(float DeltaSeconds)
{
    if (!Definition || DeltaSeconds <= 0.f) return;
    const FVector Here = GetActorLocation();
    const float Moved = FVector::Dist2D(Here, LastShown) / DeltaSeconds;
    LastShown = Here;
    ShownSpeed = bDead ? 0.f : FMath::FInterpTo(ShownSpeed, FMath::Min(Moved, Definition->RunSpeed * 1.5f), DeltaSeconds, 6.f);
    // The stride advances with the ground covered, so feet do not slide.
    StridePhase = FMath::Fmod(StridePhase + ShownSpeed / FMath::Max(Definition->StrideLength, 1.f) * 2.f * PI * DeltaSeconds, 2.f * PI);
    Visual->SetCustomPrimitiveDataFloat(0, StridePhase);
    Visual->SetCustomPrimitiveDataFloat(1, FMath::Clamp(ShownSpeed / FMath::Max(Definition->WalkSpeed * .6f, 1.f), 0.f, 1.f));
    // A struck animal shudders.
    FlinchSeconds = FMath::Max(0.f, FlinchSeconds - DeltaSeconds);
    if (!bDead)
    {
        // A generated model is one rigid mesh with no legs to move: it rocks and bobs in time with its stride instead.
        const bool bRigid = Definition->MeshFootLift > 0.f;
        const float Walking = bRigid ? FMath::Clamp(ShownSpeed / FMath::Max(Definition->WalkSpeed * .6f, 1.f), 0.f, 1.f) : 0.f;
        // Postures ease in and out: head bowed to graze, body lowered to lie down.
        GrazeShown = FMath::FInterpTo(GrazeShown, Action == EEWAnimalAction::Graze ? 1.f : 0.f, DeltaSeconds, 2.5f);
        LieShown = FMath::FInterpTo(LieShown, Action == EEWAnimalAction::Rest ? 1.f : 0.f, DeltaSeconds, 1.5f);
        const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
        const float Roll = FMath::Sin(StridePhase) * 2.6f * Walking;
        const float Pitch = FMath::Sin(StridePhase * 2.f) * 1.4f * Walking - GrazeShown * (20.f + FMath::Sin(float(Now) * 2.2f) * 4.f);     // nose down, bobbing (tuning)
        const float Shudder = FlinchSeconds > 0.f ? FMath::Sin(FlinchSeconds * 60.f) * 10.f : 0.f;
        Visual->SetRelativeRotation(FQuat(FRotator(Pitch, Shudder, Roll)) * FQuat(Definition->MeshRotation));
        const float Radius = FMath::Max3(float(Definition->Size.Y * .5f), float(Definition->Size.X * .3f), 15.f);
        const float Bob = bRigid ? FMath::Abs(FMath::Sin(StridePhase)) * 1.8f * Walking : 0.f;
        Visual->SetRelativeLocation(FVector(0, 0, -Radius + Definition->MeshFootLift + Bob - LieShown * Definition->Size.Y * .28f));
    }
}

bool AEWAnimal::IsAshore(const AEWCharacter* Survivor) const
{
    return IsValid(Survivor) && Survivor->GetCharacterMovement() && !Survivor->GetCharacterMovement()->IsSwimming()
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0.f;
}

bool AEWAnimal::GroundAt(const FVector& At, float& OutZ) const
{
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWAnimalGround), false, this);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    FHitResult Hit;
    const FVector From(At.X, At.Y, At.Z + 250.f);
    if (!GetWorld()->LineTraceSingleByObjectType(Hit, From, From - FVector(0, 0, 1500.f), FCollisionObjectQueryParams(ECC_WorldStatic), Query))
        return false;
    OutZ = Hit.ImpactPoint.Z;
    return OutZ > SurfaceZ - Definition->WadeDepth;
}

FVector AEWAnimal::PickRoamPoint() const
{
    for (int32 Try = 0; Try < 10; ++Try)
    {
        const FVector2D Offset = FMath::RandPointInCircle(Definition->RoamRadius);
        FVector Point(Home.X + Offset.X, Home.Y + Offset.Y, Home.Z);
        float Z;
        if (GroundAt(Point, Z)) { Point.Z = Z; return Point; }
    }
    return Home;
}

FVector AEWAnimal::Repulsion() const
{
    // Animals give each other room: push away from any other live animal inside twice their lengths.
    FVector Push = FVector::ZeroVector;
    const float Room = Definition->Size.X * 1.6f;
    for (TActorIterator<AEWAnimal> It(GetWorld()); It; ++It)
    {
        if (*It == this || It->bDead) continue;
        const FVector Away = GetActorLocation() - It->GetActorLocation();
        const float Distance = Away.Size2D();
        if (Distance < Room && Distance > 1.f) Push += Away.GetSafeNormal2D() * (1.f - Distance / Room);
    }
    return Push;
}

bool AEWAnimal::WalkToward(const FVector& Target, float Speed, float DeltaSeconds)
{
    const float Radius = Body->GetUnscaledSphereRadius();
    const FVector Feet = GetActorLocation() - FVector(0, 0, Radius);
    FVector Heading = (Target - Feet).GetSafeNormal2D();
    if (Action != EEWAnimalAction::Chase) Heading = (Heading + Repulsion() * .8f).GetSafeNormal2D();
    const FRotator Want = Heading.Rotation();
    FRotator Facing = GetActorRotation();
    Facing.Yaw = FMath::FixedTurn(Facing.Yaw, Want.Yaw, Definition->TurnRate * DeltaSeconds);
    Facing.Pitch = Facing.Roll = 0.f;
    // Slow while turning hard, so it turns on the spot rather than circling.
    const float Ahead = FVector::DotProduct(Facing.Vector(), Heading);
    const FVector Step = Facing.Vector() * Speed * FMath::Clamp(Ahead, .15f, 1.f) * DeltaSeconds;
    float Z;
    if (!GroundAt(Feet + Step, Z) || FMath::Abs(Z - Feet.Z) > FMath::Max(60.f, Step.Size() * 3.f))
    {
        SetActorRotation(Facing);
        return false;
    }
    SetActorLocationAndRotation(FVector(Feet.X + Step.X, Feet.Y + Step.Y, Z + Radius), Facing);
    return true;
}

void AEWAnimal::Think(float DeltaSeconds)
{
    if (!Definition) return;
    if (bDead)
    {
        DeadSeconds += DeltaSeconds;
        if (DeadSeconds >= Definition->RespawnSeconds) Respawn();
        return;
    }
    if (IsValid(Rider)) { ThinkRidden(DeltaSeconds); return; }
    AttackCooldown -= DeltaSeconds;
    FleeSeconds -= DeltaSeconds;
    if (Definition->CallInterval.Y > 0.f && (CallSeconds -= DeltaSeconds) <= 0.f)
    {
        CallSeconds = FMath::FRandRange(Definition->CallInterval.X, Definition->CallInterval.Y);
        Call();
    }
    if (Definition->bAggressive)
    {
        AEWCharacter* Target = Quarry.Get();
        // A free port's bounds end the hunt: nobody inside is quarry, and the hunter turns back at the edge.
        if (Target && (!IsAshore(Target) || FVector::Dist(Target->GetActorLocation(), GetActorLocation()) > Definition->NoticeRange * 1.6f
            || AEWSafeZone::KeepsHostilesOut(this, Target->GetActorLocation())))
            Target = nullptr;
        if (!Target)
        {
            float Best = Definition->NoticeRange;
            for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It)
            {
                const float Distance = FVector::Dist(It->GetActorLocation(), GetActorLocation());
                if (Distance < Best && IsAshore(*It) && !AEWSafeZone::KeepsHostilesOut(this, It->GetActorLocation())) { Best = Distance; Target = *It; }
            }
        }
        // Going for someone, it warns them first.
        if (Target && !Quarry.IsValid()) Call();
        Quarry = Target;
        if (Target)
        {
            Action = EEWAnimalAction::Chase;
            const FVector Nose = GetActorLocation() + GetActorForwardVector() * Definition->Size.X * .5f;
            if (FVector::Dist2D(Nose, Target->GetActorLocation()) > Definition->AttackReach * .6f)
                WalkToward(Target->GetActorLocation(), Definition->RunSpeed, DeltaSeconds);
            if (AttackCooldown <= 0.f && FVector::Dist(Nose, Target->GetActorLocation()) < Definition->AttackReach + 70.f)
            {
                AttackCooldown = Definition->AttackInterval;
                Target->GetSurvivalComponent()->ApplyDamage(Definition->AttackDamage);
                Target->ReactToHit();
            }
            return;
        }
    }
    if (FleeSeconds > 0.f && FleeFrom.IsValid())
    {
        Action = EEWAnimalAction::Flee;
        const FVector Away = (GetActorLocation() - FleeFrom->GetActorLocation()).GetSafeNormal2D();
        if (!WalkToward(GetActorLocation() + Away * 800.f, Definition->RunSpeed, DeltaSeconds))
            WalkToward(GetActorLocation() + FVector(-Away.Y, Away.X, 0.f) * 800.f, Definition->RunSpeed, DeltaSeconds);
        return;
    }
    // Wander: walk to a spot, stand a while (graze, look about, lie down), walk on.
    if (RestSeconds > 0.f)
    {
        RestSeconds -= DeltaSeconds;
        if (Action == EEWAnimalAction::Rest)
            for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It)
                if (FVector::Dist(It->GetActorLocation(), GetActorLocation()) < 500.f) { RestSeconds = 0.f; break; }      // someone comes close: it gets up
        if (Action == EEWAnimalAction::Look)
        {
            FRotator Facing = GetActorRotation();
            Facing.Yaw = FMath::FixedTurn(Facing.Yaw, LookYaw, Definition->TurnRate * .5f * DeltaSeconds);
            SetActorRotation(Facing);
        }
        if (RestSeconds > 0.f) return;
    }
    if (Action != EEWAnimalAction::Wander) Action = EEWAnimalAction::Wander;
    if (Definition->bPushesTrees) PushTrees(DeltaSeconds);
    RoamSeconds -= DeltaSeconds;
    const bool bArrived = FVector::Dist2D(RoamPoint, GetActorLocation()) < FMath::Max(60.f, Definition->Size.X * .4f);
    if (bArrived || RoamSeconds <= 0.f || !WalkToward(RoamPoint, Definition->WalkSpeed, DeltaSeconds))
    {
        RoamPoint = PickRoamPoint();
        RoamSeconds = 20.f;
        if (bArrived) ChooseIdle();
    }
}

FVector AEWAnimal::GetRideSeatLocal(float RiderHalfHeight) const
{
    const float Radius = Body->GetUnscaledSphereRadius();
    return FVector(Definition ? Definition->RideSeatForward : 0.f, 0.f, (Definition ? Definition->RideSeatHeight : 100.f) - Radius + RiderHalfHeight);
}

bool AEWAnimal::CanRide(const AEWCharacter* Character) const
{
    return IsValid(Character) && Definition && Definition->bRideable && !bDead && !IsValid(Rider) && !Character->IsMounted()
        && !IsValid(Character->GetHelmShip()) && !IsValid(Character->GetGunShip()) && !Character->IsOnLadder()
        && Character->GetSurvivalComponent() && Character->GetSurvivalComponent()->GetHealth() > 0.f
        && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) < Definition->RideReach + Definition->Size.X * .5f;
}

void AEWAnimal::SetRideSteer(AEWCharacter* Who, FVector2D Direction)
{
    if (!HasAuthority() || Who != Rider) return;
    RideDirection = Direction.GetClampedToMaxSize(1.f);
    RideSteerAge = 0.f;
}

void AEWAnimal::ThinkRidden(float DeltaSeconds)
{
    if (Rider->IsDead()) { Dismount(); return; }
    Quarry = nullptr;
    FleeSeconds = 0.f;
    // A steering order the rider stopped sending (a lost packet) lapses after half a second, so it never runs away with them.
    if ((RideSteerAge += DeltaSeconds) > .5f) RideDirection = FVector2D::ZeroVector;
    const float Power = RideDirection.Size();
    if (Power < .05f) { Action = EEWAnimalAction::Wander; return; }
    Action = EEWAnimalAction::Chase;
    const FVector Feet = GetActorLocation() - FVector(0, 0, Body->GetUnscaledSphereRadius());
    WalkToward(Feet + FVector(RideDirection.X, RideDirection.Y, 0.f).GetSafeNormal() * 400.f, Definition->RunSpeed * Power, DeltaSeconds);
}

void AEWAnimal::Dismount()
{
    if (!HasAuthority()) return;
    AEWCharacter* Who = Rider;
    Rider = nullptr;
    RideDirection = FVector2D::ZeroVector;
    ForceNetUpdate();
    if (!IsValid(Who)) return;
    Who->SetMount(nullptr);
    // Off to its side, on the ground.
    const float Radius = Body->GetUnscaledSphereRadius();
    const FVector Side = GetActorRightVector() * (Definition ? Definition->Size.Y * .5f + 110.f : 150.f);
    FVector Where = GetActorLocation() + Side;
    float Z;
    if (GroundAt(Where, Z)) Where.Z = Z + Who->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.f;
    else Where = GetActorLocation() + FVector(0, 0, Radius + 150.f);
    Who->TeleportTo(Where, FRotator(0.f, GetActorRotation().Yaw, 0.f));
    Who->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
}

void AEWAnimal::PushTrees(float DeltaSeconds)
{
    if ((TreePushCooldown -= DeltaSeconds) > 0.f) return;
    const FVector Nose = GetActorLocation() + GetActorForwardVector() * Definition->Size.X * .5f;
    AEWHarvestTree* Best = nullptr;
    float BestDistance = Definition->TreePushReach;
    for (TActorIterator<AEWHarvestTree> It(GetWorld()); It; ++It)
    {
        if (It->IsFelled() || It->IsActorBeingDestroyed()) continue;
        const FVector To = It->GetActorLocation() - Nose;
        const float Distance = To.Size2D();
        if (Distance < BestDistance && FVector::DotProduct(To.GetSafeNormal2D(), GetActorForwardVector()) > .2f) { Best = *It; BestDistance = Distance; }
    }
    if (!Best) { TreePushCooldown = 1.f; return; }      // nothing in front: look again soon
    if (Best->Fell(Best->GetActorLocation() - GetActorLocation()))      // stays down (not removed) so it can be chopped for wood
    {
        Call();
        TreePushCooldown = FMath::FRandRange(Definition->TreePushSeconds.X, Definition->TreePushSeconds.Y);
    }
    else TreePushCooldown = 1.f;
}

void AEWAnimal::ChooseIdle()
{
    const float Graze = Definition->bAggressive ? 0.f : Definition->GrazeOdds;
    bool bSurvivorNear = false;
    for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It)
        if (FVector::Dist(It->GetActorLocation(), GetActorLocation()) < 1500.f) { bSurvivorNear = true; break; }
    const float LieOdds = bSurvivorNear ? 0.f : Definition->RestOdds;
    const float Look = Definition->LookOdds;
    float Roll = FMath::FRandRange(0.f, FMath::Max(Graze + Look + LieOdds, .01f));
    if ((Roll -= Graze) < 0.f) { Action = EEWAnimalAction::Graze; RestSeconds = FMath::FRandRange(Definition->GrazeSeconds.X, Definition->GrazeSeconds.Y); }
    else if ((Roll -= Look) < 0.f)
    {
        Action = EEWAnimalAction::Look;
        LookYaw = GetActorRotation().Yaw + FMath::FRandRange(-120.f, 120.f);
        RestSeconds = FMath::FRandRange(Definition->LookSeconds.X, Definition->LookSeconds.Y);
    }
    else if (LieOdds > 0.f) { Action = EEWAnimalAction::Rest; RestSeconds = FMath::FRandRange(Definition->LieSeconds.X, Definition->LieSeconds.Y); }
    else { Action = EEWAnimalAction::Look; LookYaw = GetActorRotation().Yaw + FMath::FRandRange(-90.f, 90.f); RestSeconds = FMath::FRandRange(2.f, 5.f); }
}

AEWAnimal* AEWAnimal::FindStruck(const AEWCharacter* Striker, float Reach)
{
    if (!IsValid(Striker) || !Striker->GetWorld()) return nullptr;
    FVector Eye; FRotator View;
    Striker->GetActorEyesViewPoint(Eye, View);
    const FVector From = Striker->GetActorLocation() + FVector(0, 0, Striker->BaseEyeHeight * .5f);
    const FVector To = From + View.Vector() * Reach;
    AEWAnimal* Best = nullptr;
    float BestAlong = TNumericLimits<float>::Max();
    for (TActorIterator<AEWAnimal> It(Striker->GetWorld()); It; ++It)
    {
        AEWAnimal* Animal = *It;
        if (Animal->bDead || !Animal->Definition) continue;
        const FVector Spine = Animal->GetActorForwardVector() * Animal->Definition->Size.X * .5f;
        FVector OnSwing, OnSpine;
        FMath::SegmentDistToSegmentSafe(From, To, Animal->GetActorLocation() - Spine, Animal->GetActorLocation() + Spine, OnSwing, OnSpine);
        const float Along = FVector::Dist(From, OnSwing);
        // Low animals are struck at a downward swing's end too: the body's height counts toward reach.
        if (FVector::Dist(OnSwing, OnSpine) < Animal->Definition->Size.Y * .5f + 45.f && Along < BestAlong)
        {
            Best = Animal;
            BestAlong = Along;
        }
    }
    return Best;
}

bool AEWAnimal::TakeStrike(AEWCharacter* Striker, float Damage)
{
    if (!HasAuthority() || bDead || !Definition || Damage <= 0.f) return false;
    Rest.Wake();
    Health = FMath::Max(0.f, Health - Damage);
    MulticastFlinch();
    Call();
    if (Health <= 0.f) { Die(); if (Striker && Striker->GetProgressionComponent()) Striker->GetProgressionComponent()->Award(EEWExperienceSource::Hunt); }
    else if (Definition->bAggressive) Quarry = Striker;
    else
    {
        FleeFrom = Striker;
        FleeSeconds = 6.f;
        RestSeconds = 0.f;
        Action = EEWAnimalAction::Flee;
    }
    return true;
}

void AEWAnimal::MulticastFlinch_Implementation()
{
    FlinchSeconds = .35f;
}

void AEWAnimal::Call()
{
    const double Now = GetWorld()->GetTimeSeconds();
    if (!HasAuthority() || !Definition || Definition->Calls.IsEmpty() || Now - LastCallTime < 3.0) return;
    LastCallTime = Now;
    MulticastCall();
}

void AEWAnimal::MulticastCall_Implementation()
{
    if (!Definition || Definition->Calls.IsEmpty()) return;
    USoundBase* Sound = Definition->Calls[FMath::RandRange(0, Definition->Calls.Num() - 1)].LoadSynchronous();
    UEWSoundLibrary::PlayAssetAt(this, Sound, GetActorLocation() + FVector(0, 0, Definition->Size.Y * .5f), 1.f, FMath::FRandRange(.95f, 1.05f));
}

void AEWAnimal::Die()
{
    bDead = true;
    Health = 0.f;
    Action = EEWAnimalAction::Wander;
    LieShown = GrazeShown = 0.f;
    YieldLeft = FMath::RandRange(Definition->YieldMin, FMath::Max(Definition->YieldMin, Definition->YieldMax));
    Quarry = nullptr;
    DeadSeconds = 0.f;
    Dismount();
    OnRep_State();
    ForceNetUpdate();
}

void AEWAnimal::Respawn()
{
    bDead = bHarvested = false;
    Health = Definition->MaxHealth;
    YieldLeft = 0;
    FleeSeconds = 0.f;
    RoamPoint = Home;
    Action = EEWAnimalAction::Wander;
    SetActorLocationAndRotation(Home, FRotator(0, FMath::FRandRange(-180.f, 180.f), 0));
    OnRep_State();
    ForceNetUpdate();
}

bool AEWAnimal::CanInteract_Implementation(AEWCharacter* Character) const
{
    if (CanRide(Character)) return true;
    return IsValid(Character) && bDead && !bHarvested && Definition && Definition->Yield
        && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) < HarvestReach + Definition->Size.X * .5f;
}

FText AEWAnimal::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (!Definition) return FText::GetEmpty();
    if (!bDead) return FText::Format(NSLOCTEXT("Elitewake", "RideAnimal", "Ride the {0}"), Definition->DisplayName);
    return FText::Format(NSLOCTEXT("Elitewake", "HarvestAnimal", "Harvest the {0}"), Definition->DisplayName);
}

bool AEWAnimal::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character)) return false;
    if (CanRide(Character))
    {
        Rider = Character;
        Quarry = nullptr;
        RideDirection = FVector2D::ZeroVector;
        Character->SetMount(this);
        ForceNetUpdate();
        return true;
    }
    if (!Character->GetInventoryComponent()) return false;
    // Nothing is lost: whatever does not fit stays on the body for later.
    const int32 Taken = Character->GetInventoryComponent()->AddItem(Definition->Yield, YieldLeft);
    if (Taken <= 0) return false;
    YieldLeft -= Taken;
    if (YieldLeft > 0) return true;
    bHarvested = true;
    OnRep_State();
    ForceNetUpdate();
    return true;
}
