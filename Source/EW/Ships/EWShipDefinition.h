#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWShipTypes.h"
#include "EWShipDefinition.generated.h"

class UEWItemDefinition;
class UStaticMesh;

/** Data for one ship class: its hull and the fixed mounts players fit out. */
UCLASS(BlueprintType)
class EW_API UEWShipDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship", meta=(AssetRegistrySearchable))
    FName ShipId;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship")
    FText DisplayName;

    /** Half size of the hull's collision box, in cm. The ship actor's origin is the box centre. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull", meta=(ClampMin="10"))
    FVector HullExtent = FVector(400, 150, 90);
    /** How far the hull bottom sits below the waterline, in cm. Placement sets the actor height from it. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull", meta=(ClampMin="0"))
    float HullDraft = 60.f;
    /** Optional. Without a mesh, a box matching the hull extent stands in. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    TSoftObjectPtr<UStaticMesh> HullMesh;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    FTransform HullMeshTransform;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Mounts")
    TArray<FEWShipMount> Mounts;
    /** Built-in boarding ladders on the hull sides, relative to the ship. Hold Interact there to climb aboard. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    TArray<FVector> BoardingPoints;
    /** Built-in anchor capstan on deck, relative to the ship. Hold Interact there to raise or drop the anchor. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    FVector AnchorPoint = FVector(350, -90, 130);
    /** Cargo hatch on deck, relative to the ship. Hold Interact there to open the ship's hold. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Cargo")
    FVector CargoHatchPoint = FVector(-150, 60, 130);
    /** Slots in the ship's hold (tuning; Weight/Storage upgrades will raise it). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Cargo", meta=(ClampMin="1"))
    int32 CargoSlots = 20;

    /** Sailing tuning. Top speed with every sail mount fitted and the sails full, running before the wind. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sailing", meta=(ClampMin="0", Units="cm/s"))
    float TopSpeed = 700.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sailing", meta=(ClampMin="0", Units="deg/s"))
    float TurnRate = 30.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Ship", meta=(ClampMin="1"))
    int32 CrewCapacity = 1;

    const FEWShipMount* FindMount(FName MountId) const;
    /** True when the item is a fitting this mount accepts. */
    static bool Accepts(const FEWShipMount& Mount, const UEWItemDefinition* Item);
    /** Empty when valid; otherwise describes the first authoring problem. */
    FString Validate() const;

    virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};
