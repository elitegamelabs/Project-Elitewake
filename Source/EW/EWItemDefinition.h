// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Ships/EWShipTypes.h"
#include "EWItemDefinition.generated.h"

class UTexture2D;
class UStaticMesh;

UENUM(BlueprintType)
enum class EEWFoodKind : uint8 { None, Berry, RawFish, CookedFish, RawMeat, CookedMeat, BerryDish, Remedy };

UENUM(BlueprintType)
enum class EEWGatheringTool : uint8 { None, Hatchet, Pickaxe };

/** Ordered pickaxe material capability; None keeps older authored tools usable on unrestricted nodes. */
UENUM(BlueprintType)
enum class EEWPickaxeTier : uint8 { None, Wooden, Stone, Metal, Tungsten };

UENUM(BlueprintType)
enum class EEWItemCategory : uint8
{
	Resource,
	Consumable,
	Tool,
	Weapon,
	Ammunition,
	Clothing,
	Quest,
	Miscellaneous
};

/** The three armor categories (owner, November 8): one helmet, one chest piece (gloves included) and one pair of pants
 *  (footwear included) each. */
UENUM(BlueprintType)
enum class EEWArmorKind : uint8 { None, Cloth, Fur, Metal };

UENUM(BlueprintType)
enum class EEWEquipmentSlot : uint8
{
	None,
	Head,
	Chest,
	Hands,
	Legs,
	Feet,
	MainHand,
	OffHand
};

