#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/EWClimateRegion.h"
#include "EWSoundscapeComponent.generated.h"

class UAudioComponent;

/**
 * The background a player hears, on their own machine only: the sea's surf everywhere, the cold wind on the Winter
 * island, seabirds now and then away from it by day, insects at night away from it, and dripping water under a
 * cave's roof, where the outside sounds fall away. It follows the climate region where the player's survivor stands
 * (AEWClimateRegion) and the hour (UEWDayNightSubsystem), fading between them. The surf is full at the water's edge
 * and fades away inland, silent from SurfReach on (owner, October 16: gone 20 m inland), coming back on the way down
 * to the shore. Levels are tuning.
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
    UFUNCTION(BlueprintPure, Category="Sound") float GetInsectLevel() const { return InsectLevel; }
    UFUNCTION(BlueprintPure, Category="Sound") float GetCaveLevel() const { return CaveLevel; }
    /** The region's own loop now playing (forest wind, the jungle by day, the swamp's frogs) and its level. */
    UFUNCTION(BlueprintPure, Category="Sound") FName GetRegionLoop() const { return RegionLoopName; }
    UFUNCTION(BlueprintPure, Category="Sound") float GetRegionLoopLevel() const { return RegionLevel; }
    /** Whether the survivor stands under a cave's roof (looked for twice a second). */
    UFUNCTION(BlueprintPure, Category="Sound") bool IsInCave() const { return bInCave; }
    /** How far the survivor is from the sea (cm; 0 in it or out at sea, SurfReach or more when it is out of reach). */
    UFUNCTION(BlueprintPure, Category="Sound") float GetShoreDistance() const { return ShoreDistance; }
    static constexpr float SurfReach = 2000.f;

private:
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Surf;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Wind;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Insects;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Cave;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Forest;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Jungle;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Swamp;
    FName RegionLoopName;
    float RegionLevel = 0.f;
    float ForestLevel = 0.f, JungleLevel = 0.f, SwampLevel = 0.f;
    EEWRegion HeardRegion = EEWRegion::OpenSea;
    float SurfLevel = 0.f;
    float WindLevel = 0.f;
    float InsectLevel = 0.f;
    float CaveLevel = 0.f;
    bool bInCave = false;
    bool bNight = false;
    bool UnderCaveRoof(const FVector& At) const;
    float ShoreDistance = 0.f;
    float DistanceToSea(const FVector& At) const;
    float SampleSeconds = 0.f;
    float BirdSeconds = 0.f;
    bool bStarted = false;
    void Start();
};
