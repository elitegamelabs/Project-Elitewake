#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWClimateRegion.generated.h"

/** The world's five regions (owner, October 14), and the open sea between them. */
UENUM(BlueprintType)
enum class EEWRegion : uint8 { OpenSea, Desert, Winter, Jungle, Plains, Swamp };

/** The climate felt at a place: its region, the air's temperature and humidity, and the water's temperature. */
USTRUCT(BlueprintType)
struct FEWClimate
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Climate") EEWRegion Region = EEWRegion::OpenSea;
    UPROPERTY(BlueprintReadOnly, Category="Climate") float AirTemperature = 22.f;
    /** Relative humidity, 0 to 100. */
    UPROPERTY(BlueprintReadOnly, Category="Climate") float Humidity = 60.f;
    UPROPERTY(BlueprintReadOnly, Category="Climate") float WaterTemperature = 20.f;
};

/**
 * One region's islands: an oval over the map (centre at the actor, half-sizes Radii) whose climate holds inside it.
 * Past its shore the climate eases into the open sea's over OffshoreReach (the desert's humidity reaches 100 m
 * offshore, owner, October 14; other regions end at their shores unless the owner decides otherwise). Placed in the
 * map, so it exists on every machine; nothing about it is replicated.
 */
UCLASS()
class EW_API AEWClimateRegion : public AActor
{
    GENERATED_BODY()
public:
    AEWClimateRegion();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Climate") EEWRegion Region = EEWRegion::Plains;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Climate") FVector2D Radii = FVector2D(5000, 5000);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Climate") float OffshoreReach = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Climate") FEWClimate Climate;

    /** The climate at a place: the region it lies in, blended toward the open sea past a region's shore. */
    UFUNCTION(BlueprintPure, Category="Climate", meta=(WorldContext="WorldContext"))
    static FEWClimate SampleClimate(const UObject* WorldContext, FVector Location);
    /** The open sea's climate, away from every region. */
    static FEWClimate OpenSea();
    /** Each region's working climate (tuning; see the design reference). */
    UFUNCTION(BlueprintPure, Category="Climate")
    static FEWClimate DefaultClimate(EEWRegion Kind);
    UFUNCTION(BlueprintPure, Category="Climate")
    static FText RegionName(EEWRegion Kind);

    /** 0 inside the oval, rising to 1 at OffshoreReach beyond it (or straight to 1 past the shore without reach). */
    float DistanceOutside(const FVector& Location) const;
};