/** Data-only description shared by every stack of a particular item type. */
UCLASS(BlueprintType)
class EW_API UEWItemDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
    /** Opt-in only. Existing food stays disabled until its freshness policy is authored. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food")
    bool bFoodConsumptionEnabled = false;
    /** Fraction of the full hunger bar restored by one unit (berries: 1/16). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food", meta=(ClampMin="0", ClampMax="1"))
    float HungerRestoreFraction = 0.f;
    /** Fraction of current maximum unlocked health, not remaining health (Azul: .05). Negative for food that harms (raw meat: -.03). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food", meta=(ClampMin="-1", ClampMax="1"))
    float HealthRestoreFraction = 0.f;
    /** Chance eating one unit brings on food sickness (owner, October 22: raw fish .15, raw meat .25). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food", meta=(ClampMin="0", ClampMax="1"))
    float SicknessChance = 0.f;
    /** Eating or using one unit ends food sickness early (medicinal herbs, a crafted remedy). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food")
    bool bCuresFoodSickness = false;
    /** Real elapsed seconds in the running session; berries use 1200. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food", meta=(ClampMin="0"))
    float FreshLifetimeSeconds = 0.f;
    /** Inedible resource replacing an expired stack, with the same stack size and weight. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food")
    TObjectPtr<UEWItemDefinition> SpoiledItemDefinition;
    /** Food identity only; consumption and per-stack freshness are separate systems. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food")
    EEWFoodKind FoodKind = EEWFoodKind::None;
    /** Capability used only when this owned unit is equipped in MainHand. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Gathering")
    EEWGatheringTool GatheringTool = EEWGatheringTool::None;
	/** Material tier for pickaxes. Restricted mineable nodes compare this against their authored minimum. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Gathering")
	EEWPickaxeTier PickaxeTier = EEWPickaxeTier::None;
	/** Stable identifier used by saving, recipes, vendors, and networking. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Item", meta=(AssetRegistrySearchable))
	FName ItemId;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Item")
	FText DisplayName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Item", meta=(MultiLine="true"))
	FText Description;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Item")
	EEWItemCategory Category = EEWItemCategory::Miscellaneous;

	/** Maximum quantity stored in one inventory slot. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Inventory", meta=(ClampMin="1"))
	int32 MaxStackSize = 1;

	/** Weight of one unit in kilograms. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Inventory", meta=(ClampMin="0.0", Units="kg"))
	float UnitWeight = 0.0f;

	/** What a Port merchant pays for one unit, in Copper; 0 means they will not buy it (design reference: vendor prices are data-driven,
	 *  values TBD: every value here is a placeholder for tuning). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Economy", meta=(ClampMin="0"))
	int32 SellValueCopper = 0;

    /** Sailhand's Articles: used at a sail's lines aboard, it signs a hired Port sailhand on for that sail, who then follows
     *  the helm's orders (owner, October 18: crew dependency). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Economy")
    bool bSignsOnSailhand = false;

    /** Gunner Articles: used at an installed cannon aboard, they sign a hired Port gunner on to serve it. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Economy")
    bool bSignsOnGunner = false;

	/** Worn clothing's warmth: 0 for none; 1 keeps a survivor warm in the Winter region's working cold. It also
	 *  traps heat in humid regions (owner: overheating is relieved by removing clothing). Values are open. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Clothing", meta=(ClampMin="0.0"))
	float Insulation = 0.0f;

	/** A sextant (Part 8, 09): held in the hand, it reads the survivor's latitude on the HUD. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Navigation")
	bool bSextant = false;

	/** Armor (owner, November 8): Cloth, Fur or Metal. Only fur carries Insulation, so only fur keeps out the cold. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Clothing")
	EEWArmorKind ArmorKind = EEWArmorKind::None;
	/** This piece's share of physical damage stopped (blows, bites), 0-1. A set's pieces add up (helmet 20%, chest 45%,
	 *  pants 35% of the set's total); the sum is capped at AEWCharacter::MaxArmorReduction. Never thirst, hunger, heat or cold. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Clothing", meta=(ClampMin="0.0", ClampMax="1.0"))
	float ArmorReduction = 0.0f;
	/** This piece's addition to the health lost while overheating (0.1 = 10% more). The pieces add up: a full cloth set
	 *  1.10x, fur 1.30x, metal 1.50x. Applies only once the body is already overheating. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Clothing", meta=(ClampMin="0.0"))
	float OverheatPenalty = 0.0f;

	/** None means this item is not directly equippable. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Equipment")
	EEWEquipmentSlot EquipmentSlot = EEWEquipmentSlot::None;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation")
	TSoftObjectPtr<UTexture2D> Icon;

    /** What a survivor holding it in the main hand carries, gripped at its origin, and how it sits in the right hand. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation")
    TSoftObjectPtr<UStaticMesh> HeldMesh;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation")
    FTransform HeldMeshTransform;
    /** A held light, such as a torch's flame: brightness in candelas (0 for none) and where it sits on the held mesh. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation", meta=(ClampMin="0"))
    float HeldLightIntensity = 0.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation")
    FVector HeldLightOffset = FVector::ZeroVector;
    /** A held flame drawn at the light while the item burns (a torch's fire). An item with a held light must be
     *  lit before it gives light. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Held")
    TSoftObjectPtr<UStaticMesh> HeldFlameMesh;
    /** Waterskins: the same skin full of fresh water (set on the empty one) and emptied again (set on the full
     *  one). Filling or drinking swaps one for the other where the skin is held. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Water")
    TSoftObjectPtr<UEWItemDefinition> FilledVersion;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Water")
    TSoftObjectPtr<UEWItemDefinition> EmptiedVersion;
    /** Laid on the ground from the hand (Left Mouse / the right trigger where its ghost shows blue), becoming this actor and
     *  leaving the hand: the campfire (Phase 1). None for everything else. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Placement")
    TSubclassOf<class AEWCampfire> PlacedActor;

    /** How much hull patching one unit gives a voyage's provisions (Phase 1 slice 6, FEWVoyageProvisions): Wood 1, a Repair Kit 20;
     *  0 for everything else (tuning). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting", meta=(ClampMin="0"))
    int32 PatchValue = 0;
    /** None means this item is not a ship fitting. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    EEWShipMountType FittingMountType = EEWShipMountType::None;
    /** Sails only: the mount size this sail fits. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    EEWSailSize FittingSailSize = EEWSailSize::None;
    /** Sails only (owner, October 18): the whole-ship speed multiplier this sail gives at full deployment while it draws: small 1.30,
     *  medium 1.50, large 1.80; weighted small 1.25, medium 1.40, large 1.70. Sails do not stack: the best one counts. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting", meta=(ClampMin="0"))
    float SailSpeedMultiplier = 1.f;
    /** Sails only: a weighted sail (a weighted hem) steadies the ship in the wind (delegated, October 18: 10% more roll and pitch damping). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    bool bWeightedSail = false;
    /** Railing modules only: how many cannon places the module opens behind it (0 plain or dinghy, 2 two-cannon). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting", meta=(ClampMin="0"))
    int32 FittingCannonSlots = 0;
    /** Shown on the ship while installed, attached at the mount. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    TSoftObjectPtr<UStaticMesh> FittingMesh;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    FTransform FittingMeshTransform;
    /** Sails only: shown while the sails are furled (cloth rolled on its spars). Without it a furled sail hides.
     *  Half sail shows FittingMesh lowered toward its origin, so build sails standing up from their foot. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    TSoftObjectPtr<UStaticMesh> FittingFurledMesh;
    /** A helm's part that turns with the rudder (a wheel on its axle, a tiller and rudder on their post), built
     *  with its pivot at the origin; where that pivot sits in the fitting's frame; and how it is turned with the
     *  rudder hard to starboard. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    TSoftObjectPtr<UStaticMesh> FittingTurningMesh;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    FTransform FittingTurningPivot;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    FRotator FittingTurnAtFull = FRotator::ZeroRotator;
    /** Cannons: the round shot they load, and how far the muzzle lies along the barrel from its pivot (the
     *  barrel is the fitting's turning part, aimed rather than turned with the rudder). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    TSoftObjectPtr<UEWItemDefinition> CannonAmmo;
    /** Cannons: the powder charge a load takes with each round shot (CLAUDE.md 7.4, November 7: a real powder item backs the
     *  powder step). None: no powder needed. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    TSoftObjectPtr<UEWItemDefinition> CannonPowder;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    float CannonMuzzleLength = 150.f;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
