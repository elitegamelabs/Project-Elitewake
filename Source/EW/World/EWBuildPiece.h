#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWBuildPiece.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;

/** The twelve dial slots, clockwise from the top (owner's list, October 27). */
UENUM(BlueprintType)
enum class EEWBuildPieceType : uint8
{
    TopWall, TopCorner, HalfWall, RightCeiling, RightLowerCorner, Roof,
    BottomSpiralStaircase, BottomLeftCorner, LShapeStaircase, LeftUShapeStaircase, LeftTopCorner, Foundation
};

/**
 * A piece the player built with Build Mode (design: Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md).
 * The foundation is a 4 m square slab whose top is just above the ground and whose underside reaches down to the lowest ground
 * beneath it, so it stands level on uneven ground. Every other piece attaches to a foundation (its Base) in the foundation's
 * frame: walls on an edge, pillar corners on a corner, ceilings and roofs above, staircases on its footprint. Server-owned and
 * replicated; the server decides where a piece may stand. Shapes are plain placeholder boxes (sizes are tuning, TBD); real
 * meshes come with the art milestone.
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
    static constexpr float WallHeight = 300.f;     // tuning

    static constexpr int32 MaterialCount = 4;
    static const TCHAR* TypeName(EEWBuildPieceType Type);
    /** Placeholder material names and tints (the real material tiers are TBD, owner). */
    static const TCHAR* MaterialName(int32 Material);
    static FLinearColor MaterialTint(int32 Material);

    /** Shape of an attached piece in its foundation's frame: size, middle offset from the foundation's middle, height above its top. */
    static void Spec(EEWBuildPieceType Type, FVector& Size, FVector& LocalOffset, float& Lift);
    /** Where an attached piece of this type goes on this foundation, facing Yaw. */
    static void AttachedTransform(const AEWBuildPiece* Base, EEWBuildPieceType Type, float Yaw, FVector& OutLocation, FVector& OutSize);

    /** Size the foundation slab: its top and underside heights in world space. Set by the server right after spawning. */
    void Configure(float InTopZ, float InBottomZ);
    /** Make this an attached piece (server, right after spawning at its transform). */
    void ConfigureAttached(EEWBuildPieceType InType, const FVector& InSize, int32 InMaterial, AEWBuildPiece* InBase);
    void SetMaterialIndex(int32 InMaterial);

    UFUNCTION(BlueprintPure, Category="Build") float GetTopZ() const { return TopZ; }
    UFUNCTION(BlueprintPure, Category="Build") EEWBuildPieceType GetPieceType() const { return PieceType; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetMaterialIndex() const { return MaterialIndex; }
    UFUNCTION(BlueprintPure, Category="Build") AEWBuildPiece* GetBase() const { return Base; }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Build") TObjectPtr<UStaticMeshComponent> Slab;

private:
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float TopZ = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float BottomZ = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) EEWBuildPieceType PieceType = EEWBuildPieceType::Foundation;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) FVector Size = FVector::ZeroVector;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) int32 MaterialIndex = 0;
    UPROPERTY(Replicated) TObjectPtr<AEWBuildPiece> Base;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Tint;
    UFUNCTION() void OnRep_Shape();
    void ApplyShape();
};
