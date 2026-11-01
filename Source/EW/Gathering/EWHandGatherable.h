#pragma once

#include "CoreMinimal.h"
#include "EWPickup.h"
#include "EWHandGatherable.generated.h"

UENUM(BlueprintType)
/** LooseStones (October 31): stones lying loose on the ground, picked up by hand (Phase 1: the first stone tool needs no pickaxe). */
enum class EEWHandGatheringKind : uint8 { PlantFiber, LooseSticks, Berries, LooseStones };

/** Finite hand-gathered resource pool. Uses pickup's serialized partial transfer.
 * Quantity is the remaining authored yield; no automatic regrowth or tool/Attack behavior.
 */
UCLASS(Blueprintable)
class EW_API AEWHandGatherable : public AEWPickup
{
    GENERATED_BODY()
public:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Gathering")
    EEWHandGatheringKind GatheringKind = EEWHandGatheringKind::PlantFiber;

    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const override;
    virtual int32 TryPickup(AEWCharacter* Survivor) override;
    virtual bool UsesBushReach() const override { return GatheringKind == EEWHandGatheringKind::Berries; }
};
