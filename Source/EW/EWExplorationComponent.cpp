// Copyright Elite Game Labs. All Rights Reserved.

#include "EWExplorationComponent.h"
#include "EWSurvivalComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "World/EWClimateRegion.h"
#include "GameFramework/GameModeBase.h"
#include "Ships/EWShip.h"

UEWExplorationComponent::UEWExplorationComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .5f;
    Cells.Init(0, GridSize * GridSize);
}

void UEWExplorationComponent::EnsureBounds()
{
    if (BoundsSize > 0.f || !GetWorld()) return;
    FVector2D Min(TNumericLimits<float>::Max(), TNumericLimits<float>::Max()), Max(TNumericLimits<float>::Lowest(), TNumericLimits<float>::Lowest());
    bool bFound = false;
    for (TActorIterator<AEWClimateRegion> It(GetWorld()); It; ++It)
    {
        const FVector L = It->GetActorLocation();
        Min.X = FMath::Min(Min.X, L.X - It->Radii.X); Min.Y = FMath::Min(Min.Y, L.Y - It->Radii.Y);
        Max.X = FMath::Max(Max.X, L.X + It->Radii.X); Max.Y = FMath::Max(Max.Y, L.Y + It->Radii.Y);
        bFound = true;
    }
    if (bFound)
    {
        // A square a little wider than every region, so the shores are not at the edge.
        const FVector2D Centre = (Min + Max) * .5f;
        const float Size = FMath::Max(Max.X - Min.X, Max.Y - Min.Y) * 1.2f;
        SetBounds(Centre - FVector2D(Size, Size) * .5f, Size);
    }
    else if (const APlayerController* PC = Cast<APlayerController>(GetOwner()))
    {
        const FVector L = PC->GetPawn() ? PC->GetPawn()->GetActorLocation() : FVector::ZeroVector;
        SetBounds(FVector2D(L.X, L.Y) - FVector2D(50000.f, 50000.f), 100000.f);
    }
}

void UEWExplorationComponent::SetBounds(const FVector2D& Min, float Size)
{
    BoundsMin = Min; BoundsSize = FMath::Max(1000.f, Size);
    Cells.Init(0, GridSize * GridSize); RevealedCells = 0; ++Revision;
}

bool UEWExplorationComponent::WorldToCell(const FVector& Location, int32& X, int32& Y) const
{
    if (BoundsSize <= 0.f) return false;
    X = FMath::FloorToInt((Location.X - BoundsMin.X) / BoundsSize * GridSize);
    Y = FMath::FloorToInt((Location.Y - BoundsMin.Y) / BoundsSize * GridSize);
    return X >= 0 && X < GridSize && Y >= 0 && Y < GridSize;
}

void UEWExplorationComponent::RevealAround(FVector Location, float Radius)
{
    EnsureBounds();
    if (BoundsSize <= 0.f) return;
    const float CellSize = BoundsSize / GridSize;
    // At least a cell and a half, so a wide world still clears something round the survivor.
    const float R = FMath::Max(Radius, CellSize * 1.5f);
    const int32 Reach = FMath::CeilToInt(R / CellSize);
    const int32 CX = FMath::FloorToInt((Location.X - BoundsMin.X) / CellSize), CY = FMath::FloorToInt((Location.Y - BoundsMin.Y) / CellSize);
    bool bChanged = false;
    for (int32 Y = FMath::Max(0, CY - Reach); Y <= FMath::Min(GridSize - 1, CY + Reach); ++Y)
        for (int32 X = FMath::Max(0, CX - Reach); X <= FMath::Min(GridSize - 1, CX + Reach); ++X)
        {
            const float Dx = (X + .5f) * CellSize + BoundsMin.X - Location.X, Dy = (Y + .5f) * CellSize + BoundsMin.Y - Location.Y;
            if (Dx * Dx + Dy * Dy > R * R) continue;
            uint8& Cell = Cells[Y * GridSize + X];
            if (!Cell) { Cell = 255; ++RevealedCells; bChanged = true; }
        }
    if (bChanged) { ++Revision; if (GetRevealedFraction() >= ExpandAtFraction) ExpandBounds(ExpandFactor); }
}

