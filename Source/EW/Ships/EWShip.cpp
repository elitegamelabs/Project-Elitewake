#include "EWShip.h"
#include "EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EW.h"
#include "Components/BoxComponent.h"
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
    bReplicates = true;
    SetReplicateMovement(true);
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
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    return Mount && (GetFitting(MountId) || FindCarriedFitting(Character, *Mount));
}

FText AEWShip::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return FText::GetEmpty();
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        return FText::Format(NSLOCTEXT("Elitewake", "RemoveFitting", "Remove {0}"), Installed->DisplayName);
    if (const UEWItemDefinition* Carried = IsValid(Character) && Character->GetInventoryComponent() ? FindCarriedFitting(Character, *Mount) : nullptr)
        return FText::Format(NSLOCTEXT("Elitewake", "InstallFitting", "Install {0}"), Carried->DisplayName);
    return FText::Format(NSLOCTEXT("Elitewake", "EmptyMount", "Empty {0} mount"), MountTypeName(*Mount));
}

bool AEWShip::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !Character || !Character->HasAuthority() || !CanInteract_Implementation(Character)
        || FEWInteractionTargeting::FindTarget(Character) != this) return false;
    const FName MountId = FindAimedMount(Character);
    const EEWFittingResult Result = GetFitting(MountId) ? RemoveFitting(Character, MountId) : InstallFitting(Character, MountId);
    return Result == EEWFittingResult::Installed || Result == EEWFittingResult::Removed;
}
