#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWSound.generated.h"

class USoundBase;

/** The game's own sounds, played from code. Each is a draft from Art/Audio, imported by Scripts/Setup/import_audio.py. */
UENUM(BlueprintType)
enum class EEWSound : uint8
{
    ChopWood, PickaxeStone, GlanceClink, GatherRustle, Pickup, StepSand, StepSnow, OceanSurf, WinterWind, Seabirds,
    CannonFire, HullHit, ShotSplash, Bail, ShipSinking, StepDeck, SwimStroke, HullCreak, Rigging, NightInsects, CaveDrips
};

/**
 * Plays the game's sounds where things happen. Every machine plays what it sees (nothing about sound is replicated);
 * a dedicated server plays none. Volumes and falloff live on the imported assets. Each world counts what it started,
 * by asset name, for the Play checks.
 */
UCLASS()
class EW_API UEWSoundLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** One of the sound's takes, at random (some footsteps and the alligator have two). */
    UFUNCTION(BlueprintPure, Category="Sound")
    static USoundBase* GetSound(EEWSound Sound);
    /** Plays Sound at Location, falling off with distance; Pitch varies it a little for repeated steps. */
    UFUNCTION(BlueprintCallable, Category="Sound", meta=(WorldContext="WorldContext"))
    static void PlaySoundAt(const UObject* WorldContext, EEWSound Sound, FVector Location, float Volume = 1.f, float Pitch = 1.f);
    /** Plays any sound asset at Location (an animal's call). */
    static void PlayAssetAt(const UObject* WorldContext, USoundBase* Asset, FVector Location, float Volume = 1.f, float Pitch = 1.f);
    /** Plays any sound asset everywhere at once, for this machine's player only. */
    static void PlayAsset2D(const UObject* WorldContext, USoundBase* Asset, float Volume = 1.f);

    /** For the checks: how many times this world started the named sound asset (e.g. "S_ChopWood_v1"). */
    UFUNCTION(BlueprintPure, Category="Sound", meta=(WorldContext="WorldContext"))
    static int32 GetPlayCount(const UObject* WorldContext, FName AssetName);
    /** For the checks: the sound asset this world started last, and how many it has started in all. */
    UFUNCTION(BlueprintPure, Category="Sound", meta=(WorldContext="WorldContext"))
    static FName GetLastPlayed(const UObject* WorldContext);
    UFUNCTION(BlueprintPure, Category="Sound", meta=(WorldContext="WorldContext"))
    static int32 GetTotalPlayCount(const UObject* WorldContext);

private:
    static bool CanPlay(const UObject* WorldContext, USoundBase* Asset, UWorld*& OutWorld);
    static void Count(UWorld* World, const USoundBase* Asset);
};
