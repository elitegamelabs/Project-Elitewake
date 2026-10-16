#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWShipSoundComponent.generated.h"

class UAudioComponent;
class AEWShip;

/**
 * A ship's own sounds, on every screen that has her (nothing extra is replicated: it reads her replicated state).
 * Her timbers creak always, more as she makes way; her rigging sounds while sail is set, more with speed; she groans
 * as she goes down; each stroke of the bucket that takes water out of her splashes over the side; and her anchor's
 * chain rattles out when it is let go, clanks as it catches the bottom a moment later, and grinds in at the capstan
 * when it is raised (owner, October 16). Levels are tuning.
 */
UCLASS(ClassGroup=(Sound))
class EW_API UEWShipSoundComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWShipSoundComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** For the checks: the creak and rigging loops' levels now, and whether both are playing. */
    UFUNCTION(BlueprintPure, Category="Sound") float GetCreakLevel() const { return CreakLevel; }
    UFUNCTION(BlueprintPure, Category="Sound") float GetRiggingLevel() const { return RiggingLevel; }
    UFUNCTION(BlueprintPure, Category="Sound") bool AreLoopsPlaying() const;

private:
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Creak;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Rigging;
    float CreakLevel = 0.f;
    float RiggingLevel = 0.f;
    float LastWater = 0.f;
    bool bWasSinking = false;
    bool bWasAnchored = true;
    FTimerHandle AnchorCatchTimer;
    void AnchorCaught();
    AEWShip* Ship() const;
};
