#pragma once

#include "CoreMinimal.h"

/**
 * Where north is (CLAUDE.md 4; owner, November 1): the world's +Y. East is -X, a quarter turn clockwise from north seen
 * from above, the way Unreal's yaw turns, so the compass, the map and the sun agree with the world layout
 * (Scripts/Setup/world_layout.py: Winter north, Swamp south, Desert east, Jungle west).
 */
namespace EWNorth
{
    /** The world yaw that faces north. */
    constexpr float NorthYaw = 90.f;

    /** A compass bearing, 0-360 clockwise from north, of a world yaw. */
    inline float BearingOfYaw(float Yaw) { return FMath::Fmod(FMath::Fmod(Yaw - NorthYaw, 360.f) + 360.f, 360.f); }

    /** The world yaw that faces a compass bearing. */
    inline float YawOfBearing(float Bearing) { return float(FRotator::NormalizeAxis(double(Bearing + NorthYaw))); }

    /** The bearing along a world offset. */
    inline float BearingOf(const FVector& Offset) { return BearingOfYaw(FMath::RadiansToDegrees(FMath::Atan2(Offset.Y, Offset.X))); }

    /** How far east and how far north a world location lies (from the origin, or as an offset). */
    inline FVector2D EastNorth(const FVector& Location) { return FVector2D(-Location.X, Location.Y); }
}
