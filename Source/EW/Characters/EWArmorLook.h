#pragma once

#include "CoreMinimal.h"

class USkeletalMeshComponent;
class UStaticMeshComponent;
class UEWItemDefinition;
struct FEWEquipmentEntry;

/**
 * Armor on the survivor (owner, November 8): PLACEHOLDER shapes until production skinned garments exist (CLAUDE.md Phase 5).
 * Each worn piece is drawn as simple shapes fixed to the body's bones, so it follows every animation, both survivor bodies and
 * the body sliders:
 *   helmet  the head, face and neck;
 *   chest   the torso, shoulders, both arms and both hands (gloves);
 *   pants   the hips, both legs and both feet (footwear).
 * A shape runs along a bone segment (an upper arm from shoulder to elbow), measured from the skeleton's reference pose, so
 * no angle is typed by hand. Colours by category: cloth beige, fur brown-grey with ears on the hood, metal dark steel over a
 * navy coat with a tricorn brim and leather boots.
 */
namespace EWArmorLook
{
/** Rebuilds the shapes for what is worn now, replacing InOutPieces (destroyed and made again). Nothing on a dedicated server. */
EW_API void Rebuild(USkeletalMeshComponent* Body, const TArray<FEWEquipmentEntry>& Worn, TArray<TObjectPtr<UStaticMeshComponent>>& InOutPieces);
/** How many shapes a worn item draws (checks). */
EW_API int32 ShapeCount(const UEWItemDefinition* Item);
}
