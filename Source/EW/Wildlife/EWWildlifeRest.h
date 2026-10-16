#pragma once

#include "CoreMinimal.h"

class AActor;

/**
 * Wildlife rests while no survivor is within RestRange (DECIDED, delegated, October 15 night; tuning): nobody can
 * see it (a client is not even sent animals that far off), and its ground and water traces against the bigger
 * islands cost the frame for every animal and fish in the world. It looks for a survivor about once a second.
 */
struct EW_API FEWWildlifeRest
{
    static constexpr float RestRange = 20000.f;   // cm
    static constexpr float LookSeconds = 1.f;
    float Look = 0.f;
    bool bAwake = true;

    /** Advances the look timer; true while the creature should live its life this frame. */
    bool IsAwake(const AActor* Creature, float DeltaSeconds);
    /** Something happened to it (a blow): awake now, and for the next look's while. */
    void Wake() { bAwake = true; Look = LookSeconds; }
};
