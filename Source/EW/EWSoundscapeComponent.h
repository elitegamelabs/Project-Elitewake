#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/EWClimateRegion.h"
#include "EWSoundscapeComponent.generated.h"

class UAudioComponent;

/**
 * The background a player hears, on their own machine only: the sea's surf everywhere, the cold wind on the Winter
 * island, and seabirds now and then away from it. It follows the climate region where the player's survivor stands
 * (AEWClimateRegion), fading between them. Levels are tuning.
 */
UCLASS(ClassGroup=(Sound))
class EW_API UEWSoundscapeComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWSoundscapeComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** For the checks: the region heard now, the loops' current levels, and whether both loops are playing. */
    UFUNCTION(BlueprintPure, Category="Sound") EEWRegion GetHeardRegion() const { return HeardRegion; }
    UFUNCTION(BlueprintPure, Category="Sound") float GetSurfLevel() const { return SurfLevel; }
    UFUNCTION(BlueprintPure, Category="Sound") float GetWindLevel() const { return WindLevel; }
    UFUNCTION(BlueprintPure, Category="Sound") bool IsAmbiencePlaying() const;

private:
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Surf;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Wind;
    EEWRegion HeardRegion = EEWRegion::OpenSea;
    float SurfLevel = 0.f;
    float WindLevel = 0.f;
    float SampleSeconds = 0.f;
    float BirdSeconds = 0.f;
    bool bStarted = false;
    void Start();
};
