#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWWalletComponent.generated.h"

/**
 * A survivor's money (design reference, Currency: 500 Copper = 1 Silver, 30 Silver = 1 Gold, converted automatically; it weighs
 * nothing and is kept on death). One whole number of Copper, replicated to its owner only; Gold and Silver are only how it is read.
 * Only the server changes it. Nothing earns Copper yet except the placeholder starting purse (vendors, wages and loot are open work).
 */
UCLASS(ClassGroup=(Elitewake), meta=(BlueprintSpawnableComponent))
class EW_API UEWWalletComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWWalletComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    static constexpr int64 CopperPerSilver = 500;
    static constexpr int64 SilverPerGold = 30;
    /** Placeholder (tuning): the design gives 250 Copper when the inn introduction completes; until that exists a new survivor starts with it. */
    static constexpr int64 StartingCopper = 250;

    UFUNCTION(BlueprintPure, Category="Wallet") int64 GetCopper() const { return Copper; }
    /** Server only. Sets the purse outright (restoring a save). */
    UFUNCTION(BlueprintCallable, Category="Wallet") void SetCopper(int64 Amount);
    /** Server only. Adds Amount (positive). */
    UFUNCTION(BlueprintCallable, Category="Wallet") void AddCopper(int64 Amount);
    /** Server only: takes Amount if the purse holds it; false and no change otherwise. */
    UFUNCTION(BlueprintCallable, Category="Wallet") bool TrySpend(int64 Amount);
    UFUNCTION(BlueprintPure, Category="Wallet") bool CanAfford(int64 Amount) const { return Copper >= Amount; }
    /** "2 Gold 14 Silver 30 Copper", leaving out a zero part; "0 Copper" when empty. */
    UFUNCTION(BlueprintPure, Category="Wallet") static FString Format(int64 Amount);
    /** The short form, "2g 14s 30c". */
    UFUNCTION(BlueprintPure, Category="Wallet") static FString FormatShort(int64 Amount);
    virtual void BeginPlay() override;
private:
    UPROPERTY(Replicated) int64 Copper = 0;
};
