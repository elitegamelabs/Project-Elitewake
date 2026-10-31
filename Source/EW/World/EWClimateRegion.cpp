#include "World/EWClimateRegion.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Engine/Engine.h"

AEWClimateRegion::AEWClimateRegion()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Centre")));
    Climate = DefaultClimate(Region);
}

FEWClimate AEWClimateRegion::OpenSea()
{
    return DefaultClimate(EEWRegion::OpenSea);
}

FEWClimate AEWClimateRegion::DefaultClimate(EEWRegion Kind)
{
    // Working values (tuning): air C, humidity %, water C. The owner set the character of each region (humid
    // desert, jungle and swamp; cold winter; comfortable plains); the numbers are not the owner's.
    FEWClimate C;
    C.Region = Kind;
    switch (Kind)
    {
    case EEWRegion::Desert: C.AirTemperature = 34.f; C.Humidity = 75.f; C.WaterTemperature = 27.f; break;
    case EEWRegion::Winter: C.AirTemperature = -12.f; C.Humidity = 40.f; C.WaterTemperature = 2.f; break;
    case EEWRegion::Jungle: C.AirTemperature = 30.f; C.Humidity = 85.f; C.WaterTemperature = 26.f; break;
    case EEWRegion::Plains: C.AirTemperature = 20.f; C.Humidity = 45.f; C.WaterTemperature = 18.f; break;
    case EEWRegion::Swamp: C.AirTemperature = 29.f; C.Humidity = 92.f; C.WaterTemperature = 24.f; break;
    default: C.AirTemperature = 22.f; C.Humidity = 60.f; C.WaterTemperature = 20.f; break;
    }
    return C;
}

FText AEWClimateRegion::RegionName(EEWRegion Kind)
{
    switch (Kind)
    {
    case EEWRegion::Desert: return NSLOCTEXT("Elitewake", "RegionDesert", "Desert");
    case EEWRegion::Winter: return NSLOCTEXT("Elitewake", "RegionWinter", "Winter");
    case EEWRegion::Jungle: return NSLOCTEXT("Elitewake", "RegionJungle", "Jungle");
    case EEWRegion::Plains: return NSLOCTEXT("Elitewake", "RegionPlains", "Plains");
    case EEWRegion::Swamp: return NSLOCTEXT("Elitewake", "RegionSwamp", "Swamp");
    default: return NSLOCTEXT("Elitewake", "RegionOpenSea", "Open Sea");
    }
}

float AEWClimateRegion::DistanceOutside(const FVector& Location) const
{
    const FVector Here = GetActorLocation();
    const float Dx = (Location.X - Here.X) / FMath::Max(Radii.X, 1.0), Dy = (Location.Y - Here.Y) / FMath::Max(Radii.Y, 1.0);
    const float Scaled = FMath::Sqrt(Dx * Dx + Dy * Dy);
    if (Scaled <= 1.f) return 0.f;
    // Distance past the shore, measured along the way out from the centre.
    const float Out = FVector2D(Location.X - Here.X, Location.Y - Here.Y).Size() * (1.f - 1.f / Scaled);
    return OffshoreReach > 0.f ? FMath::Clamp(Out / OffshoreReach, 0.f, 1.f) : 1.f;
}

FEWClimate AEWClimateRegion::SampleClimate(const UObject* WorldContext, FVector Location)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    const FEWClimate Sea = OpenSea();
    if (!World) return Sea;
    const AEWClimateRegion* Best = nullptr;
    float BestOut = 1.f, BestScore = 2.f;
    for (TActorIterator<AEWClimateRegion> It(const_cast<UWorld*>(World)); It; ++It)
    {
        const float Out = It->DistanceOutside(Location);
        // Where two regions' circles overlap (a big island's circle reaching its neighbour's shore), the nearer centre decides.
        const float Score = Out + .001f * FVector::Dist2D(Location, It->GetActorLocation()) / FMath::Max(1.f, It->Radii.GetMax());
        if (Out < 1.f && Score < BestScore) { BestScore = Score; BestOut = Out; Best = *It; }
    }
    if (!Best) return Sea;
    FEWClimate C = Best->Climate;
    C.Region = Best->Region;
    // Offshore, the region's air eases into the sea's; the region is still named until its reach ends.
    C.AirTemperature = FMath::Lerp(C.AirTemperature, Sea.AirTemperature, BestOut);
    C.Humidity = FMath::Lerp(C.Humidity, Sea.Humidity, BestOut);
    C.WaterTemperature = FMath::Lerp(C.WaterTemperature, Sea.WaterTemperature, BestOut);
    return C;
}
