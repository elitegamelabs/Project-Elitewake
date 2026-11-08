#pragma once

#include "CoreMinimal.h"
#include "EWColourVision.generated.h"

/** Colour vision (FUTURE_IMPLEMENTATIONS Part 8, 61; November 8): which palette the interface's colour cues use. */
UENUM(BlueprintType)
enum class EEWColourVision : uint8
{
    Standard,
    /** Red-green colour blindness (deuteranopia, protanopia): good is blue, warning is orange. */
    RedGreen,
    /** Blue-yellow colour blindness (tritanopia): good is bluish green, warning is vermilion. */
    BlueYellow,
};

/**
 * The interface's colour cues, in the palette the player chose (Options). Each cue also carries a shape or a word where it
 * matters (a ✓ on a ship mount a carried fitting fits; the warnings' words), so no meaning rests on colour alone. The
 * alternative palettes take Okabe and Ito's colour-blind-safe set.
 */
namespace EWCue
{
EW_API EEWColourVision GetMode();
EW_API void SetMode(EEWColourVision Mode);
EW_API FText ModeName(EEWColourVision Mode);
/** Right, ready, fits: a carried fitting fits a mount; sails trimmed well. */
EW_API FLinearColor Good();
/** Needs attention: an empty mount; sails trimmed badly. */
EW_API FLinearColor Warning();
/** The body cooling, and warming. */
EW_API FLinearColor Cold();
EW_API FLinearColor Hot();
/** The ✓ put before a label whose meaning is "this fits / this is right". */
inline const TCHAR* GoodMark() { return TEXT("✓ "); }
}
