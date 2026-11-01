#include "EWPlacementPreviewComponent.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWEquipmentComponent.h"
#include "World/EWCampfire.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
    const TCHAR* const GhostMaterial = TEXT("/Game/Elitewake/UI/M_PlacementGhost_v1.M_PlacementGhost_v1");
    // How near a ship must be to look for its mounts (cm): the ships' marker range.
    constexpr float ShipRange = 2500.f;
}

const FLinearColor UEWPlacementPreviewComponent::Placeable(.12f, .45f, 1.f);
const FLinearColor UEWPlacementPreviewComponent::NotPlaceable(1.f, .1f, .08f);

UEWPlacementPreviewComponent::UEWPlacementPreviewComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .05f;
}

void UEWPlacementPreviewComponent::BeginPlay()
{
    Super::BeginPlay();
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, GhostMaterial, nullptr, LOAD_Quiet | LOAD_NoWarn);
    // Only the machine whose player this is sees it.
    if (!PC || !PC->IsLocalController() || GetNetMode() == NM_DedicatedServer || !Base)
    {
        SetComponentTickEnabled(false);
        return;
    }
    Glow = UMaterialInstanceDynamic::Create(Base, this);
    // Its own local actor: a player controller is never drawn, nor anything it owns.
    FActorSpawnParameters Params;
    Params.ObjectFlags = RF_Transient;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    GhostActor = GetWorld()->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform::Identity, Params);
    if (!GhostActor)
    {
        SetComponentTickEnabled(false);
        return;
    }
    GhostActor->SetReplicates(false);
    Ghost = GhostActor->GetStaticMeshComponent();
    Ghost->SetMobility(EComponentMobility::Movable);
    Ghost->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Ghost->SetCastShadow(false);
    Ghost->SetVisibility(false);
}

void UEWPlacementPreviewComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (GhostActor) GhostActor->Destroy();
    Super::EndPlay(Reason);
}

bool UEWPlacementPreviewComponent::IsShowing() const
{
    return Ghost && Ghost->IsVisible();
}

void UEWPlacementPreviewComponent::Hide()
{
    if (Ghost) Ghost->SetVisibility(false);
    ShownMount = NAME_None;
    ShownItem = nullptr;
    bPlaceable = false;
}

void UEWPlacementPreviewComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const AEWCharacter* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Survivor || !Ghost || Survivor->GetHelmShip() || Survivor->GetGunShip() || Survivor->IsOnLadder() || !Survivor->GetInventoryComponent())
    {
        Hide();
        return;
    }
    // A campfire in hand (Phase 1): its ring where it would be laid, blue if the ground there takes it, red if not.
    UEWItemDefinition* Held = Survivor->GetEquipmentComponent() ? Survivor->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    if (Held && Held->PlacedActor)
    {
        FTransform Spot; bool bHit = false;
        bPlaceable = AEWCampfire::FindPlacement(Survivor, Spot, bHit);
        UStaticMesh* Mesh = Held->PlacedActor->GetDefaultObject<AEWCampfire>()->Ring->GetStaticMesh();
        if (!bHit || !Mesh)
        {
            Hide();
            return;
        }
        if (Ghost->GetStaticMesh() != Mesh)
        {
            Ghost->SetStaticMesh(Mesh);
            for (int32 Slot = 0; Slot < Ghost->GetNumMaterials(); ++Slot) Ghost->SetMaterial(Slot, Glow);
        }
        Glow->SetVectorParameterValue(TEXT("Colour"), bPlaceable ? Placeable : NotPlaceable);
        Ghost->SetWorldTransform(Spot);
        Ghost->SetVisibility(true);
        ShownMount = NAME_None;
        ShownItem = Held;
        return;
    }
    // The mount being looked at, on any ship close by.
    AEWShip* Ship = nullptr;
    FName MountId = NAME_None;
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        if (FVector::Dist(It->GetActorLocation(), Survivor->GetActorLocation()) > ShipRange + It->GetSimpleCollisionRadius()) continue;
        const FName Aimed = It->FindAimedMount(Survivor);
        if (!Aimed.IsNone()) { Ship = *It; MountId = Aimed; break; }
    }
    const FEWShipMount* Mount = Ship && Ship->Definition ? Ship->Definition->FindMount(MountId) : nullptr;
    if (!Mount)
    {
        Hide();
        return;
    }
    // A carried fitting of the mount's kind: one that fits if there is one, else any (shown red).
    UEWItemDefinition* Item = nullptr;
    bool bFits = false;
    for (const FEWInventoryEntry& Entry : Survivor->GetInventoryComponent()->GetInventoryEntries())
    {
        if (Entry.Quantity <= 0 || !Entry.ItemDefinition || Entry.ItemDefinition->FittingMountType != Mount->Type) continue;
        const bool bThisFits = UEWShipDefinition::Accepts(*Mount, Entry.ItemDefinition);
        if (!Item || (bThisFits && !bFits)) { Item = Entry.ItemDefinition; bFits = bThisFits; }
    }
    if (!Item)
    {
        Hide();
        return;
    }
    bPlaceable = bFits && Ship->IsMountOpen(MountId) && !Ship->GetFitting(MountId);
    // As the fitting would sit there: the mount's own look for it if the ship has one, else the item's.
    const bool bMountLook = !Mount->FittedMesh.IsNull();
    UStaticMesh* Mesh = bMountLook ? Mount->FittedMesh.LoadSynchronous() : Item->FittingMesh.LoadSynchronous();
    const FTransform Local = bMountLook ? Mount->FittedMeshTransform : Item->FittingMeshTransform;
    if (!Mesh)
    {
        Hide();
        return;
    }
    if (Ghost->GetStaticMesh() != Mesh)
    {
        Ghost->SetStaticMesh(Mesh);
        for (int32 Slot = 0; Slot < Ghost->GetNumMaterials(); ++Slot) Ghost->SetMaterial(Slot, Glow);
    }
    Glow->SetVectorParameterValue(TEXT("Colour"), bPlaceable ? Placeable : NotPlaceable);
    Ghost->SetWorldTransform(Local * Mount->Transform * Ship->GetActorTransform());
    Ghost->SetVisibility(true);
    ShownMount = MountId;
    ShownItem = Item;
}
