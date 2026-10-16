#include "EWSoundscapeComponent.h"
#include "EWSound.h"
#include "Components/AudioComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "World/EWDayNight.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

namespace
{
    // Loop levels in each place (tuning): the surf softer on the Winter island, where the wind takes over.
    constexpr float SurfAshore = .7f, SurfAtSea = .85f, SurfInWinter = .3f, WindInWinter = 1.f, InsectsAtNight = .6f;
    // Under a cave's roof the drips come up and everything outside falls to this much of its level.
    constexpr float CaveDrips = 1.f, OutsideInCave = .3f;
    // Each wooded region's own sound ashore (tuning): wind in the Plains' oaks, the jungle's chorus by day, the swamp's
    // frogs day and night.
    constexpr float ForestAshore = .5f, JungleByDay = .55f, SwampAshore = .7f;
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
    for (UAudioComponent* Loop : {Surf.Get(), Wind.Get(), Insects.Get(), Cave.Get(), Forest.Get(), Jungle.Get(), Swamp.Get()})
        if (Loop) Loop->Stop();
    Super::EndPlay(Reason);
}

void UEWSoundscapeComponent::Start()
{
    bStarted = true;
    Surf = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::OceanSurf), 1.f, 1.f, 0.f, nullptr, true, false);
    Wind = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::WinterWind), 1.f, 1.f, 0.f, nullptr, true, false);
    Insects = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::NightInsects), 1.f, 1.f, 0.f, nullptr, true, false);
    Cave = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::CaveDrips), 1.f, 1.f, 0.f, nullptr, true, false);
    Forest = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::ForestWind), 1.f, 1.f, 0.f, nullptr, true, false);
    Jungle = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::JungleDay), 1.f, 1.f, 0.f, nullptr, true, false);
    Swamp = UGameplayStatics::CreateSound2D(this, UEWSoundLibrary::GetSound(EEWSound::SwampFrogs), 1.f, 1.f, 0.f, nullptr, true, false);
    for (UAudioComponent* Loop : {Surf.Get(), Wind.Get(), Insects.Get(), Cave.Get(), Forest.Get(), Jungle.Get(), Swamp.Get()})
        if (Loop)
        {
            Loop->SetVolumeMultiplier(0.f);
            Loop->Play(FMath::FRandRange(0.f, 6.f));   // start somewhere in the loop, so two players don't hear it in step
        }
}

bool UEWSoundscapeComponent::IsAmbiencePlaying() const
{
    return Surf && Wind && Insects && Cave && Surf->IsPlaying() && Wind->IsPlaying() && Insects->IsPlaying() && Cave->IsPlaying();
}

bool UEWSoundscapeComponent::UnderCaveRoof(const FVector& At) const
{
    // A cave is rock built as SM_Cave_<island>_v1 (Scripts/Setup/build_caves.py): its rock overhead means inside.
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWCaveRoof), false);
    if (const APlayerController* PC = Cast<APlayerController>(GetOwner()); PC && PC->GetPawn()) Query.AddIgnoredActor(PC->GetPawn());
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, At, At + FVector(0, 0, 3000), ECC_Visibility, Query)) return false;
    const auto* Rock = Cast<UStaticMeshComponent>(Hit.GetComponent());
    return Rock && Rock->GetStaticMesh() && Rock->GetStaticMesh()->GetName().StartsWith(TEXT("SM_Cave_"));
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
        bInCave = UnderCaveRoof(Pawn->GetActorLocation() + FVector(0, 0, 60));
        const UEWDayNightSubsystem* Clock = UEWDayNightSubsystem::GetForWorld(this);
        bNight = Clock && !Clock->IsDay();
    }
    const bool bWinter = HeardRegion == EEWRegion::Winter;
    const float Outside = bInCave ? OutsideInCave : 1.f;
    const float SurfTarget = Outside * (bWinter ? SurfInWinter : HeardRegion == EEWRegion::OpenSea ? SurfAtSea : SurfAshore);
    const float WindTarget = Outside * (bWinter ? WindInWinter : 0.f);
    // Insects on warm nights ashore, not in the snow and not out at sea.
    const float InsectTarget = Outside * (bNight && !bWinter && HeardRegion != EEWRegion::OpenSea ? InsectsAtNight : 0.f);
    const float Rate = 1.f / FadeSeconds;
    SurfLevel = FMath::FInterpConstantTo(SurfLevel, SurfTarget, DeltaSeconds, Rate);
    WindLevel = FMath::FInterpConstantTo(WindLevel, WindTarget, DeltaSeconds, Rate);
    InsectLevel = FMath::FInterpConstantTo(InsectLevel, InsectTarget, DeltaSeconds, Rate);
    CaveLevel = FMath::FInterpConstantTo(CaveLevel, bInCave ? CaveDrips : 0.f, DeltaSeconds, Rate);
    // Never quite silent, so a loop keeps its place instead of stopping while it is faded out.
    if (Surf) Surf->SetVolumeMultiplier(FMath::Max(SurfLevel, .001f));
    if (Wind) Wind->SetVolumeMultiplier(FMath::Max(WindLevel, .001f));
    if (Insects) Insects->SetVolumeMultiplier(FMath::Max(InsectLevel, .001f));
    if (Cave) Cave->SetVolumeMultiplier(FMath::Max(CaveLevel, .001f));
    const bool bAshore = HeardRegion != EEWRegion::OpenSea;
    ForestLevel = FMath::FInterpConstantTo(ForestLevel, Outside * (bAshore && HeardRegion == EEWRegion::Plains ? ForestAshore : 0.f), DeltaSeconds, Rate);
    JungleLevel = FMath::FInterpConstantTo(JungleLevel, Outside * (HeardRegion == EEWRegion::Jungle && !bNight ? JungleByDay : 0.f), DeltaSeconds, Rate);
    SwampLevel = FMath::FInterpConstantTo(SwampLevel, Outside * (HeardRegion == EEWRegion::Swamp ? SwampAshore : 0.f), DeltaSeconds, Rate);
    if (Forest) Forest->SetVolumeMultiplier(FMath::Max(ForestLevel, .001f));
    if (Jungle) Jungle->SetVolumeMultiplier(FMath::Max(JungleLevel, .001f));
    if (Swamp) Swamp->SetVolumeMultiplier(FMath::Max(SwampLevel, .001f));
    RegionLevel = FMath::Max3(ForestLevel, JungleLevel, SwampLevel);
    RegionLoopName = RegionLevel < .01f ? NAME_None : ForestLevel >= RegionLevel ? FName(TEXT("ForestWind"))
        : JungleLevel >= RegionLevel ? FName(TEXT("JungleDay")) : FName(TEXT("SwampFrogs"));
    // Now and then a few gulls by day, wherever it isn't snowing, out of caves.
    BirdSeconds -= DeltaSeconds;
    if (BirdSeconds <= 0.f)
    {
        BirdSeconds = FMath::FRandRange(BirdsMin, BirdsMax);
        if (!bWinter && !bNight && !bInCave) UEWSoundLibrary::PlayAsset2D(this, UEWSoundLibrary::GetSound(EEWSound::Seabirds), FMath::FRandRange(.6f, 1.f));
    }
}
