#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWWaterSource.generated.h"

class UBoxComponent;

UENUM(BlueprintType)
enum class EEWWaterQuality : uint8 { Fresh, Salt };

/** Place a query surface on a pond/source. Visual water remains designer-owned. */
UCLASS(Blueprintable)
class EW_API AEWWaterSource : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWWaterSource();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Water")
    TObjectPtr<UBoxComponent> InteractionSurface;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Water")
    EEWWaterQuality WaterQuality = EEWWaterQuality::Fresh;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Water")
    bool bAvailable = true;

    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const override;
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override;
    /** True if the survivor holds an empty waterskin, which this water fills. */
    static bool HoldsEmptyWaterskin(const AEWCharacter* Survivor);
private:
    bool bDrinking = false;
};
