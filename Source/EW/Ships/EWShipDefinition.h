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
    /** With a hull mesh: the walkable deck's height above the ship's origin, in cm. The mesh is what crew stand
     *  on, inside its bulwarks and hold; the extent box then only meets docks, land and other hulls. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    float DeckHeight = 90.f;
    /** Optional ropes and other thin rigging, drawn with the hull but without collision so they never snag
     *  walkers or the camera. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    TSoftObjectPtr<UStaticMesh> RiggingMesh;
    /** Lowest walkable floor inside the hull (the hold), above the ship's origin, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    float HoldFloorHeight = 0.f;

    /** Where crew stand on deck: the mesh's deck, or the stand-in box's top when there is no mesh. */
    UFUNCTION(BlueprintPure, Category="Hull")
    float GetDeckHeight() const { return HullMesh.IsNull() ? HullExtent.Z : DeckHeight; }

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Mounts")
    TArray<FEWShipMount> Mounts;
    /** Part of the hull rather than fitted by players, such as a raft's paddles: installed when the ship
     *  starts if the mount is empty, and never removed. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Mounts")
    TArray<FEWInstalledFitting> BuiltInFittings;

    UFUNCTION(BlueprintPure, Category="Mounts")
    bool IsBuiltIn(FName MountId) const;
    /** Built-in boarding ladders on the hull sides, relative to the ship. Hold Interact there to climb aboard. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    TArray<FVector> BoardingPoints;
    /** Built-in anchor capstan on deck, relative to the ship. Hold Interact there to raise or drop the anchor. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    FVector AnchorPoint = FVector(350, -90, 130);
    /** The capstan's head, which turns while the anchor is worked; it stands with its base at CapstanLocation,
     *  relative to the ship. None on a boat without a capstan. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    TSoftObjectPtr<UStaticMesh> CapstanMesh;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull")
    FVector CapstanLocation = FVector::ZeroVector;
    /** The hull's health when whole (tuning; Hull Health upgrades will raise it). Round shot takes it away. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Hull", meta=(ClampMin="1"))
    float HullHealth = 1000.f;
    /** Cargo hatch on deck, relative to the ship. Hold Interact there to open the ship's hold. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Cargo")
    FVector CargoHatchPoint = FVector(-150, 60, 130);
    /** Slots in the ship's hold (tuning; Weight/Storage upgrades will raise it). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Cargo", meta=(ClampMin="1"))
    int32 CargoSlots = 20;
    /** Load the ship carries at full speed-penalty but not yet overloaded: hold plus fittings, in kg (tuning;
     *  Weight/Storage upgrades will raise it). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Cargo", meta=(ClampMin="1", Units="kg"))
    float WeightCapacity = 1500.f;

    /** Sailing tuning. Top speed with every sail mount fitted and the sails full, running before the wind. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sailing", meta=(ClampMin="0", Units="cm/s"))
    float TopSpeed = 700.f;
    /** Moved by paddles rather than sails, like a raft: speed ignores the wind and fitted sails, and the helmsman's
     *  forward and back set the stroke (resting, easy, hard) instead of the sails. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sailing")
    bool bPaddled = false;
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