void UEWExplorationComponent::ExpandBounds(float Factor)
{
    if (BoundsSize <= 0.f || Factor <= 1.f) return;
    const float NewSize = BoundsSize * Factor;
    const FVector2D NewMin = BoundsMin - FVector2D(NewSize - BoundsSize, NewSize - BoundsSize) * .5f;
    TArray<uint8> Old = MoveTemp(Cells);
    Cells.Init(0, GridSize * GridSize);
    RevealedCells = 0;
    // Every old cell lands in the new, coarser grid.
    for (int32 Y = 0; Y < GridSize; ++Y)
        for (int32 X = 0; X < GridSize; ++X)
            if (Old[Y * GridSize + X])
            {
                const int32 Nx = FMath::FloorToInt(((X + .5f) / GridSize * BoundsSize + BoundsMin.X - NewMin.X) / NewSize * GridSize);
                const int32 Ny = FMath::FloorToInt(((Y + .5f) / GridSize * BoundsSize + BoundsMin.Y - NewMin.Y) / NewSize * GridSize);
                uint8& Cell = Cells[Ny * GridSize + Nx];
                if (!Cell) { Cell = 255; ++RevealedCells; }
            }
    BoundsMin = NewMin; BoundsSize = NewSize; ++Revision;
}

void UEWExplorationComponent::GrowToCover(float Size)
{
    EnsureBounds();
    for (int32 Guard = 0; BoundsSize > 0.f && BoundsSize < Size * .999f && Guard < 20; ++Guard) ExpandBounds(ExpandFactor);
}

bool UEWExplorationComponent::IsWorldEdge() const
{
    return Cast<AGameModeBase>(GetOwner()) != nullptr;
}

FVector UEWExplorationComponent::WrapLocation(FVector L) const
{
    if (BoundsSize <= 0.f) return L;
    auto Wrap = [this](double V, double Min) { return V < Min ? V + BoundsSize : V >= Min + BoundsSize ? V - BoundsSize : V; };
    return FVector(Wrap(L.X, BoundsMin.X), Wrap(L.Y, BoundsMin.Y), L.Z);
}

bool UEWExplorationComponent::IsRevealed(FVector Location) const
{
    int32 X, Y;
    return WorldToCell(Location, X, Y) && Cells[Y * GridSize + X] != 0;
}

void UEWExplorationComponent::ForgetAll()
{
    Cells.Init(0, GridSize * GridSize); RevealedCells = 0; ++Revision;
}

void UEWExplorationComponent::LoadCells(const TArray<uint8>& Saved, const FVector2D& Min, float Size)
{
    if (Saved.Num() != GridSize * GridSize) return;
    BoundsMin = Min; BoundsSize = Size; Cells = Saved;
    RevealedCells = 0; for (uint8 C : Cells) if (C) ++RevealedCells;
    ++Revision;
}

void UEWExplorationComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (IsWorldEdge())
    {
        // The world's edge, kept by the server: it grows as players clear the map, and anything past it comes out on the other side.
        UWorld* World = GetWorld();
        if (!World || !GetOwner()->HasAuthority()) return;
        EnsureBounds();
        for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
            if (const APawn* P = It->IsValid() ? It->Get()->GetPawn() : nullptr) RevealAround(P->GetActorLocation(), RevealRadius);
        for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
            if (APawn* P = It->IsValid() ? It->Get()->GetPawn() : nullptr)
            {
                const FVector Here = P->GetActorLocation(), There = WrapLocation(Here);
                if (!Here.Equals(There, 1.0) && !P->GetAttachParentActor()) P->TeleportTo(There, P->GetActorRotation());
            }
        for (TActorIterator<AEWShip> Ship(World); Ship; ++Ship)
        {
            const FVector Here = Ship->GetActorLocation(), There = WrapLocation(Here);
            if (!Here.Equals(There, 1.0)) Ship->SetActorLocation(There, false, nullptr, ETeleportType::TeleportPhysics);
        }
        return;
    }
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    if (!PC || !PC->IsLocalController() || !PC->GetPawn()) return;
    if (const UEWSurvivalComponent* Body = PC->GetPawn()->FindComponentByClass<UEWSurvivalComponent>()) if (Body->IsDead()) return;
    RevealAround(PC->GetPawn()->GetActorLocation(), RevealRadius);
}

