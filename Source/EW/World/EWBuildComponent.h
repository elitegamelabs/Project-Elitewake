#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/EWBuildPiece.h"
#include "EWBuildComponent.generated.h"

class AStaticMeshActor;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class SWidget;
struct FInputKeyEventArgs;

UENUM(BlueprintType)
enum class EEWBuildMode : uint8 { Off, Place, Demolish };

/**
 * Build Mode (design: CLAUDE.md). On the player controller.
 * Press B (keyboard) or click the right stick (controller) to enter it: a blue ghost of the selected piece follows where you
 * look, red with a one-line reason where it may not go (UEWBuildZones for foundations; other pieces need a foundation to attach
 * to). Place with left mouse / A / right trigger; turn it a quarter with Q and E (d-pad left and right); change the material
 * with Z and C (LB and RB); switch to demolish with X (B button); leave with B again or Escape.
 * The piece dial (owner's radial design, October 27): Tab (Y button) opens a ring of
 * the twelve piece slots; the mouse (or either analog stick) moves a pointer, the slot it points at is highlighted, and left
 * mouse / A / right trigger picks it. While Build Mode is on and the dial is closed the mouse wheel steps through the slots.
 * The server re-checks every placement and removal; the ghost is only the local player's prediction. Test access: until the
 * Builder's Plan item exists, Build Mode opens without it and pieces cost nothing (costs TBD, owner). Reach, snapping and
 * placeholder shapes and materials are tuning.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class EW_API UEWBuildComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWBuildComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** The player controller's key hook: true if the key was used here. */
    bool HandleKey(const FInputKeyEventArgs& Params);

    UFUNCTION(BlueprintCallable, Category="Build") void ToggleBuildMode();
    UFUNCTION(BlueprintCallable, Category="Build") void ToggleDemolish();
    UFUNCTION(BlueprintCallable, Category="Build") void RotateStep(int32 Direction);
    /** Place the selected piece where the ghost is, or remove the aimed piece in demolish mode (what the place key does). */
    UFUNCTION(BlueprintCallable, Category="Build") void Confirm();

    UFUNCTION(BlueprintCallable, Category="Build") void ToggleDial();
    UFUNCTION(BlueprintCallable, Category="Build") void SetDialPointer(float X, float Y);
    UFUNCTION(BlueprintCallable, Category="Build") void SelectSlot(int32 Slot);
    /** The second wheel: door frame, door, window frame, window (F / X button opens it). */
    UFUNCTION(BlueprintCallable, Category="Build") void ToggleFittings();
    UFUNCTION(BlueprintCallable, Category="Build") void SelectFitting(int32 Index);
    UFUNCTION(BlueprintPure, Category="Build") bool IsFittingsWheelOpen() const { return bDialOpen && bFittingsWheel; }
    UFUNCTION(BlueprintCallable, Category="Build") void CycleMaterial(int32 Direction);
    UFUNCTION(BlueprintCallable, Category="Build") void CycleDesign(int32 Direction);
    UFUNCTION(BlueprintCallable, Category="Build") void StepSlot(int32 Direction);

    UFUNCTION(BlueprintPure, Category="Build") EEWBuildMode GetMode() const { return Mode; }
    UFUNCTION(BlueprintPure, Category="Build") bool IsAimPlaceable() const { return bAimOk; }
    UFUNCTION(BlueprintPure, Category="Build") FString GetAimReason() const { return AimReason; }
    UFUNCTION(BlueprintPure, Category="Build") FVector GetAimLocation() const { return AimLocation; }
    UFUNCTION(BlueprintPure, Category="Build") float GetAimYaw() const { return YawDegrees; }
    UFUNCTION(BlueprintPure, Category="Build") bool IsGhostShowing() const;
    UFUNCTION(BlueprintPure, Category="Build") AEWBuildPiece* GetAimedPiece() const { return AimedPiece; }
    UFUNCTION(BlueprintPure, Category="Build") bool IsDialOpen() const { return bDialOpen; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetHoveredSlot() const { return HoveredSlot; }
    UFUNCTION(BlueprintPure, Category="Build") EEWBuildPieceType GetSelectedType() const { return SelectedType; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetMaterial() const { return MaterialIndex; }
    UFUNCTION(BlueprintPure, Category="Build") int32 GetDesign() const { return DesignIndex; }

    /** Tuning. */
    static constexpr float Reach = 1000.f;          // cm from the survivor to a piece
    static constexpr float SnapGrid = 50.f;         // cm, free placement
    static constexpr float SnapPieceRange = 250.f;  // cm: how near an edge slot must be to the aim to snap to it
    static constexpr int32 SlotCount = 12;
    static constexpr int32 FittingCount = 4;

    /** Ask the server to place a piece (what Confirm does after the ghost's checks); the server checks it again. */
    UFUNCTION(BlueprintCallable, Category="Build") void RequestPlace(EEWBuildPieceType Type, FVector Location, float InYawDegrees, int32 Material, int32 InDesign, AEWBuildPiece* BasePiece) { ServerPlace(Type, Location, InYawDegrees, Material, InDesign, BasePiece); }
    UFUNCTION(Server, Reliable) void ServerPlace(EEWBuildPieceType Type, FVector Location, float InYawDegrees, int32 Material, int32 InDesign, AEWBuildPiece* BasePiece);
    UFUNCTION(Server, Reliable) void ServerDemolish(AEWBuildPiece* Piece);

private:
    EEWBuildMode Mode = EEWBuildMode::Off;
    EEWBuildPieceType SelectedType = EEWBuildPieceType::Foundation;
    int32 MaterialIndex = 0;
    int32 DesignIndex = 0;
    float YawDegrees = 0.f;
    bool bAimOk = false;
    FString AimReason;
    FVector AimLocation = FVector::ZeroVector;
    UPROPERTY(Transient) TObjectPtr<AEWBuildPiece> AimedPiece;
    UPROPERTY(Transient) TObjectPtr<AEWBuildPiece> AimBase;
    UPROPERTY(Transient) TObjectPtr<AStaticMeshActor> GhostActor;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Glow;

    bool bDialOpen = false;
    bool bFittingsWheel = false;
    bool bLookLocked = false;
    int32 HoveredSlot = 11;
    FVector2D DialPointer = FVector2D::ZeroVector;     // -1..1, x right, y up
    TSharedPtr<SWidget> DialWidget;

    void SetMode(EEWBuildMode NewMode);
    void UpdateAim();
    void UpdateDial(float DeltaSeconds);
    void ShowDial(bool bShow);
    void ShowGhost(const FVector& Centre, const FRotator& Rotation, const FVector& Size, bool bOk);
    class AEWCharacter* GetSurvivor() const;
    static bool PlacementAllowed(UWorld* World, const FVector& Location, float Yaw, float& OutTop, float& OutBottom, FString& Reason);
    static bool AttachAllowed(UWorld* World, AEWBuildPiece* Base, EEWBuildPieceType Type, FVector& OutLocation, FVector& OutSize, FRotator& OutRotation, FString& Reason);
};
