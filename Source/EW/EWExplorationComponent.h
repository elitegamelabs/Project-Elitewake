// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWExplorationComponent.generated.h"

/**
 * What this player has seen of the world (owner, October 22: the map is covered in grey mist, the mist clears in a circle round the player as they move, and what
 * has been cleared stays clear for good). A square grid laid over the world, one byte a cell, kept on the local player's controller; each player's discoveries are
 * their own. The map draws the mist from it (BuildFog).
 */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWExplorationComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWExplorationComponent();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** Cells across the grid. */
    static constexpr int32 GridSize = 1024;
    /** How far the survivor sees, cm: the mist clears this far round them (the owner asked for a circular radius; 500 m is a working value). */
    UPROPERTY(EditDefaultsOnly, Category="Exploration", meta=(ClampMin="1000")) float RevealRadius = 50000.f;

    /** The world square the grid covers: found from the regions on first use, a little wider than all of them. */
    UFUNCTION(BlueprintCallable, Category="Exploration") void EnsureBounds();
    UFUNCTION(BlueprintPure, Category="Exploration") FVector2D GetBoundsMin() const { return BoundsMin; }
    UFUNCTION(BlueprintPure, Category="Exploration") float GetBoundsSize() const { return BoundsSize; }
    /** Sets the covered square directly (tests, and a map whose regions are not placed). */
    void SetBounds(const FVector2D& Min, float Size);
    /** Clears the mist in a circle round the place. */
    UFUNCTION(BlueprintCallable, Category="Exploration") void RevealAround(FVector Location, float Radius);
    UFUNCTION(BlueprintPure, Category="Exploration") bool IsRevealed(FVector Location) const;
    /** Share of the covered square that has been cleared, 0 to 1. */
    UFUNCTION(BlueprintPure, Category="Exploration") float GetRevealedFraction() const { return float(RevealedCells) / float(GridSize * GridSize); }
    /** Changes every time something new is cleared; the map redraws its mist when it moves. */
    UFUNCTION(BlueprintPure, Category="Exploration") int32 GetRevision() const { return Revision; }
    /** Forgets everything (a new character; tests). */
    UFUNCTION(BlueprintCallable, Category="Exploration") void ForgetAll();

    /** The mist as an image: Size x Size pixels of grey with drifting cloud, clear (transparent) where the survivor has been, softly edged. */
    void BuildFog(int32 Size, float TimeSeconds, TArray<FColor>& OutPixels) const;
    /** The place the grid cell holds, for saving; and a way to load it back. */
    const TArray<uint8>& GetCells() const { return Cells; }
    void LoadCells(const TArray<uint8>& Saved, const FVector2D& Min, float Size);
private:
    bool WorldToCell(const FVector& Location, int32& X, int32& Y) const;
    TArray<uint8> Cells;
    FVector2D BoundsMin = FVector2D::ZeroVector;
    float BoundsSize = 0.f;
    int32 RevealedCells = 0;
    int32 Revision = 0;
};
