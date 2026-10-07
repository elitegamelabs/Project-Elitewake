#pragma once

#include "CoreMinimal.h"
#include "EWPickup.h"
#include "EWHandGatherable.generated.h"

UENUM(BlueprintType)
enum class EEWHandGatheringKind : uint8 { PlantFiber, LooseSticks };

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
};
