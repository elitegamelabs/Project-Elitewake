#include "EWShip.h"
#include "EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWPlayerController.h"
#include "EWInteractionComponent.h"
#include "EWWindSubsystem.h"
#include "EW.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"

namespace
{
    UStaticMesh* StandInCube() { return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")); }

    /** Stand-in proportions (cube scale, 1 = 1 m) for fittings without authored meshes. */
    FVector StandInScale(const UEWItemDefinition* Item)
    {
        switch (Item->FittingMountType)
        {
        case EEWShipMountType::Helm: return FVector(.3, .3, .8);
        case EEWShipMountType::Cannon: return FVector(1.2, .35, .35);
        case EEWShipMountType::Utility: return FVector(1, 1, .2);
        case EEWShipMountType::Sail:
            return Item->FittingSailSize == EEWSailSize::Large ? FVector(.05, 4, 6)
                : Item->FittingSailSize == EEWSailSize::Medium ? FVector(.05, 3, 4.5) : FVector(.05, 2, 3);
        default: return FVector(.3);
        }
    }

    FText MountTypeName(const FEWShipMount& Mount)
    {
        switch (Mount.Type)
        {
        case EEWShipMountType::Helm: return NSLOCTEXT("Elitewake", "MountHelm", "helm");
        case EEWShipMountType::Cannon: return NSLOCTEXT("Elitewake", "MountCannon", "cannon");
        case EEWShipMountType::Utility: return NSLOCTEXT("Elitewake", "MountUtility", "utility attachment");
        case EEWShipMountType::Sail:
            return Mount.SailSize == EEWSailSize::Large ? NSLOCTEXT("Elitewake", "MountSailLarge", "large sail")
                : Mount.SailSize == EEWSailSize::Medium ? NSLOCTEXT("Elitewake", "MountSailMedium", "medium sail")
                : NSLOCTEXT("Elitewake", "MountSailSmall", "small sail");
        default: return FText::GetEmpty();
        }
    }
}

AEWShip::AEWShip()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicateMovement(true);
    SetNetUpdateFrequency(30.f);
    HullCollision = CreateDefaultSubobject<UBoxComponent>(TEXT("HullCollision"));
    SetRootComponent(HullCollision);
    HullCollision->SetMobility(EComponentMobility::Movable);
    HullCollision->SetCollisionProfileName(TEXT("BlockAll"));
    HullCollision->SetBoxExtent(FVector(400, 150, 90));
    HullVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HullVisual"));
    HullVisual->SetupAttachment(HullCollision);
    HullVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AEWShip::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWShip, Definition);
    DOREPLIFETIME(AEWShip, Fittings);
    DOREPLIFETIME(AEWShip, Helmsman);
    DOREPLIFETIME(AEWShip, SailState);
    DOREPLIFETIME(AEWShip, Speed);
    DOREPLIFETIME(AEWShip, Rudder);
}

void AEWShip::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyDefinition();
    RefreshFittingVisuals();
}

void AEWShip::BeginPlay()
{
    Super::BeginPlay();
    if (Definition)
    {
        const FString Problem = Definition->Validate();
        if (!Problem.IsEmpty()) UE_LOG(LogEW, Error, TEXT("Ship definition %s is invalid: %s"), *GetNameSafe(Definition), *Problem);
    }
    ApplyDefinition();
    RefreshFittingVisuals();
}

void AEWShip::OnRep_Definition() { ApplyDefinition(); RefreshFittingVisuals(); }
void AEWShip::OnRep_Fittings() { RefreshFittingVisuals(); }

