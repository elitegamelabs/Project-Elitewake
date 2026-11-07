#pragma once
#include "CoreMinimal.h"
#include "EWMerchant.h"
#include "EWFreeportServices.generated.h"

class AEWShip;
class UEWItemDefinition;
class UEWShipDefinition;

/** A hull the shipwright sells: its class, price (tuning) and the fittings it is launched with (mount and item, pairwise). */
USTRUCT(BlueprintType)
struct FEWShipForSale
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") TObjectPtr<UEWShipDefinition> Definition;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright", meta=(ClampMin="0")) int32 PriceCopper = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") TArray<FName> FittedMounts;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") TArray<TObjectPtr<UEWItemDefinition>> FittedItems;
};

/**
 * The Freeport's shipwright (owner, October 30: purchase, repair and prepare ships). In the dialogue window: buy a hull, launched at
 * the yard's slipway with its fittings, anchored and ready (refused while another ship blocks the slip); or repair the damaged ship
 * nearest the survivor in the harbor (full hull, holes patched, water out) for Copper by the hull health missing. He also sells
 * fittings like a merchant (Goods: the six sail assemblies and cannons at the Freeport), but buys nothing. Ships have no owner yet, so
 * "your ship" is the one nearest you. Prices and the repair rate are placeholders for tuning.
 */
UCLASS()
class EW_API AEWShipwright : public AEWMerchant
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") TArray<FEWShipForSale> ShipsForSale;
    /** The ship class to launch (the placed ships' class; set by Scripts/Setup/build_freeport.py). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") TSubclassOf<AEWShip> ShipClass;
    /** Where a new hull is launched: the slipway's foot in the water, bow out (world). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright") FTransform LaunchPoint;
    /** Tuning: Copper per point of hull health restored; how far from the shipwright (cm) a ship can be repaired. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright", meta=(ClampMin="0")) float RepairCopperPerPoint = .5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Shipwright", meta=(ClampMin="100")) float YardReach = 20000.f;

    /** Authority: launch the hull at Index for its price; the new ship, or null when refused. */
    UFUNCTION(BlueprintCallable, Category="Shipwright") AEWShip* BuyShip(AEWCharacter* Character, int32 Index);
    /** Authority: repair the damaged ship nearest the survivor within the yard's reach, for its price. */
    UFUNCTION(BlueprintCallable, Category="Shipwright") bool RepairShip(AEWCharacter* Character);
    /** The damaged ship nearest the survivor within reach, and what making her whole costs. */
    UFUNCTION(BlueprintPure, Category="Shipwright") AEWShip* FindShipToRepair(const AEWCharacter* Character, int64& OutCost) const;
    /** A ship the yard holds for sale of this class (AEWShip::bHeldByYard), or null. */
    UFUNCTION(BlueprintPure, Category="Shipwright") AEWShip* FindHeldShip(const UEWShipDefinition* Definition) const;
    /** No ship lies on the slipway's foot. */
    UFUNCTION(BlueprintPure, Category="Shipwright") bool IsSlipClear() const;
    static FText ShipName(const UEWShipDefinition* Definition);
    /** Talking to the shipwright is the town's shipyard step (Phase 1 slice 5). */
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

protected:
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const override;
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) override;
};

/** A job the tavern keeper pays for: bring so many of an item, paid in Copper (tuning). Repeatable. */
USTRUCT(BlueprintType)
struct FEWDeliveryContract
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern") TObjectPtr<UEWItemDefinition> Item;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern", meta=(ClampMin="1")) int32 Quantity = 1;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern", meta=(ClampMin="0")) int32 RewardCopper = 0;
    /** Who wants it and why, as the keeper tells it. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern") FText Story;
};

/**
 * The tavern keeper (owner, October 30: rumours, information and quests). In the dialogue window: hear a rumour (one after another
 * from the keeper's list), take a delivery job (bring the goods, be paid at once; the jobs stay on the board), or buy a drink that
 * slakes thirst. Rumours, jobs and prices are placeholders for the owner to rewrite.
 */
UCLASS()
class EW_API AEWTavernKeeper : public AEWTownsfolk
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern") TArray<FText> Rumors;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern") TArray<FEWDeliveryContract> Contracts;
    /** Tuning: a drink's price in Copper and how much thirst it slakes (hydration points). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern", meta=(ClampMin="0")) int32 DrinkCost = 5;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tavern", meta=(ClampMin="0")) float DrinkHydration = 30.f;

    /** Authority: hand in the goods for a job; true when paid. */
    UFUNCTION(BlueprintCallable, Category="Tavern") bool CompleteContract(AEWCharacter* Character, int32 Index);
    UFUNCTION(BlueprintCallable, Category="Tavern") bool BuyDrink(AEWCharacter* Character);
    /** The jobs as the notice board shows them. */
    FText DescribeContracts() const;

protected:
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const override;
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) override;

private:
    int32 NextRumor = 0;
};

/** A berth at the harbor's piers: where a ship lies (bow out to sea) and the longest hull it takes, cm. */
USTRUCT(BlueprintType)
struct FEWBerth
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor") FTransform Where;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor", meta=(ClampMin="100")) float MaxLength = 2000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor") FText Name;
};

/**
 * The harbor master (owner, October 30: manage docking and departure). In the dialogue window: bring your ship to a free berth (the
 * harbor's pilots tow the ship nearest you within the approaches to the first free berth that takes her length, and anchor her
 * there), clear her for departure (towed to the harbor mouth, bow to the sea, anyone aboard with her; you are rowed out to her deck
 * if you are ashore), or hear the harbor's rules. Ships have no owner yet, so "your ship" is the one nearest you.
 */
UCLASS()
class EW_API AEWHarborMaster : public AEWTownsfolk
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor") TArray<FEWBerth> Berths;
    /** The harbor mouth: where a departing ship is brought, bow out (world). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor") FTransform DepartureLane;
    /** Tuning: how far from the harbor master (cm) the pilots fetch a ship. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Harbor", meta=(ClampMin="100")) float ApproachRadius = 40000.f;

    /** Authority: tow the survivor's ship to a free berth; the berth's index, or -1. */
    UFUNCTION(BlueprintCallable, Category="Harbor") int32 RequestBerth(AEWCharacter* Character);
    /** Authority: tow the survivor's ship to the harbor mouth and put the survivor aboard. */
    UFUNCTION(BlueprintCallable, Category="Harbor") bool ClearForDeparture(AEWCharacter* Character);
    /** The ship nearest the survivor within the approaches (none sinking). */
    UFUNCTION(BlueprintPure, Category="Harbor") AEWShip* FindShipFor(const AEWCharacter* Character) const;
    /** The berth a ship lies in, or -1. */
    UFUNCTION(BlueprintPure, Category="Harbor") int32 FindBerthOf(const AEWShip* Ship) const;
    /** The first free berth that takes this ship, or -1. */
    UFUNCTION(BlueprintPure, Category="Harbor") int32 FindFreeBerth(const AEWShip* Ship) const;

protected:
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const override;
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) override;
};

/**
 * The town square's notice board: reading it opens the same window, with the tavern's jobs and where each service stands.
 * It has no figure; its post-and-board mesh is placed beside it by Scripts/Setup/build_freeport.py.
 */
UCLASS()
class EW_API AEWNoticeBoard : public AEWTownsfolk
{
    GENERATED_BODY()
public:
    AEWNoticeBoard();
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    /** The services and where they are, as posted. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Notice Board", meta=(MultiLine="true")) FText Directions;

protected:
    virtual FText GetDialogueGreeting(const AEWCharacter* Character) const override;
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const override;
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) override;
};
