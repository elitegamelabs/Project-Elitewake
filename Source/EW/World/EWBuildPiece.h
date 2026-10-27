#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWBuildPiece.generated.h"

class UStaticMeshComponent;

/**
 * A piece the player built with Build Mode (design: Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md).
 * Milestone 2 has one piece, the foundation: a 4 m square slab whose top is just above the ground and whose underside reaches
 * down to the lowest ground beneath it, so it stands level on uneven ground. Server-owned and replicated; the server
 * decides where it may stand (UEWBuildZones). The look is a plain placeholder slab; real meshes come with the art milestone.
 */
UCLASS()
class EW_API AEWBuildPiece : public AActor
{
    GENERATED_BODY()
public:
    AEWBuildPiece();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void OnConstruction(const FTransform& Transform) override;

    /** The foundation's footprint half sizes (cm) and slab thickness above its ground. Tuning. */
    static constexpr float HalfSize = 200.f;
    static constexpr float TopAboveGround = 20.f;
    static constexpr float SinkBelowGround = 10.f;

    /** Size the slab: its top and underside heights in world space. Set by the server before the piece is spawned or at once after. */
    void Configure(float TopZ, float BottomZ);

    UFUNCTION(BlueprintPure, Category="Build") float GetTopZ() const { return TopZ; }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Build") TObjectPtr<UStaticMeshComponent> Slab;

private:
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float TopZ = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float BottomZ = 0.f;
    UFUNCTION() void OnRep_Shape();
    void ApplyShape();
};
