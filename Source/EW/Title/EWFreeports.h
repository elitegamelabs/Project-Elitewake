#pragma once

#include "CoreMinimal.h"

class UWorld;

/**
 * The five Freeports a new survivor can start at (owner, November 7), one per region at its village (CLAUDE.md 5.7).
 * Centres are each Port's site from Scripts/Setup/world_layout.py PORTS (cm, north +Y); the survivor is set down on the
 * plaza in front of that Port's merchant.
 */
namespace EWFreeports
{
struct FFreeport
{
    const TCHAR* Id;          // the region, as world_layout.PORTS keys it
    const TCHAR* Name;
    const TCHAR* Island;
    const TCHAR* Region;
    const TCHAR* Line;        // one line on why to start there
    FVector2D Centre;
};

inline const FFreeport List[] = {
    {TEXT("Plains"), TEXT("Saltreach Freeport"), TEXT("P1 Starter"), TEXT("Plains"),
        TEXT("The central start: gentle land, oak, flint and the spring pond."), FVector2D(-59922.f, -66271.f)},
    {TEXT("Winter"), TEXT("Birch Haven Freeport"), TEXT("W2 Birch Haven"), TEXT("Winter"),
        TEXT("Sheltered birch valleys and fresh water in the cold north."), FVector2D(-23289.f, 617152.f)},
    {TEXT("Swamp"), TEXT("River Isle Freeport"), TEXT("S1 River Isle"), TEXT("Swamp"),
        TEXT("A river that carries ships inland through the southern marsh."), FVector2D(23552.f, -624117.f)},
    {TEXT("Desert"), TEXT("Oasis Isle Freeport"), TEXT("D1 Oasis Isle"), TEXT("Desert"),
        TEXT("The oasis spring, date palms and coconuts among the dunes."), FVector2D(-636411.f, -24016.f)},
    {TEXT("Jungle"), TEXT("Waterfall Basin Freeport"), TEXT("J1 Waterfall Basin"), TEXT("Jungle"),
        TEXT("Falls, fruit and fresh water at the jungle's river mouth."), FVector2D(645764.f, 24368.f)},
};
inline constexpr int32 Count = UE_ARRAY_COUNT(List);

inline int32 IndexOf(FName Id)
{
    for (int32 I = 0; I < Count; ++I) if (Id == FName(List[I].Id)) return I;
    return INDEX_NONE;
}

/** Where a survivor stands at a Freeport: on the plaza before its merchant, facing them. False if the Port has no merchant. */
EW_API bool FindSpawn(UWorld* World, int32 Index, FVector& OutLocation, FRotator& OutFacing);
}
