// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Ships/EWShipTypes.h"
#include "EWItemDefinition.generated.h"

class UTexture2D;
class UStaticMesh;

UENUM(BlueprintType)
enum class EEWFoodKind : uint8 { None, Berry };

UENUM(BlueprintType)
enum class EEWGatheringTool : uint8 { None, Hatchet, Pickaxe };

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
    /** Fraction of current maximum unlocked health, not remaining health (Azul: .05). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Food", meta=(ClampMin="0", ClampMax="1"))
    float HealthRestoreFraction = 0.f;
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

	/** Worn clothing's warmth: 0 for none; 1 keeps a survivor warm in the Winter region's working cold. It also
	 *  traps heat in humid regions (owner: overheating is relieved by removing clothing). Values are open. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Clothing", meta=(ClampMin="0.0"))
	float Insulation = 0.0f;

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

    /** None means this item is not a ship fitting. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    EEWShipMountType FittingMountType = EEWShipMountType::None;
    /** Sails only: the mount size this sail fits. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    EEWSailSize FittingSailSize = EEWSailSize::None;
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
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship Fitting")
    float CannonMuzzleLength = 150.f;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
