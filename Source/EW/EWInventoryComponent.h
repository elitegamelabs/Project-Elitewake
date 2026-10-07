// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWInventoryComponent.generated.h"

class FLifetimeProperty;
class UEWItemDefinition;

UENUM(BlueprintType)
enum class EEWFoodUseResult : uint8
{
    Success, NotAuthority, InvalidFood, NotOwned, UnavailableSurvivor, Busy, NoBenefit
};

USTRUCT(BlueprintType)
struct FEWInventoryEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Inventory")
	TObjectPtr<UEWItemDefinition> ItemDefinition = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Inventory", meta=(ClampMin="1"))
	int32 Quantity = 1;

    /** Oldest unit age in this stack, measured in real session seconds. */
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Inventory|Food")
    float FoodAgeSeconds = 0.f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWOnInventoryChanged);

/** Server-authoritative, slot-based inventory foundation. */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWInventoryComponent : public UActorComponent
{
	GENERATED_BODY()

public:
    /** Oldest owned batch's remaining freshness; -1 when no timed berry is owned. */
    UFUNCTION(BlueprintPure, Category="Inventory|Food")
    float GetFoodFreshness(const UEWItemDefinition* ItemDefinition) const;
	UEWInventoryComponent();

	virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Raised after authoritative or replicated inventory contents change. */
	UPROPERTY(BlueprintAssignable, Category="Inventory")
	FEWOnInventoryChanged OnInventoryChanged;

	/** Adds as much as fits and returns the quantity actually added. Authority only. */
	UFUNCTION(BlueprintCallable, Category="Inventory")
	int32 AddItem(UEWItemDefinition* ItemDefinition, int32 Quantity);

	/** Removes up to the requested quantity and returns the quantity removed. Authority only. */
	UFUNCTION(BlueprintCallable, Category="Inventory")
	int32 RemoveItem(UEWItemDefinition* ItemDefinition, int32 Quantity);

    /** Consume one owned, explicitly enabled berry on authority. No client grant or RPC. */
    UFUNCTION(BlueprintCallable, Category="Inventory|Food")
    EEWFoodUseResult ConsumeFood(UEWItemDefinition* ItemDefinition);

	UFUNCTION(BlueprintPure, Category="Inventory")
	int32 GetItemCount(const UEWItemDefinition* ItemDefinition) const;

	UFUNCTION(BlueprintPure, Category="Inventory")
	bool HasItem(const UEWItemDefinition* ItemDefinition, int32 Quantity = 1) const;

	UFUNCTION(BlueprintPure, Category="Inventory")
	TArray<FEWInventoryEntry> GetInventoryEntries() const { return Entries; }

	UFUNCTION(BlueprintPure, Category="Inventory")
	int32 GetUsedSlotCount() const { return Entries.Num(); }

	UFUNCTION(BlueprintPure, Category="Inventory")
	int32 GetMaxSlotCount() const { return MaxSlots; }

	UFUNCTION(BlueprintPure, Category="Inventory")
	float GetTotalWeight() const;

protected:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Inventory", meta=(ClampMin="1"))
	int32 MaxSlots = 24;

	UPROPERTY(ReplicatedUsing=OnRep_Entries, VisibleInstanceOnly, BlueprintReadOnly, Category="Inventory")
	TArray<FEWInventoryEntry> Entries;

	UFUNCTION()
	void OnRep_Entries();

private:
    friend class UEWEditorVerificationLibrary;
    friend class FEWFoodTest;
    friend class UEWEquipmentComponent;
    double LastFoodClockSeconds = 0.;
    void RefreshFoodAge();
    void AdvanceFoodAge(float RealSeconds);
    bool bEquipmentTransferInProgress = false;
    static int32 AddToEntries(TArray<FEWInventoryEntry>& Entries, int32 MaxSlots, UEWItemDefinition* Item, int32 Quantity);
    static int32 RemoveFromEntries(TArray<FEWInventoryEntry>& Entries, UEWItemDefinition* Item, int32 Quantity);
	void HandleInventoryChanged();
	void RefreshSurvivalWeight();
};
