#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWBowWaveComponent.generated.h"

class AEWShip;
class UInstancedStaticMeshComponent;

/**
 * Water pushed aside by a ship's hull (owner, October 16: Design/Ships/SHIP_DISPLACEMENT_WAVES_2026-10-16.md), drawn on
 * every machine from the ship's speed and how fast she is turning (nothing extra is replicated). Making way, her bow
 * parts the water in two waves spreading outward and aft from the stem, and foam washes along both sides to meet the
 * wake trail (UEWWakeTrailComponent) astern. Turning, the wash is heavier on the outside of the turn and lighter
 * inside. Stopped, nothing. Sizes scale with her hull; strengths with her speed. All amounts are tuning.
 * Ships cannot go astern yet, so there is no wash for backing; it belongs here when they can.
 */
UCLASS(ClassGroup=(Ship))
class EW_API UEWBowWaveComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWBowWaveComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** For the checks: the bow waves' strength (0-1), and the side wash on her port and starboard sides (0-1). */
    UFUNCTION(BlueprintPure, Category="Ship|Wake") float GetBowStrength() const { return Bow; }
    UFUNCTION(BlueprintPure, Category="Ship|Wake") float GetPortWash() const { return Port; }
    UFUNCTION(BlueprintPure, Category="Ship|Wake") float GetStarboardWash() const { return Starboard; }
    /** Degrees per second she is turning (positive to starboard), as this machine sees it. */
    UFUNCTION(BlueprintPure, Category="Ship|Wake") float GetTurnRate() const { return TurnRate; }

private:
    UPROPERTY(Transient) TObjectPtr<UInstancedStaticMeshComponent> Foam;
    float Bow = 0.f, Port = 0.f, Starboard = 0.f, TurnRate = 0.f;
    float LastYaw = 0.f;
    bool bHasYaw = false;
    AEWShip* Ship() const;
};
