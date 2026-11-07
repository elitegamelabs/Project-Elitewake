#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Subsystems/WorldSubsystem.h"
#include "EWDayNight.generated.h"

class ADirectionalLight;

/**
 * Day and night (owner: 90 real minutes of day, 90 of night). Day runs from 06:00 to 18:00 and night from 18:00 to
 * 06:00, so the clock turns at one game hour every 450 real seconds. The server owns the time: it replicates the hour
 * it set and the server time it set it at, and every machine works the hour out from there. DECIDED (delegated,
 * tuning): a new world starts at 08:00; the sun climbs to 65 degrees at noon in the south (Winter lies north), rising
 * in the east and setting in the west; the moon stands opposite it.
 */
struct EW_API FEWSkyClock
{
    static constexpr float DayStarts = 6.f;
    static constexpr float NightStarts = 18.f;
    static constexpr float SecondsPerHour = 90.f * 60.f / 12.f;
    static constexpr float StartHour = 8.f;
    static constexpr float HighestSun = 65.f;
    /** How much darker (in exposure stops) full night is than day (tuning). */
    static constexpr float NightExposure = 3.f;

    /** The hour (0 to 24) a given number of real seconds after the clock read Hour. */
    static float HourAfter(float Hour, double Seconds);
    static bool IsDay(float Hour) { return Hour >= DayStarts && Hour < NightStarts; }
    /** The sun's height above the horizon in degrees: 0 at 06:00 and 18:00, HighestSun at noon, below at night. */
    static float SunElevation(float Hour);
    /** The world yaw toward the sun (World/EWNorth.h): east (180, toward -X) at 06:00, south (-90) at noon, west (0) at 18:00. */
    static float SunAzimuth(float Hour);
    /** How a directional light pointing from a body at (Elevation, Azimuth) toward the ground is turned. */
    static FRotator LightRotation(float Elevation, float Azimuth) { return FRotator(-Elevation, Azimuth + 180.f, 0.f); }
};

/** The replicated clock: the hour the server set and the server time it set it at. Moves the map's sun on every machine. */
UCLASS(NotPlaceable)
class EW_API AEWSkyClock : public AActor
{
    GENERATED_BODY()
public:
    AEWSkyClock();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(Replicated) float AnchorHour = FEWSkyClock::StartHour;
    UPROPERTY(Replicated) double AnchorServerTime = 0.0;

    float GetHour() const;

private:
    void FindLights();
    void ApplyLight(float Hour);

    /** The map's sun: its directional light tagged EWSun (maps without one keep their own lighting). */
    UPROPERTY(Transient) TObjectPtr<ADirectionalLight> Sun;
    /** A moon made on each machine for the night, a dim cool light opposite the sun. */
    UPROPERTY(Transient) TObjectPtr<ADirectionalLight> Moon;
    /** Darkens the picture as night falls, so the eye's adjustment does not turn moonlight back into day. */
    UPROPERTY(Transient) TObjectPtr<class APostProcessVolume> NightGrade;
    float SunIntensity = 3.f;
};

UCLASS()
class EW_API UEWDayNightSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;

    UFUNCTION(BlueprintPure, Category="Time", meta=(WorldContext="WorldContext"))
    static UEWDayNightSubsystem* GetForWorld(const UObject* WorldContext);
    /** The hour of the day, 0 to 24 (the same on every machine). */
    UFUNCTION(BlueprintPure, Category="Time")
    float GetHour() const;
    UFUNCTION(BlueprintPure, Category="Time")
    bool IsDay() const { return FEWSkyClock::IsDay(GetHour()); }
    /** Server only: set the clock to an hour (for a saved world, or to test). Ignored on a client. */
    UFUNCTION(BlueprintCallable, Category="Time")
    void SetHour(float Hour);
    AEWSkyClock* GetClock() const { return Clock; }
    void SetClock(AEWSkyClock* InClock) { Clock = InClock; }

private:
    UPROPERTY(Transient) TObjectPtr<AEWSkyClock> Clock;
};
