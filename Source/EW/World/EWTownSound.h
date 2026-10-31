#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWTownSound.generated.h"

class UAudioComponent;
class USoundBase;
class USoundAttenuation;

/** When a town sound is heard. */
UENUM(BlueprintType)
enum class EEWTownSoundHours : uint8 { Always, Day, Night };

/**
 * A sound of a place (owner, October 30: the Freeport should feel lived in): a loop (the tavern's voices, the yard at work, water at
 * the piles) or a sound struck now and then (the harbor bell), heard by day, by night or always, fading in and out as the hour
 * turns. Each machine plays its own; the day-night clock is the same everywhere, so nothing is replicated. Placed by
 * Scripts/Setup/build_freeport.py; levels and intervals are tuning.
 */
UCLASS()
class EW_API AEWTownSound : public AActor
{
    GENERATED_BODY()
public:
    AEWTownSound();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Sound") TObjectPtr<USoundBase> Sound;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Sound") TObjectPtr<USoundAttenuation> Attenuation;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Sound") EEWTownSoundHours Hours = EEWTownSoundHours::Always;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Sound", meta=(ClampMin="0")) float Volume = 1.f;
    /** Seconds between strikes, picked between the two; 0 and 0 plays the sound as a continuous loop. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Sound") FVector2D Interval = FVector2D::ZeroVector;

    /** For the checks: heard now (the hour allows it), and how many times it has been struck. */
    UFUNCTION(BlueprintPure, Category="Sound") bool IsActive() const { return bActive; }
    UFUNCTION(BlueprintPure, Category="Sound") bool IsPlaying() const;
    UFUNCTION(BlueprintPure, Category="Sound") int32 GetStrikes() const { return Strikes; }

private:
    bool WantsToSound() const;
    UPROPERTY(VisibleAnywhere, Category="Sound") TObjectPtr<UAudioComponent> Audio;
    bool bActive = false;
    float NextStrike = 0.f;
    int32 Strikes = 0;
};