void AEWShip::ApplyDefinition()
{
    for (auto& Pair : MountTargets) if (Pair.Value) Pair.Value->DestroyComponent();
    MountTargets.Reset();
    if (!Definition) return;

    HullCollision->SetBoxExtent(Definition->HullExtent);
    if (UStaticMesh* Mesh = Definition->HullMesh.LoadSynchronous())
    {
        HullVisual->SetStaticMesh(Mesh);
        HullVisual->SetRelativeTransform(Definition->HullMeshTransform);
    }
    else
    {
        HullVisual->SetStaticMesh(StandInCube());
        HullVisual->SetRelativeTransform(FTransform(FRotator::ZeroRotator, FVector::ZeroVector, Definition->HullExtent / 50.f));
    }

    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        if (Mount.MountId.IsNone() || MountTargets.Contains(Mount.MountId)) continue;
        auto* Target = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(),
            *FString::Printf(TEXT("Mount_%s"), *Mount.MountId.ToString())), RF_Transient);
        Target->SetupAttachment(HullCollision);
        Target->SetRelativeTransform(Mount.Transform);
        Target->SetBoxExtent(FVector(30, 30, 40));
        Target->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Target->SetCollisionResponseToAllChannels(ECR_Ignore);
        Target->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
        Target->SetGenerateOverlapEvents(false);
        Target->RegisterComponent();
        MountTargets.Add(Mount.MountId, Target);
    }
}

void AEWShip::RefreshFittingVisuals()
{
    for (auto It = FittingVisuals.CreateIterator(); It; ++It)
        if (!GetFitting(It.Key()))
        {
            if (It.Value()) It.Value()->DestroyComponent();
            It.RemoveCurrent();
        }
    if (!Definition) return;
    for (const FEWInstalledFitting& Fitting : Fittings)
    {
        const FEWShipMount* Mount = Definition->FindMount(Fitting.MountId);
        if (!Mount || !Fitting.Item) continue;
        TObjectPtr<UStaticMeshComponent>& Visual = FittingVisuals.FindOrAdd(Fitting.MountId);
        if (!Visual)
        {
            Visual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                *FString::Printf(TEXT("Fitting_%s"), *Fitting.MountId.ToString())), RF_Transient);
            Visual->SetupAttachment(HullCollision);
            Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Visual->RegisterComponent();
        }
        FTransform Local = Fitting.Item->FittingMeshTransform;
        UStaticMesh* Mesh = Fitting.Item->FittingMesh.LoadSynchronous();
        if (!Mesh)
        {
            // Stand-in box resting on the mount point until real fitting art exists.
            Mesh = StandInCube();
            const FVector Scale = StandInScale(Fitting.Item);
            Local = FTransform(FRotator::ZeroRotator, FVector(0, 0, Scale.Z * 50.f), Scale);
        }
        Visual->SetStaticMesh(Mesh);
        Visual->SetRelativeTransform(Local * Mount->Transform);
    }
}

UEWItemDefinition* AEWShip::GetFitting(FName MountId) const
{
    const FEWInstalledFitting* Found = Fittings.FindByPredicate([MountId](const FEWInstalledFitting& F) { return F.MountId == MountId; });
    return Found ? Found->Item : nullptr;
}

bool AEWShip::HasFittingOfType(EEWShipMountType Type) const
{
    return Fittings.ContainsByPredicate([Type](const FEWInstalledFitting& F) { return F.Item && F.Item->FittingMountType == Type; });
}

FTransform AEWShip::GetMountWorldTransform(FName MountId) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    return Mount ? Mount->Transform * GetActorTransform() : FTransform::Identity;
}

FName AEWShip::FindAimedMount(const AEWCharacter* Character) const
{
    if (!IsValid(Character) || !Character->GetWorld() || !Character->GetController()
        || Character->GetController()->GetPawn() != Character) return NAME_None;
    FVector Eye; FRotator Rotation;
    Character->GetActorEyesViewPoint(Eye, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipMount), false, Character);
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + Rotation.Vector() * FEWInteractionTargeting::Range, ECC_Visibility, Query)
        || Hit.GetActor() != this) return NAME_None;
    for (const auto& Pair : MountTargets) if (Pair.Value == Hit.GetComponent()) return Pair.Key;
    return NAME_None;
}

bool AEWShip::CanModifyFittings(const AEWCharacter* Character) const
{
    return Definition && IsValid(Character) && !Character->IsActorBeingDestroyed() && !IsActorBeingDestroyed()
        && Character->GetWorld() == GetWorld() && Character->GetController() && Character->GetController()->GetPawn() == Character
        && Character->GetInventoryComponent() && Character->GetSurvivalComponent()
        && Character->GetSurvivalComponent()->GetHealth() > 0;
}

