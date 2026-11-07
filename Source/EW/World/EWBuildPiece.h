#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWBuildPiece.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;

/** The twelve dial slots, clockwise from the top (owner's list, October 27), then the fittings of the second wheel. */
UENUM(BlueprintType)
enum class EEWBuildPieceType : uint8
{
    TopWall, TopCorner, HalfWall, RightCeiling, RightLowerCorner, Roof,
    BottomSpiralStaircase, BottomLeftCorner, LShapeStaircase, LeftUShapeStaircase, LeftTopCorner, Foundation,
    /** Fittings (second wheel, owner October 27): a door leaf fills a door frame (a wall with a doorway), a window pane a window frame. */
    Door, Window
};

/** One built piece as saved (single player Save Game): everything needed to rebuild it, with its Base as an index into the same list (-1 none). */
USTRUCT(BlueprintType)
struct EW_API FEWSavedPiece
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadWrite) EEWBuildPieceType Type = EEWBuildPieceType::Foundation;
    UPROPERTY(BlueprintReadWrite) FVector Location = FVector::ZeroVector;
    UPROPERTY(BlueprintReadWrite) float Yaw = 0.f;
    UPROPERTY(BlueprintReadWrite) FVector Size = FVector::ZeroVector;
    UPROPERTY(BlueprintReadWrite) float TopZ = 0.f;
    UPROPERTY(BlueprintReadWrite) float BottomZ = 0.f;
    UPROPERTY(BlueprintReadWrite) int32 Material = 0;
    UPROPERTY(BlueprintReadWrite) int32 Design = 0;
    UPROPERTY(BlueprintReadWrite) int32 BaseIndex = -1;
    UPROPERTY(BlueprintReadWrite) bool bOpen = false;
};

/**
 * A piece the player built with Build Mode (design: CLAUDE.md).
 * The foundation is a 4 m square slab whose top is just above the ground and whose underside reaches down to the lowest ground
 * beneath it, so it stands level on uneven ground. Every other piece attaches to a foundation (its Base) in the foundation's
 * frame: walls on an edge, pillar corners on a corner, ceilings and roofs above, staircases on its footprint. Server-owned and
 * replicated; the server decides where a piece may stand. Shapes are plain placeholder boxes (sizes are tuning, TBD); real
 * meshes come with the art milestone.
 */
UCLASS()
class EW_API AEWBuildPiece : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWBuildPiece();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void Tick(float DeltaSeconds) override;

    /** A door opens and closes on Interact (E / X); every other piece is not interactable. */
    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;
    UFUNCTION(BlueprintPure, Category="Build") bool IsOpen() const { return bOpen; }
    /** 0 closed .. 1 fully swung open. */
    UFUNCTION(BlueprintPure, Category="Build") float GetOpenAlpha() const { return OpenAlpha; }
    static constexpr float DoorSwingSeconds = .6f;      // tuning

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
    static void AttachedTransform(const AEWBuildPiece* Base, EEWBuildPieceType Type, FVector& OutLocation, FVector& OutSize, FRotator& OutRotation);
    /** Wall designs: 0 solid, 1 doorway (door frame), 2 window (window frame). Placeholder sizes; more designs TBD, owner. */
    static constexpr int32 DesignCount = 3;
    static constexpr float WindowWidth = 120.f;     // tuning
    static constexpr float WindowHeight = 120.f;
    static constexpr float WindowSill = 90.f;
    static bool IsFitting(EEWBuildPieceType Type) { return Type == EEWBuildPieceType::Door || Type == EEWBuildPieceType::Window; }
    static constexpr float DoorWidth = 120.f;    // tuning
    static constexpr float DoorHeight = 230.f;   // tuning
    static bool IsWall(EEWBuildPieceType Type) { return Type == EEWBuildPieceType::TopWall || Type == EEWBuildPieceType::HalfWall; }
    static bool IsStair(EEWBuildPieceType Type)
    { return Type == EEWBuildPieceType::BottomSpiralStaircase || Type == EEWBuildPieceType::LShapeStaircase || Type == EEWBuildPieceType::LeftUShapeStaircase; }

    /** One block of a staircase in its cell's frame (cm): footprint, and Top = height of its top above the cell's top.
     *  The last riser up to the ceiling's top is not a block: the ceiling itself is the top step. */
    struct FStairStep { float X0, X1, Y0, Y1, Top; };
    static constexpr float StairRise = WallHeight + 20.f;   // the ceiling's top above the cell's top; eight risers of 40 cm
    static void StairSteps(EEWBuildPieceType Type, TArray<FStairStep>& Out);

    /** Single player save: every piece in the world, bases before what stands on them; and building them again from that list. */
    static void CaptureAll(UWorld* World, TArray<FEWSavedPiece>& Out);
    static int32 RestoreAll(UWorld* World, const TArray<FEWSavedPiece>& Pieces);
    /** Put a door straight into its open or closed state (no swing). */
    void SetOpenImmediate(bool bInOpen);

    /** Size the foundation slab: its top and underside heights in world space. Set by the server right after spawning. */
    void Configure(float InTopZ, float InBottomZ);
    /** Make this an attached piece (server, right after spawning at its transform). */
    void ConfigureAttached(EEWBuildPieceType InType, const FVector& InSize, int32 InMaterial, int32 InDesign, AEWBuildPiece* InBase);
    void SetMaterialIndex(int32 InMaterial);

    UFUNCTION(BlueprintPure, Category="Build") float GetTopZ() const { return TopZ; }
    UFUNCTION(BlueprintPure, Category="Build") EEWBuildPieceType GetPieceType() const { return PieceType; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetMaterialIndex() const { return MaterialIndex; }
    UFUNCTION(BlueprintPure, Category="Build") AEWBuildPiece* GetBase() const { return Base; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetDesign() const { return Design; }
    UFUNCTION(BlueprintPure, Category="Build") FVector GetPieceSize() const { return Size; }
    UFUNCTION(BlueprintPure, Category="Build") float GetBottomZ() const { return BottomZ; }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Build") TObjectPtr<UStaticMeshComponent> Slab;
    /** Extra boxes for a doorway wall (the other jamb and the lintel). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Build") TObjectPtr<UStaticMeshComponent> Part1;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Build") TObjectPtr<UStaticMeshComponent> Part2;

private:
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float TopZ = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) float BottomZ = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) EEWBuildPieceType PieceType = EEWBuildPieceType::Foundation;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) FVector Size = FVector::ZeroVector;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) int32 MaterialIndex = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) int32 Design = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Shape) TObjectPtr<AEWBuildPiece> Base;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Extras;     // more boxes for steps and a cut-out ceiling
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Tint;
    UFUNCTION() void OnRep_Shape();
    UPROPERTY(ReplicatedUsing=OnRep_Open) bool bOpen = false;
    float OpenAlpha = 0.f;
    UFUNCTION() void OnRep_Open();
    void ApplyDoorSwing();
    void ApplyShape();
    UStaticMeshComponent* ExtraBox(int32 Index);
    /** A ceiling is cut away over the staircases standing on the same cell; this re-shapes the ceilings of that cell. */
    void RefreshCeilingsOver();
};
