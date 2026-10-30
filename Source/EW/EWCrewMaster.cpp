#include "EWCrewMaster.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWWalletComponent.h"

FText AEWCrewMaster::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    const FText Fee = FText::FromString(UEWWalletComponent::Format(HireCost));
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    if (!Purse || !Purse->CanAfford(HireCost))
        return FText::Format(NSLOCTEXT("Elitewake", "CrewMasterPoor", "Crew master: a sailhand costs {0}"), Fee);
    return FText::Format(NSLOCTEXT("Elitewake", "CrewMasterHire", "Hire a sailhand ({0})"), Fee);
}

bool AEWCrewMaster::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !Articles || !CanInteract_Implementation(Character)
        || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return false;
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Pack || !Purse || !Purse->CanAfford(HireCost)) return false;
    // The articles go into the pack first, so a full pack costs nothing.
    if (Pack->AddItem(Articles, 1) != 1) return false;
    if (!Purse->TrySpend(HireCost))
    {
        Pack->RemoveItem(Articles, 1);
        return false;
    }
    return true;
}
