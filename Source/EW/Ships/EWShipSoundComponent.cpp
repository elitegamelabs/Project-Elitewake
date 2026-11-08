#include "Ships/EWShipSoundComponent.h"
#include "EWGameInstance.h"
#include "Ships/EWShip.h"
#include "EWSound.h"
#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

namespace
{
    // Levels (tuning): the creak at rest and at speed; the rigging with half and full sail at speed. Speeds in cm/s.
    constexpr float CreakAtRest = .3f, CreakAtSpeed = 1.f, RiggingHalf = .55f, RiggingFull = 1.f, FullSpeed = 800.f;
    // Less water aboard than a moment ago by this much (kg) means a bucket went over the side.
    constexpr float BailDrop = 5.f;
}

UEWShipSoundComponent::UEWShipSoundComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .1f;
}

AEWShip* UEWShipSoundComponent::Ship() const
{
    return Cast<AEWShip>(GetOwner());
}

void UEWShipSoundComponent::BeginPlay()
{
    Super::BeginPlay();
    AEWShip* Owner = Ship();
    if (!Owner || GetNetMode() == NM_DedicatedServer)
    {
        SetComponentTickEnabled(false);
        return;
    }
    USceneComponent* Root = Owner->GetRootComponent();
    Creak = UGameplayStatics::SpawnSoundAttached(UEWSoundLibrary::GetSound(EEWSound::HullCreak), Root, NAME_None, FVector::ZeroVector,
        EAttachLocation::KeepRelativeOffset, false, 0.f, 1.f, FMath::FRandRange(0.f, 8.f), nullptr, nullptr, false);
    Rigging = UGameplayStatics::SpawnSoundAttached(UEWSoundLibrary::GetSound(EEWSound::Rigging), Root, NAME_None, FVector(0, 0, 600.f),
        EAttachLocation::KeepRelativeOffset, false, 0.f, 1.f, FMath::FRandRange(0.f, 8.f), nullptr, nullptr, false);
    LastWater = Owner->GetWaterAboard();
    bWasSinking = Owner->IsSinking();
    bWasAnchored = Owner->IsAnchored();
    LastChainCatches = Owner->GetChainCatches();
}

void UEWShipSoundComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    for (UAudioComponent* Loop : {Creak.Get(), Rigging.Get()})
        if (Loop) Loop->Stop();
    Super::EndPlay(Reason);
}

bool UEWShipSoundComponent::AreLoopsPlaying() const
{
    return Creak && Rigging && Creak->IsPlaying() && Rigging->IsPlaying();
}

void UEWShipSoundComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    const AEWShip* Owner = Ship();
    if (!Owner) return;
    const float Way = FMath::Clamp(FMath::Abs(Owner->GetSpeed()) / FullSpeed, 0.f, 1.f);
    const float SailSet = Owner->GetSailFraction();
    const float SailLevel = SailSet <= .5f
        ? FMath::Lerp(0.f, RiggingHalf, SailSet * 2.f)
        : FMath::Lerp(RiggingHalf, RiggingFull, (SailSet - .5f) * 2.f);
    // Going down, the loops give way to the groan.
    const float Afloat = Owner->IsSinking() ? 0.f : 1.f;
    CreakLevel = FMath::FInterpConstantTo(CreakLevel, Afloat * FMath::Lerp(CreakAtRest, CreakAtSpeed, Way), DeltaSeconds, 1.f);
    RiggingLevel = FMath::FInterpConstantTo(RiggingLevel, Afloat * SailLevel * FMath::Lerp(.4f, 1.f, Way), DeltaSeconds, 1.f);
    // Never quite silent, so a loop keeps its place instead of stopping while it is faded out.
    const float Ambience = UEWGameInstance::GetAmbienceVolume();      // Options (owner, November 7)
    if (Creak) Creak->SetVolumeMultiplier(FMath::Max(CreakLevel * Ambience, .001f));
    if (Rigging) Rigging->SetVolumeMultiplier(FMath::Max(RiggingLevel * Ambience, .001f));

    if (Owner->IsSinking() && !bWasSinking)
        UEWSoundLibrary::PlaySoundAt(this, EEWSound::ShipSinking, Owner->GetActorLocation());
    bWasSinking = Owner->IsSinking();

    if (Owner->IsAnchored() != bWasAnchored)
    {
        bWasAnchored = Owner->IsAnchored();
        UEWSoundLibrary::PlaySoundAt(this, bWasAnchored ? EEWSound::AnchorDrop : EEWSound::AnchorRaise, Owner->GetHawseWorld());
    }
    // The chain comes taut and snubs her up (owner, October 16): the clank, where it leaves the bow.
    if (Owner->GetChainCatches() != LastChainCatches)
    {
        LastChainCatches = Owner->GetChainCatches();
        if (Owner->IsAnchored()) UEWSoundLibrary::PlaySoundAt(this, EEWSound::AnchorCatch, Owner->GetHawseWorld());
    }

    const float Water = Owner->GetWaterAboard();
    if (Water < LastWater - BailDrop && !Owner->IsSinking())
        UEWSoundLibrary::PlaySoundAt(this, EEWSound::Bail, Owner->GetBucketWorld(), 1.f, FMath::FRandRange(.95f, 1.05f));
    LastWater = Water;
}
