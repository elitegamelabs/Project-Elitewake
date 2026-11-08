#pragma once

#include "CoreMinimal.h"
#include "World/EWClimateRegion.h"
#include "EWPlaces.generated.h"

/** What sort of named place a discovery is (FUTURE_IMPLEMENTATIONS Part 8, 63). Creatures are their own kind. */
UENUM(BlueprintType)
enum class EEWPlaceKind : uint8 { Island, Freeport, Reef, Cave, Creature };

/**
 * Every named place in the world a survivor can discover: the twenty islands, the five Freeports, the three open-ocean reefs
 * and each island's cave. The table is generated from the world's data by Scripts/Setup/write_discovery_places.py.
 */
namespace EWPlaces
{
struct FPlace
{
    const TCHAR* Id;
    const TCHAR* Name;
    EEWPlaceKind Kind;
    EEWRegion Region;
    FVector2D Centre;   // cm
    FVector2D Radii;    // cm, of an ellipse turned by Turn
    float Turn;         // radians
    float Z;            // cm: the place's height, when ZRange is not 0
    float ZRange;       // cm above or below Z that counts as being there; 0 for any height
    const TCHAR* Note;  // one line for the journal
};

EW_API TConstArrayView<FPlace> All();
EW_API const FPlace* Find(FName Id);
/** True when Location is at the place: inside its turned ellipse and, for a cave, near its height. */
EW_API bool IsAt(const FPlace& Place, const FVector& Location);
EW_API FText KindName(EEWPlaceKind Kind);
}
