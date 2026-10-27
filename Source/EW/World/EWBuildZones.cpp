#include "World/EWBuildZones.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/OverlapResult.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "World/EWBuildPiece.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    struct FZone
    {
        bool bBox = false;
        float X = 0, Y = 0, R = 0, Yaw = 0, U0 = 0, U1 = 0, HalfV = 0;
        float MaxZ = TNumericLimits<float>::Max();
        FString Reason;
    };

    TArray<FZone> Zones;
    float SeaZ = -65.f, GroundAboveSea = 40.f, MaxSlopeRise = 120.f;
    bool bLoaded = false;

    void Load()
    {
        if (bLoaded) return;
        bLoaded = true;
        FString Text;
        if (!FFileHelper::LoadFileToString(Text, *(FPaths::ProjectContentDir() / TEXT("Elitewake/Data/BuildZones.json")))) return;
        TSharedPtr<FJsonObject> Root;
        if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root) || !Root.IsValid()) return;
        SeaZ = Root->GetNumberField(TEXT("sea_z"));
        GroundAboveSea = Root->GetNumberField(TEXT("ground_above_sea"));
        MaxSlopeRise = Root->GetNumberField(TEXT("max_slope_rise"));
        for (const TSharedPtr<FJsonValue>& Value : Root->GetArrayField(TEXT("shapes")))
        {
            const TSharedPtr<FJsonObject> S = Value->AsObject();
            FZone Z;
            Z.bBox = S->GetStringField(TEXT("kind")) == TEXT("box");
            Z.X = S->GetNumberField(TEXT("x"));
            Z.Y = S->GetNumberField(TEXT("y"));
            Z.Reason = S->GetStringField(TEXT("reason"));
            if (S->HasField(TEXT("max_z"))) Z.MaxZ = S->GetNumberField(TEXT("max_z"));
            if (Z.bBox)
            {
                Z.Yaw = S->GetNumberField(TEXT("yaw"));
                Z.U0 = S->GetNumberField(TEXT("u0"));
                Z.U1 = S->GetNumberField(TEXT("u1"));
                Z.HalfV = S->GetNumberField(TEXT("half_v"));
            }
            else Z.R = S->GetNumberField(TEXT("r"));
            Zones.Add(Z);
        }
    }

    /** True for the island, sea-floor and seamount ground meshes; trees, rocks, buildings and pieces are not ground. */
    bool IsTerrain(const UPrimitiveComponent* Component)
    {
        const UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Component);
        const UStaticMesh* Asset = Mesh ? Mesh->GetStaticMesh() : nullptr;
        if (!Asset) return false;
        const FString Name = Asset->GetName();
        return Name.StartsWith(TEXT("SM_Island_")) || Name.StartsWith(TEXT("SM_SeaFloor")) || Name.StartsWith(TEXT("SM_Seamount"));
    }

    /** The ground height under a point: the terrain mesh's surface, whatever stands on it. */
    bool GroundAt(UWorld* World, float X, float Y, float& OutZ)
    {
        // A trace stops at the first thing that blocks it (a treetop, a roof), so go down through whatever is not terrain.
        FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildGround), false);
        FVector From(X, Y, 200000.f);
        for (int32 Try = 0; Try < 12; ++Try)
        {
            FHitResult Hit;
            if (!World->LineTraceSingleByChannel(Hit, From, FVector(X, Y, -400000.f), ECC_Visibility, Params)) return false;
            if (IsTerrain(Hit.GetComponent())) { OutZ = Hit.ImpactPoint.Z; return true; }
            if (Hit.GetComponent()) Params.AddIgnoredComponent(Hit.GetComponent());
            else if (Hit.GetActor()) Params.AddIgnoredActor(Hit.GetActor());
            else return false;
        }
        return false;
    }
}

int32 UEWBuildZones::GetZoneCount() { Load(); return Zones.Num(); }

