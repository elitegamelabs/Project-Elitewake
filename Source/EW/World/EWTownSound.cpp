#include "World/EWTownSound.h"
#include "World/EWDayNight.h"
#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"

AEWTownSound::AEWTownSound()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .5f;
    bReplicates = false;
    Audio = CreateDefaultSubobject<UAudioComponent>(TEXT("Audio"));
    SetRootComponent(Audio);
    Audio->bAutoActivate = false;
}

void AEWTownSound::BeginPlay()
{
    Super::BeginPlay();
    if (!GetWorld() || GetWorld()->GetNetMode() == NM_DedicatedServer) { SetActorTickEnabled(false); return; }
    Audio->SetSound(Sound);
    if (Attenuation) Audio->AttenuationSettings = Attenuation;
    Audio->SetVolumeMultiplier(Volume);
    NextStrike = FMath::FRandRange(Interval.X * .3f, FMath::Max(Interval.X * .3f, Interval.Y));
}

bool AEWTownSound::WantsToSound() const
{
    if (Hours == EEWTownSoundHours::Always) return true;
    const UEWDayNightSubsystem* Time = UEWDayNightSubsystem::GetForWorld(this);
    const bool bDay = !Time || Time->IsDay();
    return Hours == EEWTownSoundHours::Day ? bDay : !bDay;
}

bool AEWTownSound::IsPlaying() const
{
    return Audio && Audio->IsPlaying();
}

void AEWTownSound::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Sound) return;
    bActive = WantsToSound();
    if (Interval.Y <= 0.f)
    {
        // A loop: faded in when its hours come, out when they end.
        if (bActive && !Audio->IsPlaying()) Audio->FadeIn(3.f, Volume, FMath::FRandRange(0.f, 10.f));
        else if (!bActive && Audio->IsPlaying()) Audio->FadeOut(4.f, 0.f);
        return;
    }
    if (!bActive) return;
    if ((NextStrike -= DeltaSeconds) <= 0.f)
    {
        Audio->Play();
        ++Strikes;
        NextStrike = FMath::FRandRange(Interval.X, FMath::Max(Interval.X, Interval.Y));
    }
}
