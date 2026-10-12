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

	/** None means this item is not directly equippable. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Equipment")
	EEWEquipmentSlot EquipmentSlot = EEWEquipmentSlot::None;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Presentation")
	TSoftObjectPtr<UTexture2D> Icon;

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

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
