#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWMerchant.generated.h"

class UStaticMeshComponent;
class UPrimitiveComponent;
class AEWCharacter;
class UEWItemDefinition;

/** One line of a merchant's goods: what is sold, how many units one purchase gives, its price and how many purchases the stall holds. */
USTRUCT(BlueprintType)
struct FEWMerchantGoods
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant") TObjectPtr<UEWItemDefinition> Item;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant", meta=(ClampMin="1")) int32 Bundle = 1;
    /** Tuning, in Copper for one bundle. Never below what the bundle sells back for (see GetGoodsPrice). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant", meta=(ClampMin="0")) int32 PriceCopper = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant", meta=(ClampMin="1")) int32 MaxStock = 10;
};

/**
 * A Port's general merchant (design reference, Economy; prologue step 9). One press of Interact sells every item in the survivor's pack that
 * has a sell value (EWItemDefinition::SellValueCopper) and pays the total into their purse; equipped items and things with no value stay.
 * The server does the selling. Goods to buy stand in crates on a counter in front of the merchant (Goods, set per merchant by
 * Scripts/Setup/add_port_merchants.py): aim at a crate and press Interact to buy one bundle. Each stall holds a few bundles of each line and
 * restocks one bundle of each every RestockSeconds. Stock and prices are placeholders for tuning (vendor data is TBD). The figure, counter and
 * crates are placeholders (engine shapes) until the owner's art.
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
    UFUNCTION(BlueprintPure, Category="Merchant") int32 GetGoodsCount() const { return Goods.Num(); }
    UFUNCTION(BlueprintPure, Category="Merchant") int32 GetStockLeft(int32 Index) const { return StockLeft.IsValidIndex(Index) ? StockLeft[Index] : 0; }
    /** Copper for one bundle: the set price, raised if needed so a bundle never costs less than it sells back for. */
    UFUNCTION(BlueprintPure, Category="Merchant") int64 GetGoodsPrice(int32 Index) const;
    /** The goods line whose crate this survivor aims at, or -1. */
    UFUNCTION(BlueprintPure, Category="Merchant") int32 FindAimedGoods(const AEWCharacter* Character) const;
    /** Where a goods crate stands, in the world (for checks and placement). */
    UFUNCTION(BlueprintPure, Category="Merchant") FVector GetGoodsLocation(int32 Index) const;
    /** Authority: one bundle of a goods line into the survivor's pack for its price. Refused when sold out, too dear, too far or the pack is full. */
    UFUNCTION(BlueprintCallable, Category="Merchant") bool Buy(AEWCharacter* Character, int32 Index);
    /** Authority: one bundle back on every line that is short (the restock timer calls this). */
    UFUNCTION(BlueprintCallable, Category="Merchant") void Restock();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant") TArray<FEWMerchantGoods> Goods;
    /** Tuning: seconds between restocks. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Merchant", meta=(ClampMin="1")) float RestockSeconds = 300.f;
    static constexpr float TradeReach = 450.f;

protected:
    virtual void BeginPlay() override;

private:
    void BuildStall();
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Crates;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Counter;
    UPROPERTY(Replicated) TArray<int32> StockLeft;
    FTimerHandle RestockTimer;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Head;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Hat;
    UPROPERTY(Replicated) int32 SalesMade = 0;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
