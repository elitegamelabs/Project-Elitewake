#pragma once
#include "CoreMinimal.h"
#include "EWMerchant.h"
#include "EWCrewMaster.generated.h"

class UEWItemDefinition;

/**
 * A Port's crew master (owner, October 18: "purchased Port NPCs"; crew dependency). One press of Interact hires a sailhand:
 * it takes the fee from the survivor's purse and gives Sailhand's Articles, which sign the hand on at a sail's lines aboard.
 * The fee is a placeholder for tuning; wages, crew limits per hull and cannon crews are not built. Placeholder figure.
 */
UCLASS()
class EW_API AEWCrewMaster : public AEWMerchant
{
    GENERATED_BODY()
public:
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** The item handed over for the fee (set by Scripts/Setup/add_port_merchants.py). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew")
    TObjectPtr<UEWItemDefinition> Articles;
    /** Tuning: the fee for one sailhand, in Copper. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew")
    int64 HireCost = 100;
};
