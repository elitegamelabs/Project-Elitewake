#include "EWMineable.h"
#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Net/UnrealNetwork.h"

AEWMineable::AEWMineable()
{
    // It never moves, so every machine can shake its own copy when struck.
    SetReplicateMovement(false);
}

void AEWMineable::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWMineable, Resource);
    DOREPLIFETIME(AEWMineable, Remaining);
    DOREPLIFETIME(AEWMineable, PerStrike);
}

bool AEWMineable::CanAccessSource(AEWCharacter* Survivor) const
{
    return !bMining && Super::CanInteract_Implementation(Survivor)
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0
        && Survivor->GetInventoryComponent() && IsValid(Resource)
        && Resource->Category == EEWItemCategory::Resource && !Resource->ItemId.IsNone()
        && Remaining > 0 && PerStrike > 0;
}

bool AEWMineable::CanMine(AEWCharacter* Survivor) const
{
    if (!CanAccessSource(Survivor) || !Survivor->GetEquipmentComponent()) return false;
    const auto* Tool = Survivor->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand);
    return IsValid(Tool) && Tool->Category == EEWItemCategory::Tool && Tool->GatheringTool == EEWGatheringTool::Pickaxe;
}

int32 AEWMineable::TryMine(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !IsValid(Survivor) || !Survivor->HasAuthority() || !CanMine(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return 0;
    TGuardValue<bool> Guard(bMining, true);
    const int32 Added = Survivor->GetInventoryComponent()->AddItem(Resource, FMath::Min(Remaining, PerStrike));
    Remaining -= Added;
    if (Remaining == 0) Destroy();
    else if (Added > 0) ForceNetUpdate();
    return Added;
}
