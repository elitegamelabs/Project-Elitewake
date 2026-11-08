#include "World/EWPlaces.h"

namespace EWPlaces
{
namespace
{
const FPlace Table[] = {
#include "World/EWPlacesTable.inl"
};
}

TConstArrayView<FPlace> All()
{
    return MakeArrayView(Table, UE_ARRAY_COUNT(Table));
}

const FPlace* Find(FName Id)
{
    for (const FPlace& Place : Table) if (Id == FName(Place.Id)) return &Place;
    return nullptr;
}

bool IsAt(const FPlace& Place, const FVector& Location)
{
    if (Place.ZRange > 0.f && FMath::Abs(Location.Z - Place.Z) > Place.ZRange) return false;
    // Into the place's own frame, as world_layout.Island.radius turns it (angle - turn).
    const double Dx = Location.X - Place.Centre.X, Dy = Location.Y - Place.Centre.Y;
    const double C = FMath::Cos(Place.Turn), S = FMath::Sin(Place.Turn);
    const double U = (Dx * C + Dy * S) / Place.Radii.X, V = (-Dx * S + Dy * C) / Place.Radii.Y;
    return U * U + V * V <= 1.0;
}

FText KindName(EEWPlaceKind Kind)
{
    switch (Kind)
    {
    case EEWPlaceKind::Island: return NSLOCTEXT("Elitewake", "PlaceIsland", "Islands");
    case EEWPlaceKind::Freeport: return NSLOCTEXT("Elitewake", "PlaceFreeport", "Freeports");
    case EEWPlaceKind::Reef: return NSLOCTEXT("Elitewake", "PlaceReef", "Reefs");
    case EEWPlaceKind::Cave: return NSLOCTEXT("Elitewake", "PlaceCave", "Caves");
    case EEWPlaceKind::Creature: return NSLOCTEXT("Elitewake", "PlaceCreature", "Creatures");
    }
    return FText::GetEmpty();
}
}