void UEWExplorationComponent::BuildFog(int32 Size, float TimeSeconds, TArray<FColor>& OutPixels) const
{
    OutPixels.SetNumUninitialized(Size * Size);
    const int32 Block = FMath::Max(1, GridSize / Size);
    // How much of each pixel's block has been seen.
    TArray<float> Seen; Seen.SetNumUninitialized(Size * Size);
    // The image is laid out as the map shows the world: to the right is east (-X), up is north (+Y) (World/EWNorth.h).
    for (int32 Y = 0; Y < Size; ++Y)
        for (int32 X = 0; X < Size; ++X)
        {
            int32 Count = 0;
            for (int32 By = 0; By < Block; ++By)
                for (int32 Bx = 0; Bx < Block; ++Bx)
                    if (Cells[((Size - 1 - Y) * Block + By) * GridSize + (Size - 1 - X) * Block + Bx]) ++Count;
            Seen[Y * Size + X] = float(Count) / float(Block * Block);
        }
    // A soft edge: two passes of a 3 x 3 average.
    TArray<float> Soft = Seen;
    for (int32 Pass = 0; Pass < 2; ++Pass)
    {
        for (int32 Y = 0; Y < Size; ++Y)
            for (int32 X = 0; X < Size; ++X)
            {
                float Sum = 0.f; int32 N = 0;
                for (int32 Dy = -1; Dy <= 1; ++Dy)
                    for (int32 Dx = -1; Dx <= 1; ++Dx)
                    {
                        const int32 Sx = X + Dx, Sy = Y + Dy;
                        if (Sx < 0 || Sy < 0 || Sx >= Size || Sy >= Size) continue;
                        Sum += Seen[Sy * Size + Sx]; ++N;
                    }
                Soft[Y * Size + X] = Sum / N;
            }
        Seen = Soft;
    }
    for (int32 Y = 0; Y < Size; ++Y)
        for (int32 X = 0; X < Size; ++X)
        {
            // Mist: grey, thickened and thinned by two scales of slowly drifting cloud.
            const float U = float(X) / Size, V = float(Y) / Size;
            const float Cloud = FMath::PerlinNoise2D(FVector2D(U * 5.f + TimeSeconds * .02f, V * 5.f - TimeSeconds * .012f)) * .55f
                + FMath::PerlinNoise2D(FVector2D(U * 14.f - TimeSeconds * .035f, V * 14.f + TimeSeconds * .02f)) * .3f
                + FMath::PerlinNoise2D(FVector2D(U * 38.f + TimeSeconds * .05f, V * 38.f)) * .15f;
            const float Puff = FMath::Clamp(Cloud * .9f + .5f, 0.f, 1.f);                 // 0 gap .. 1 cloud
            const float Grey = FMath::Lerp(.40f, .84f, Puff * Puff * (3.f - 2.f * Puff));
            const float Revealed = FMath::SmoothStep(.2f, .8f, Seen[Y * Size + X]);
            const float Alpha = (1.f - Revealed) * FMath::Lerp(.97f, 1.f, Puff);
            OutPixels[Y * Size + X] = FLinearColor(Grey * .96f, Grey * .98f, Grey, Alpha).ToFColor(true);
        }
}
