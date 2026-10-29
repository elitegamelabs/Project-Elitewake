#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWMerchant.generated.h"

class UStaticMeshComponent;
class AEWCharacter;

/**
 * A Port's general merchant (design reference, Economy; prologue step 9). One press of Interact sells every item in the survivor's pack that
 * has a sell value (EWItemDefinition::SellValueCopper) and pays the total into their purse; equipped items and things with no value stay.
 * The server does the selling. Stock to buy, restocking and real prices are open (vendor data is TBD), so there is no buying yet and every
 * price is a placeholder for tuning. The figure is a placeholder (engine shapes) until the owner's art.
 */
UCLASS()
class EW_API AEWMerchant : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWMerchant();

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Press; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** How many items and how much Copper selling the whole pack would bring. */
    static void Appraise(const AEWCharacter* Character, int32& OutItems, int64& OutCopper);

    UFUNCTION(BlueprintPure, Category="Merchant") int32 GetSalesMade() const { return SalesMade; }
    static constexpr float TradeReach = 450.f;

private:
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Head;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Hat;
    UPROPERTY(Replicated) int32 SalesMade = 0;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
