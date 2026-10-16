#include "Ships/EWShipSoundComponent.h"
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
    // Seconds from letting the anchor go to it catching the bottom (the drop take's chain runs about this long).
    constexpr float AnchorCatchSeconds = 2.2f;
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
}

void UEWShipSoundComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    for (UAudioComponent* Loop : {Creak.Get(), Rigging.Get()})
        if (Loop) Loop->Stop();
    if (UWorld* World = GetWorld()) World->GetTimerManager().ClearTimer(AnchorCatchTimer);
    Super::EndPlay(Reason);
}

void UEWShipSoundComponent::AnchorCaught()
{
    if (const AEWShip* Owner = Ship(); Owner && Owner->IsAnchored())
        UEWSoundLibrary::PlaySoundAt(this, EEWSound::AnchorCatch, Owner->GetAnchorPointWorld());
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
    const EEWSailState Sail = Owner->GetSailState();
    const float SailLevel = Sail == EEWSailState::Full ? RiggingFull : Sail == EEWSailState::Half ? RiggingHalf : 0.f;
    // Going down, the loops give way to the groan.
    const float Afloat = Owner->IsSinking() ? 0.f : 1.f;
    CreakLevel = FMath::FInterpConstantTo(CreakLevel, Afloat * FMath::Lerp(CreakAtRest, CreakAtSpeed, Way), DeltaSeconds, 1.f);
    RiggingLevel = FMath::FInterpConstantTo(RiggingLevel, Afloat * SailLevel * FMath::Lerp(.4f, 1.f, Way), DeltaSeconds, 1.f);
    // Never quite silent, so a loop keeps its place instead of stopping while it is faded out.
    if (Creak) Creak->SetVolumeMultiplier(FMath::Max(CreakLevel, .001f));
    if (Rigging) Rigging->SetVolumeMultiplier(FMath::Max(RiggingLevel, .001f));

    if (Owner->IsSinking() && !bWasSinking)
        UEWSoundLibrary::PlaySoundAt(this, EEWSound::ShipSinking, Owner->GetActorLocation());
    bWasSinking = Owner->IsSinking();

    if (Owner->IsAnchored() != bWasAnchored)
    {
        bWasAnchored = Owner->IsAnchored();
        FTimerManager& Timers = GetWorld()->GetTimerManager();
        Timers.ClearTimer(AnchorCatchTimer);
        if (bWasAnchored)
        {
            UEWSoundLibrary::PlaySoundAt(this, EEWSound::AnchorDrop, Owner->GetAnchorPointWorld());
            Timers.SetTimer(AnchorCatchTimer, this, &UEWShipSoundComponent::AnchorCaught, AnchorCatchSeconds, false);
        }
        else UEWSoundLibrary::PlaySoundAt(this, EEWSound::AnchorRaise, Owner->GetAnchorPointWorld());
    }

    const float Water = Owner->GetWaterAboard();
    if (Water < LastWater - BailDrop && !Owner->IsSinking())
        UEWSoundLibrary::PlaySoundAt(this, EEWSound::Bail, Owner->GetBucketWorld(), 1.f, FMath::FRandRange(.95f, 1.05f));
    LastWater = Water;
}
