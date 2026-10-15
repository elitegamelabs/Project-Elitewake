#include "EWHarvestTree.h"
#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Net/UnrealNetwork.h"

AEWHarvestTree::AEWHarvestTree()
{
    // It never moves, so every machine can shake its own copy when struck.
    SetReplicateMovement(false);
}

void AEWHarvestTree::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWHarvestTree, Wood); DOREPLIFETIME(AEWHarvestTree, Thatch);
    DOREPLIFETIME(AEWHarvestTree, WoodRemaining); DOREPLIFETIME(AEWHarvestTree, ThatchRemaining);
    DOREPLIFETIME(AEWHarvestTree, WoodPerStrike); DOREPLIFETIME(AEWHarvestTree, ThatchPerStrike);
}

bool AEWHarvestTree::CanAccessSource(AEWCharacter* Survivor) const
{
    if (bHarvesting || !Super::CanInteract_Implementation(Survivor) || !Survivor->GetSurvivalComponent()
        || Survivor->GetSurvivalComponent()->GetHealth() <= 0 || !Survivor->GetInventoryComponent()
        || !IsValid(Wood) || !IsValid(Thatch) || Wood == Thatch
        || Wood->Category != EEWItemCategory::Resource || Thatch->Category != EEWItemCategory::Resource
        || Wood->ItemId.IsNone() || Thatch->ItemId.IsNone() || WoodPerStrike <= 0 || ThatchPerStrike <= 0
        || WoodRemaining < 0 || ThatchRemaining < 0 || (WoodRemaining == 0 && ThatchRemaining == 0)) return false;
    return true;
}

bool AEWHarvestTree::CanHarvest(AEWCharacter* Survivor) const
{
    if (!CanAccessSource(Survivor) || !Survivor->GetEquipmentComponent()) return false;
    const auto* Tool = Survivor->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand);
    return IsValid(Tool) && Tool->Category == EEWItemCategory::Tool && Tool->GatheringTool == EEWGatheringTool::Hatchet;
}

int32 AEWHarvestTree::TryHarvest(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !IsValid(Survivor) || !Survivor->HasAuthority() || !CanHarvest(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return 0;
    TGuardValue<bool> Guard(bHarvesting, true);
    auto* Inventory = Survivor->GetInventoryComponent();
    const int32 AddedWood = Inventory->AddItem(Wood, FMath::Min(WoodRemaining, WoodPerStrike));
    WoodRemaining -= AddedWood;
    const int32 AddedThatch = Inventory->AddItem(Thatch, FMath::Min(ThatchRemaining, ThatchPerStrike));
    ThatchRemaining -= AddedThatch;
    if (WoodRemaining == 0 && ThatchRemaining == 0) Destroy();
    else if (AddedWood > 0 || AddedThatch > 0) ForceNetUpdate();
    return AddedWood + AddedThatch;
}