UEWItemDefinition* AEWShip::FindCarriedFitting(const AEWCharacter* Character, const FEWShipMount& Mount) const
{
    for (const FEWInventoryEntry& Entry : Character->GetInventoryComponent()->GetInventoryEntries())
        if (Entry.Quantity > 0 && UEWShipDefinition::Accepts(Mount, Entry.ItemDefinition)) return Entry.ItemDefinition;
    return nullptr;
}

EEWFittingResult AEWShip::InstallFitting(AEWCharacter* Character, FName MountId)
{
    if (!HasAuthority() || bChangingFittings) return EEWFittingResult::Busy;
    if (!CanModifyFittings(Character)) return EEWFittingResult::NotAllowed;
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    if (!Mount) return EEWFittingResult::NoMount;
    if (GetFitting(MountId)) return EEWFittingResult::Occupied;
    UEWItemDefinition* Item = FindCarriedFitting(Character, *Mount);
    if (!Item) return EEWFittingResult::NoFitting;
    TGuardValue<bool> Guard(bChangingFittings, true);
    // The unit leaves the inventory before it appears on the ship, so a failed removal installs nothing.
    if (Character->GetInventoryComponent()->RemoveItem(Item, 1) != 1) return EEWFittingResult::NoFitting;
    Fittings.Add({MountId, Item});
    RefreshFittingVisuals();
    ForceNetUpdate();
    return EEWFittingResult::Installed;
}

EEWFittingResult AEWShip::RemoveFitting(AEWCharacter* Character, FName MountId)
{
    if (!HasAuthority() || bChangingFittings) return EEWFittingResult::Busy;
    if (!CanModifyFittings(Character)) return EEWFittingResult::NotAllowed;
    const int32 Index = Fittings.IndexOfByPredicate([MountId](const FEWInstalledFitting& F) { return F.MountId == MountId; });
    if (Index == INDEX_NONE) return EEWFittingResult::NoMount;
    if (Helmsman && Fittings[Index].Item && Fittings[Index].Item->FittingMountType == EEWShipMountType::Helm)
        return EEWFittingResult::Occupied;
    TGuardValue<bool> Guard(bChangingFittings, true);
    // The fitting stays on the ship unless the inventory accepts it.
    if (Character->GetInventoryComponent()->AddItem(Fittings[Index].Item, 1) != 1) return EEWFittingResult::InventoryFull;
    Fittings.RemoveAt(Index);
    RefreshFittingVisuals();
    ForceNetUpdate();
    return EEWFittingResult::Removed;
}

bool AEWShip::CanInteract_Implementation(AEWCharacter* Character) const
{
    if (bChangingFittings || !CanModifyFittings(Character)) return false;
    if (Helmsman == Character) return true;  // Leave the helm.
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    if (!Mount) return false;
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        // An installed helm is taken, not removed; removing it is a Builder's Plan action.
        return Installed->FittingMountType != EEWShipMountType::Helm
            || (!Helmsman && !Character->GetHelmShip() && !Character->bIsCrouched && !Character->IsProne());
    return FindCarriedFitting(Character, *Mount) != nullptr;
}

FText AEWShip::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (Character && Helmsman == Character)
        return NSLOCTEXT("Elitewake", "LeaveHelm", "Leave the helm  (W/S sails, A/D rudder)");
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return FText::GetEmpty();
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        return Installed->FittingMountType == EEWShipMountType::Helm
            ? (Helmsman ? FText::GetEmpty() : NSLOCTEXT("Elitewake", "TakeHelm", "Take the helm"))
            : FText::Format(NSLOCTEXT("Elitewake", "RemoveFitting", "Remove {0}"), Installed->DisplayName);
    if (const UEWItemDefinition* Carried = IsValid(Character) && Character->GetInventoryComponent() ? FindCarriedFitting(Character, *Mount) : nullptr)
        return FText::Format(NSLOCTEXT("Elitewake", "InstallFitting", "Install {0}"), Carried->DisplayName);
    return FText::Format(NSLOCTEXT("Elitewake", "EmptyMount", "Empty {0} mount"), MountTypeName(*Mount));
}

