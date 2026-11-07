#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWSafeZone.generated.h"

class USphereComponent;

/**
 * A protected settlement (owner, October 30: the Freeport is a safe harbor). Inside its radius, as each flag says:
 *  - no survivor can hurt another (fists, and round shot striking survivors' ships);
 *  - nobody may build (Build Mode refuses the spot);
 *  - no hostile creature lives or hunts: one whose home is inside is not there, and one hunting drops the chase at the edge.
 * The bounds are a sphere (radius in cm) round the actor, flattened to a circle on the map; invisible to players. Placed by
 * Scripts/Setup/build_freeport.py. The radius is tuning.
 */
UCLASS()
class EW_API AEWSafeZone : public AActor
{
    GENERATED_BODY()
public:
    AEWSafeZone();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Safe Zone") FText ZoneName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Safe Zone", meta=(ClampMin="100")) float Radius = 12000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Safe Zone") bool bNoPvP = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Safe Zone") bool bNoBuilding = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Safe Zone") bool bNoHostiles = true;

    /** True when a point (in the world) lies within this zone (measured flat, so a ship's mast and a cellar count alike). */
    UFUNCTION(BlueprintPure, Category="Safe Zone") bool Contains(const FVector& Location) const;

    /** The zone a point lies in, or null. */
    UFUNCTION(BlueprintPure, Category="Safe Zone", meta=(WorldContext="WorldContext"))
    static AEWSafeZone* FindAt(const UObject* WorldContext, const FVector& Location);
    UFUNCTION(BlueprintPure, Category="Safe Zone", meta=(WorldContext="WorldContext"))
    static bool IsPvPBlocked(const UObject* WorldContext, const FVector& Location);
    UFUNCTION(BlueprintPure, Category="Safe Zone", meta=(WorldContext="WorldContext"))
    static bool IsBuildingBlocked(const UObject* WorldContext, const FVector& Location);
    UFUNCTION(BlueprintPure, Category="Safe Zone", meta=(WorldContext="WorldContext"))
    static bool KeepsHostilesOut(const UObject* WorldContext, const FVector& Location);

#if WITH_EDITOR
    virtual void OnConstruction(const FTransform& Transform) override;
#endif

private:
    /** Shows the bounds in the editor only. */
    UPROPERTY(VisibleAnywhere, Category="Safe Zone") TObjectPtr<USphereComponent> Bounds;
};
