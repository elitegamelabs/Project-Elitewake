// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWItemDefinition.generated.h"

class UTexture2D;

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

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