bool AEWShip::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !Character || !Character->HasAuthority() || !CanInteract_Implementation(Character)
        || FEWInteractionTargeting::FindTarget(Character) != this) return false;
    if (Helmsman == Character) return LeaveHelm(Character);
    const FName MountId = FindAimedMount(Character);
    const UEWItemDefinition* Installed = GetFitting(MountId);
    if (Installed && Installed->FittingMountType == EEWShipMountType::Helm) return TakeHelm(Character);
    const EEWFittingResult Result = Installed ? RemoveFitting(Character, MountId) : InstallFitting(Character, MountId);
    return Result == EEWFittingResult::Installed || Result == EEWFittingResult::Removed;
}

// ---- Helm and sailing ----

namespace
{
    float SailWeight(EEWSailSize Size)
    {
        return Size == EEWSailSize::Large ? 3.f : Size == EEWSailSize::Medium ? 2.f : Size == EEWSailSize::Small ? 1.f : 0.f;
    }
}

const FEWShipMount* AEWShip::FindHelmMount() const
{
    return Definition ? Definition->Mounts.FindByPredicate([](const FEWShipMount& M) { return M.Type == EEWShipMountType::Helm; }) : nullptr;
}

FVector AEWShip::GetHelmSeatLocal(float CapsuleHalfHeight) const
{
    const FEWShipMount* Helm = FindHelmMount();
    const FVector Wheel = Helm ? Helm->Transform.GetLocation() : FVector::ZeroVector;
    const float DeckTop = Definition ? Definition->HullExtent.Z : 0.f;
    // Stand just aft of the wheel, on the deck.
    return FVector(Wheel.X - 60.f, Wheel.Y, DeckTop + CapsuleHalfHeight + 2.f);
}

bool AEWShip::IsValidHelmsman(const AEWCharacter* Character) const
{
    return Character && Helmsman == Character && Character->GetHelmShip() == this && CanModifyFittings(Character);
}

bool AEWShip::TakeHelm(AEWCharacter* Character)
{
    if (!HasAuthority() || bChangingFittings || Helmsman || !CanModifyFittings(Character)
        || Character->GetHelmShip() || Character->bIsCrouched || Character->IsProne() || !HasFittingOfType(EEWShipMountType::Helm))
        return false;
    Helmsman = Character;
    Rudder = 0.f;
    Character->SetHelmShip(this);
    ForceNetUpdate();
    return true;
}

bool AEWShip::LeaveHelm(AEWCharacter* Character, bool bForce)
{
    if (!HasAuthority() || !Character || Helmsman != Character) return false;
    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const float HalfHeight = Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 90.f;
    const FVector Exit = GetActorTransform().TransformPosition(GetHelmSeatLocal(HalfHeight) + FVector(0, 90.f, 0));
    if (!bForce && Capsule)
    {
        FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipHelmExit), false, Character);
        if (GetWorld()->OverlapBlockingTestByChannel(Exit, FQuat::Identity, ECC_Pawn, Capsule->GetCollisionShape(), Query))
            return false;
    }
    Helmsman = nullptr;
    Rudder = 0.f;  // Sails stay as they were set; the ship keeps sailing until someone changes them.
    Character->SetHelmShip(nullptr);
    if (!Character->IsActorBeingDestroyed()) Character->SetActorLocation(Exit, false, nullptr, ETeleportType::TeleportPhysics);
    ForceNetUpdate();
    return true;
}

bool AEWShip::SetRudder(AEWCharacter* Character, float NewRudder)
{
    if (!HasAuthority() || !IsValidHelmsman(Character) || !FMath::IsFinite(NewRudder) || FMath::Abs(NewRudder) > 1.f) return false;
    const auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC || PC->GetInteractionComponent()->IsMenuBlocked()) return false;
    Rudder = NewRudder;
    return true;
}

