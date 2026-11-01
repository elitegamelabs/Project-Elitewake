#include "EWHandGatherable.h"
#include "EWCharacter.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Net/UnrealNetwork.h"

void AEWHandGatherable::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWHandGatherable, GatheringKind);
}

bool AEWHandGatherable::CanInteract_Implementation(AEWCharacter* Survivor) const
{
    return Super::CanInteract_Implementation(Survivor)
        && (GatheringKind == EEWHandGatheringKind::Berries
            ? ItemDefinition->Category == EEWItemCategory::Consumable && ItemDefinition->FoodKind == EEWFoodKind::Berry
            : ItemDefinition->Category == EEWItemCategory::Resource)
        && !ItemDefinition->ItemId.IsNone()
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0;
}

FText AEWHandGatherable::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    if (!IsValid(ItemDefinition)) return FText::GetEmpty();
    const FText Full = NoRoomPrompt(Survivor);
    if (!Full.IsEmpty()) return Full;
    const FText Pattern = GatheringKind != EEWHandGatheringKind::LooseSticks && GatheringKind != EEWHandGatheringKind::LooseStones
        ? NSLOCTEXT("Elitewake", "GatherPlantResource", "Gather {0}")
        : NSLOCTEXT("Elitewake", "CollectLooseResource", "Collect {0}");
    return FText::Format(Pattern, ItemDefinition->DisplayName);
}

int32 AEWHandGatherable::TryPickup(AEWCharacter* Survivor)
{
    return CanInteract_Implementation(Survivor) ? Super::TryPickup(Survivor) : 0;
}
