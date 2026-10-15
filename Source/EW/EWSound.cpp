#include "EWSound.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "UObject/ObjectKey.h"

namespace
{
    // Each sound's takes under /Game/Elitewake/Audio (see Scripts/Setup/import_audio.py).
    const TCHAR* const Takes[][2] = {
        {TEXT("Work/S_ChopWood_v1"), nullptr},
        {TEXT("Work/S_PickaxeStone_v1"), nullptr},
        {TEXT("Work/S_GlanceClink_v1"), nullptr},
        {TEXT("Gather/S_GatherRustle_v1"), nullptr},
        {TEXT("Gather/S_Pickup_v1"), nullptr},
        {TEXT("Footsteps/S_StepSand_v1"), TEXT("Footsteps/S_StepSand_v1b")},
        {TEXT("Footsteps/S_StepSnow_v1"), nullptr},
        {TEXT("Ambience/S_AmbOceanSurf_v2"), nullptr},
        {TEXT("Ambience/S_AmbWinterWind_v2"), nullptr},
        {TEXT("Ambience/S_AmbSeabirds_v1"), nullptr},
    };
    static_assert(UE_ARRAY_COUNT(Takes) == int32(EEWSound::Seabirds) + 1, "a take for every sound");

    struct FWorldSounds { TMap<FName, int32> Counts; FName Last; int32 Total = 0; };
    TMap<FObjectKey, FWorldSounds>& Played() { static TMap<FObjectKey, FWorldSounds> Map; return Map; }

    USoundBase* LoadTake(const TCHAR* Take)
    {
        if (!Take) return nullptr;
        const FString Name = FPaths::GetCleanFilename(Take);
        return LoadObject<USoundBase>(nullptr, *FString::Printf(TEXT("/Game/Elitewake/Audio/%s.%s"), Take, *Name));
    }
}

USoundBase* UEWSoundLibrary::GetSound(EEWSound Sound)
{
    const int32 Index = int32(Sound);
    if (Index < 0 || Index >= UE_ARRAY_COUNT(Takes)) return nullptr;
    const int32 Count = Takes[Index][1] ? 2 : 1;
    USoundBase* Picked = LoadTake(Takes[Index][FMath::RandRange(0, Count - 1)]);
    return Picked ? Picked : LoadTake(Takes[Index][0]);
}

bool UEWSoundLibrary::CanPlay(const UObject* WorldContext, USoundBase* Asset, UWorld*& OutWorld)
{
    OutWorld = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    return Asset && OutWorld && OutWorld->GetNetMode() != NM_DedicatedServer;
}

void UEWSoundLibrary::Count(UWorld* World, const USoundBase* Asset)
{
    FWorldSounds& Sounds = Played().FindOrAdd(FObjectKey(World));
    ++Sounds.Counts.FindOrAdd(Asset->GetFName());
    Sounds.Last = Asset->GetFName();
    ++Sounds.Total;
}

void UEWSoundLibrary::PlaySoundAt(const UObject* WorldContext, EEWSound Sound, FVector Location, float Volume, float Pitch)
{
    PlayAssetAt(WorldContext, GetSound(Sound), Location, Volume, Pitch);
}

void UEWSoundLibrary::PlayAssetAt(const UObject* WorldContext, USoundBase* Asset, FVector Location, float Volume, float Pitch)
{
    UWorld* World;
    if (!CanPlay(WorldContext, Asset, World)) return;
    UGameplayStatics::PlaySoundAtLocation(World, Asset, Location, Volume, Pitch);
    Count(World, Asset);
}

void UEWSoundLibrary::PlayAsset2D(const UObject* WorldContext, USoundBase* Asset, float Volume)
{
    UWorld* World;
    if (!CanPlay(WorldContext, Asset, World)) return;
    UGameplayStatics::PlaySound2D(World, Asset, Volume);
    Count(World, Asset);
}

int32 UEWSoundLibrary::GetPlayCount(const UObject* WorldContext, FName AssetName)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    const FWorldSounds* Sounds = World ? Played().Find(FObjectKey(World)) : nullptr;
    const int32* Found = Sounds ? Sounds->Counts.Find(AssetName) : nullptr;
    return Found ? *Found : 0;
}

FName UEWSoundLibrary::GetLastPlayed(const UObject* WorldContext)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    const FWorldSounds* Sounds = World ? Played().Find(FObjectKey(World)) : nullptr;
    return Sounds ? Sounds->Last : NAME_None;
}

int32 UEWSoundLibrary::GetTotalPlayCount(const UObject* WorldContext)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    const FWorldSounds* Sounds = World ? Played().Find(FObjectKey(World)) : nullptr;
    return Sounds ? Sounds->Total : 0;
}