bool AEWShip::StepSails(AEWCharacter* Character, int32 Direction)
{
    if (!HasAuthority() || !IsValidHelmsman(Character) || (Direction != 1 && Direction != -1)) return false;
    const auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC || PC->GetInteractionComponent()->IsMenuBlocked()) return false;
    SailState = static_cast<EEWSailState>(FMath::Clamp(static_cast<int32>(SailState) + Direction, 0, 2));
    return true;
}

float AEWShip::GetFittedSailFraction() const
{
    if (!Definition) return 0.f;
    float Capacity = 0.f, Fitted = 0.f;
    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        if (Mount.Type != EEWShipMountType::Sail) continue;
        Capacity += SailWeight(Mount.SailSize);
        if (GetFitting(Mount.MountId)) Fitted += SailWeight(Mount.SailSize);
    }
    return Capacity > 0.f ? Fitted / Capacity : 0.f;
}

float AEWShip::ComputeTargetSpeed() const
{
    if (!Definition || SailState == EEWSailState::Furled) return 0.f;
    const float SailSet = SailState == EEWSailState::Full ? 1.f : .5f;
    const UEWWindSubsystem* Wind = GetWorld() ? GetWorld()->GetSubsystem<UEWWindSubsystem>() : nullptr;
    const float Heading = Wind ? Wind->GetHeadingFactor(GetActorForwardVector()) : 1.f;
    return Definition->TopSpeed * SailSet * GetFittedSailFraction() * Heading;
}

void AEWShip::SimulateSailing(float DeltaSeconds)
{
    if (!HasAuthority() || !Definition || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    SimulationRemainder += FMath::Min(DeltaSeconds, MaxCatchUpSeconds);
    while (SimulationRemainder >= SimulationStep)
    {
        SimulationRemainder -= SimulationStep;
        StepSimulation(SimulationStep);
    }
}

void AEWShip::StepSimulation(float Step)
{
    const float Target = ComputeTargetSpeed();
    Speed = FMath::FInterpConstantTo(Speed, Target, Step, Target > Speed ? Acceleration : Deceleration);
    if (Speed <= 1.f && FMath::IsNearlyZero(Rudder)) { Speed = FMath::Max(Speed, 0.f); return; }
    const float Steerage = FMath::Clamp(Speed / FullSteerageSpeed, MinSteerage, 1.f);
    const FRotator Rotation = GetActorRotation() + FRotator(0, Rudder * Definition->TurnRate * Steerage * Step, 0);
    // People never stop a ship: survivors on deck ride with it and swimmers are pushed aside.
    // Hulls, land and other world geometry still block the sweep.
    HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    FHitResult Hit;
    SetActorLocationAndRotation(GetActorLocation() + Rotation.Vector() * Speed * Step, Rotation, true, &Hit);
    HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    if (Hit.bBlockingHit)
    {
        if (!bAgainstObstacle)
            UE_LOG(LogEW, Log, TEXT("Ship %s stopped by %s (%s) at %s"), *GetName(), *GetNameSafe(Hit.GetActor()),
                *GetNameSafe(Hit.GetComponent()), *GetActorLocation().ToCompactString());
        bAgainstObstacle = true;
        Speed = 0.f;
    }
    else bAgainstObstacle = false;
}

void AEWShip::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;
    if (Helmsman && !IsValidHelmsman(Helmsman))
    {
        if (IsValid(Helmsman)) LeaveHelm(Helmsman, true);
        else Helmsman = nullptr;
        Rudder = 0.f;
    }
    // An open menu centres the rudder; the sails keep their setting.
    if (Helmsman)
        if (const auto* PC = Cast<AEWPlayerController>(Helmsman->GetController()); !PC || PC->GetInteractionComponent()->IsMenuBlocked())
            Rudder = 0.f;
    SimulateSailing(DeltaSeconds);
}

void AEWShip::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && IsValid(Helmsman)) LeaveHelm(Helmsman, true);
    Super::EndPlay(Reason);
}
