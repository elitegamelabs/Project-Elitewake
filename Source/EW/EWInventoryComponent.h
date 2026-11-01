// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWInventoryComponent.generated.h"

class FLifetimeProperty;
class UEWItemDefinition;
class UEWCraftingRecipe;

UENUM(BlueprintType)
enum class EEWCraftResult : uint8 { Success, NotAuthority, Locked, InvalidRecipe, MissingIngredients, InventoryFull, Busy, NeedsFire };

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

    /** Trusted server code grants availability; callers cannot grant recipes through an RPC. */
    UFUNCTION(BlueprintCallable, Category="Inventory|Crafting")
    bool UnlockRecipe(UEWCraftingRecipe* Recipe);
    UFUNCTION(BlueprintPure, Category="Inventory|Crafting")
    TArray<UEWCraftingRecipe*> GetAvailableRecipes() const;
    /** How many of Quantity units of Item the pack could take now (free slots and part stacks). Any machine that sees the entries. */
    UFUNCTION(BlueprintPure, Category="Inventory")
    int32 GetRoomFor(UEWItemDefinition* Item, int32 Quantity) const;

    /** Crafts exactly one item atomically, using server-owned recipe availability. */
    UFUNCTION(BlueprintCallable, Category="Inventory|Crafting")
    EEWCraftResult CraftItem(UEWCraftingRecipe* Recipe);
    /** Read-only local estimate. Authority revalidates when executing the request. */
    UFUNCTION(BlueprintPure, Category="Inventory|Crafting")
    EEWCraftResult GetCraftReadiness(UEWCraftingRecipe* Recipe) const;

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

    /**
     * Authority only. Moves up to Quantity units of the stack at EntryIndex into another inventory, as one
     * transaction: only what the destination can hold leaves this inventory, so nothing is lost or copied.
     * Ageing food keeps its age and stays a separate batch. Returns the number of units moved.
     */
    int32 TransferEntryTo(UEWInventoryComponent* Destination, int32 EntryIndex, int32 Quantity);
    /** Authority only. Sets the slot count for containers such as a ship's hold; never below the slots in use. */
    void SetMaxSlots(int32 NewMaxSlots);

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
    /** Designer-authored baseline unlocks. Empty until production availability is approved. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Inventory|Crafting")
    TArray<TObjectPtr<UEWCraftingRecipe>> StartingRecipes;
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Inventory", meta=(ClampMin="1"))
	int32 MaxSlots = 24;

	UPROPERTY(ReplicatedUsing=OnRep_Entries, VisibleInstanceOnly, BlueprintReadOnly, Category="Inventory")
	TArray<FEWInventoryEntry> Entries;

	UFUNCTION()
	void OnRep_Entries();

private:
    friend class FEWCraftingTest;
    void InitializeStartingRecipes();
    EEWCraftResult StageCraft(UEWCraftingRecipe* Recipe, TArray<FEWInventoryEntry>& Proposed) const;
    UPROPERTY(ReplicatedUsing=OnRep_Entries)
    TArray<TObjectPtr<UEWCraftingRecipe>> AvailableRecipes;
    friend class UEWEditorVerificationLibrary;
    friend class FEWFoodTest;
    friend class FEWContainerTransferTest;
    friend class UEWEquipmentComponent;
    friend class UEWSurvivorSave;
    friend class AEWShip;
    friend class AEWDeathBag;
    friend class AEWWreckCrate;
    friend class AEWPlayerController;
    friend class FEWSurvivorSaveRoundTripTest;
    double LastFoodClockSeconds = 0.;
    void RefreshFoodAge();
    void AdvanceFoodAge(float RealSeconds);
    bool bEquipmentTransferInProgress = false;
    static int32 AddToEntries(TArray<FEWInventoryEntry>& Entries, int32 MaxSlots, UEWItemDefinition* Item, int32 Quantity);
    static int32 RemoveFromEntries(TArray<FEWInventoryEntry>& Entries, UEWItemDefinition* Item, int32 Quantity);
	void HandleInventoryChanged();
	void RefreshSurvivalWeight();
};
