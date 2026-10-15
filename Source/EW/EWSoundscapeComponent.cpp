#include "EWSoundscapeComponent.h"
#include "EWSound.h"
#include "Components/AudioComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

namespace
{
    // Loop levels in each place (tuning): the surf softer on the Winter island, where the wind takes over.
    constexpr float SurfAshore = .7f, SurfAtSea = .85f, SurfInWinter = .3f, WindInWinter = 1.f;
    // Seconds for a loop to fade to a new place's level, and between seabird cries away from the Winter island.
    constexpr float FadeSeconds = 2.5f, BirdsMin = 14.f, BirdsMax = 35.f;
}

UEWSoundscapeComponent::UEWSoundscapeComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .1f;
}

void UEWSoundscapeComponent::BeginPlay()
{
    Super::BeginPlay();
    // Only the machine whose player this is hears it.
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    SetComponentTickEnabled(PC && PC->IsLocalController() && GetNetMode() != NM_DedicatedServer);
    BirdSeconds = FMath::FRandRange(4.f, BirdsMin);
}

void UEWSoundscapeComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    for (UAudioComponent* Loop : {Surf.Get(), Wind.Get()})
        if (Loop) Loop->Stop();
    Super::EndPlay(Reason);
}

void UEWSoundscapeComponent::Start()
{
    bStarted = true;
    Surf = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::OceanSurf), 1.f, 1.f, 0.f, nullptr, true, false);
    Wind = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::WinterWind), 1.f, 1.f, 0.f, nullptr, true, false);
    for (UAudioComponent* Loop : {Surf.Get(), Wind.Get()})
        if (Loop)
        {
            Loop->SetVolumeMultiplier(0.f);
            Loop->Play(FMath::FRandRange(0.f, 10.f));   // start somewhere in the loop, so two players don't hear it in step
        }
}

bool UEWSoundscapeComponent::IsAmbiencePlaying() const
{
    return Surf && Wind && Surf->IsPlaying() && Wind->IsPlaying();
}

void UEWSoundscapeComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
    if (!Pawn) return;   // the title screen and the moments between survivors are quiet
    if (!bStarted) Start();
    SampleSeconds -= DeltaSeconds;
    if (SampleSeconds <= 0.f)
    {
        SampleSeconds = .5f;
        HeardRegion = AEWClimateRegion::SampleClimate(this, Pawn->GetActorLocation()).Region;
    }
    const bool bWinter = HeardRegion == EEWRegion::Winter;
    const float SurfTarget = bWinter ? SurfInWinter : HeardRegion == EEWRegion::OpenSea ? SurfAtSea : SurfAshore;
    const float WindTarget = bWinter ? WindInWinter : 0.f;
    SurfLevel = FMath::FInterpConstantTo(SurfLevel, SurfTarget, DeltaSeconds, 1.f / FadeSeconds);
    WindLevel = FMath::FInterpConstantTo(WindLevel, WindTarget, DeltaSeconds, 1.f / FadeSeconds);
    // Never quite silent, so a loop keeps its place instead of stopping while it is faded out.
    if (Surf) Surf->SetVolumeMultiplier(FMath::Max(SurfLevel, .001f));
    if (Wind) Wind->SetVolumeMultiplier(FMath::Max(WindLevel, .001f));
    // Now and then a few gulls, wherever it isn't snowing.
    BirdSeconds -= DeltaSeconds;
    if (BirdSeconds <= 0.f)
    {
        BirdSeconds = FMath::FRandRange(BirdsMin, BirdsMax);
        if (!bWinter) UEWSoundLibrary::PlayAsset2D(this, UEWSoundLibrary::GetSound(EEWSound::Seabirds), FMath::FRandRange(.6f, 1.f));
    }
}
