#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWBuildZones.generated.h"

/**
 * Where Build Mode may place a piece (owner, October 26-27: build on every island outside Ports and obstruction zones; zones
 * only carve out parts of an island; beaches near docks are not buildable). Design:
 * Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md. The zone list is Content/Elitewake/Data/BuildZones.json,
 * written by Scripts/Setup/export_buildzones.py from the world layout, so the editor scripts and the game agree. This is only
 * the rule; the pieces, ghost and placing come in later milestones. Sizes and limits are tuning, not owner-approved values.
 *
 * Each check returns an empty string when a piece may be built there, otherwise one line saying why not (for the red ghost).
 */
UCLASS()
class EW_API UEWBuildZones : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** The point's ground: island ground above the waterline and outside every zone. Traces for the ground itself. */
    UFUNCTION(BlueprintCallable, Category="Build", meta=(WorldContext="WorldContext"))
    static FString CheckPoint(const UObject* WorldContext, float X, float Y);

    /** A rectangular footprint on the ground (half sizes in cm, yaw in degrees): its middle, corners and edge middles must
     *  be buildable, the ground under it level enough, and nothing solid in the way. */
    UFUNCTION(BlueprintCallable, Category="Build", meta=(WorldContext="WorldContext"))
    static FString CheckFootprint(const UObject* WorldContext, float X, float Y, float HalfX, float HalfY, float YawDegrees);

    /** The lowest and highest ground under a footprint (pieces already built are ignored, so a neighbour's slab is not ground).
     *  False if any of its nine sample points has no ground. */
    UFUNCTION(BlueprintCallable, Category="Build", meta=(WorldContext="WorldContext"))
    static bool GetFootprintGround(const UObject* WorldContext, float X, float Y, float HalfX, float HalfY, float YawDegrees, float& LowZ, float& HighZ);

    /** How many zones were loaded (0 means the data file is missing). */
    UFUNCTION(BlueprintPure, Category="Build")
    static int32 GetZoneCount();

    /** The zone rule alone for a point at a known ground height (no trace); used by the checks and tests. */
    static FString CheckZones(float X, float Y, float GroundZ);
};
