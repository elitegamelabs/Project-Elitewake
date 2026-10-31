#include "World/EWSafeZone.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"

AEWSafeZone::AEWSafeZone()
{
    PrimaryActorTick.bCanEverTick = false;
    // Every game instance has the placed zone from the map, so it needs no replication.
    bReplicates = false;
    Bounds = CreateDefaultSubobject<USphereComponent>(TEXT("Bounds"));
    SetRootComponent(Bounds);
    Bounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Bounds->SetHiddenInGame(true);
    Bounds->ShapeColor = FColor(80, 200, 120);
    Bounds->InitSphereRadius(Radius);
}

#if WITH_EDITOR
void AEWSafeZone::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (Bounds) Bounds->SetSphereRadius(Radius);
}
#endif

bool AEWSafeZone::Contains(const FVector& Location) const
{
    return FVector::DistSquared2D(Location, GetActorLocation()) <= FMath::Square(Radius);
}

AEWSafeZone* AEWSafeZone::FindAt(const UObject* WorldContext, const FVector& Location)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return nullptr;
    for (TActorIterator<AEWSafeZone> It(World); It; ++It)
        if (It->Contains(Location)) return *It;
    return nullptr;
}

bool AEWSafeZone::IsPvPBlocked(const UObject* WorldContext, const FVector& Location)
{
    const AEWSafeZone* Zone = FindAt(WorldContext, Location);
    return Zone && Zone->bNoPvP;
}

bool AEWSafeZone::IsBuildingBlocked(const UObject* WorldContext, const FVector& Location)
{
    const AEWSafeZone* Zone = FindAt(WorldContext, Location);
    return Zone && Zone->bNoBuilding;
}

bool AEWSafeZone::KeepsHostilesOut(const UObject* WorldContext, const FVector& Location)
{
    const AEWSafeZone* Zone = FindAt(WorldContext, Location);
    return Zone && Zone->bNoHostiles;
}