FString UEWBuildZones::CheckZones(float X, float Y, float GroundZ)
{
    Load();
    if (GroundZ < SeaZ + GroundAboveSea) return TEXT("Not on island ground (water or too low).");
    for (const FZone& Z : Zones)
    {
        if (GroundZ >= Z.MaxZ) continue;
        bool bIn;
        if (!Z.bBox) bIn = FVector2D::Distance(FVector2D(X, Y), FVector2D(Z.X, Z.Y)) < Z.R;
        else
        {
            const float Dx = X - Z.X, Dy = Y - Z.Y, C = FMath::Cos(Z.Yaw), S = FMath::Sin(Z.Yaw);
            const float U = Dx * C + Dy * S, V = -Dx * S + Dy * C;
            bIn = U >= Z.U0 && U <= Z.U1 && FMath::Abs(V) <= Z.HalfV;
        }
        if (bIn) return FString::Printf(TEXT("In an obstruction zone (%s)."), *Z.Reason);
    }
    return FString();
}

FString UEWBuildZones::CheckPoint(const UObject* WorldContext, float X, float Y)
{
    Load();
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    float Z;
    if (!World || !GroundAt(World, X, Y, Z)) return TEXT("No ground here.");
    return CheckZones(X, Y, Z);
}

bool UEWBuildZones::GetFootprintGround(const UObject* WorldContext, float X, float Y, float HalfX, float HalfY, float YawDegrees, float& LowZ, float& HighZ)
{
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return false;
    const float Yaw = FMath::DegreesToRadians(YawDegrees), C = FMath::Cos(Yaw), S = FMath::Sin(Yaw);
    LowZ = TNumericLimits<float>::Max();
    HighZ = TNumericLimits<float>::Lowest();
    for (int32 Sx = -1; Sx <= 1; ++Sx)
        for (int32 Sy = -1; Sy <= 1; ++Sy)
        {
            const float U = Sx * HalfX, V = Sy * HalfY;
            float Z;
            if (!GroundAt(World, X + U * C - V * S, Y + U * S + V * C, Z)) return false;
            LowZ = FMath::Min(LowZ, Z);
            HighZ = FMath::Max(HighZ, Z);
        }
    return true;
}

FString UEWBuildZones::CheckFootprint(const UObject* WorldContext, float X, float Y, float HalfX, float HalfY, float YawDegrees)
{
    Load();
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return TEXT("No world.");
    const float Yaw = FMath::DegreesToRadians(YawDegrees), C = FMath::Cos(Yaw), S = FMath::Sin(Yaw);
    float LowZ = TNumericLimits<float>::Max(), HighZ = TNumericLimits<float>::Lowest();
    for (int32 Sx = -1; Sx <= 1; ++Sx)
        for (int32 Sy = -1; Sy <= 1; ++Sy)
        {
            const float U = Sx * HalfX, V = Sy * HalfY;
            const float Px = X + U * C - V * S, Py = Y + U * S + V * C;
            float Z;
            if (!GroundAt(World, Px, Py, Z)) return TEXT("No ground here.");
            const FString Why = CheckZones(Px, Py, Z);
            if (!Why.IsEmpty()) return Why;
            LowZ = FMath::Min(LowZ, Z);
            HighZ = FMath::Max(HighZ, Z);
        }
    if (HighZ - LowZ > MaxSlopeRise) return TEXT("The ground is too uneven.");
    // Nothing solid standing on the footprint (trees, rocks, buildings, pieces, survivors): a box from just above the highest
    // ground up a body's height. The terrain itself does not count.
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildCheck), false);
    const FVector Middle(X, Y, HighZ + 20.f + 100.f);
    const FCollisionShape Box = FCollisionShape::MakeBox(FVector(HalfX - 3.f, HalfY - 3.f, 100.f));
    for (ECollisionChannel Channel : {ECC_Pawn, ECC_WorldStatic})
    {
        TArray<FOverlapResult> Overlaps;
        World->OverlapMultiByChannel(Overlaps, Middle, FQuat(FVector::UpVector, Yaw), Channel, Box, Params);
        for (const FOverlapResult& Overlap : Overlaps)
            if (Overlap.bBlockingHit && !IsTerrain(Overlap.GetComponent())) return TEXT("Something is in the way.");
    }
    return FString();
}
