#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWBuildComponent.generated.h"

class AEWBuildPiece;
class AStaticMeshActor;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
struct FInputKeyEventArgs;

UENUM(BlueprintType)
enum class EEWBuildMode : uint8 { Off, Place, Demolish };

/**
 * Build Mode (design: Design/Gameplay/BUILD_MODE_ISLAND_BUILDING_DESIGN_2026-10-27.md, milestone 2). On the player controller.
 * Press B (keyboard) or click the right stick (controller) to enter it: a blue ghost of the foundation follows where you look,
 * red with a one-line reason where it may not go (UEWBuildZones: Ports, caves, landmarks, docks and their beaches, water,
 * uneven ground, something in the way, out of reach). Place it with left mouse / right trigger, turn it a quarter with Q and E
 * (LB and RB), switch to demolish with X (B button) to remove the piece you look at, leave with B again or Escape.
 * Near an existing piece the ghost snaps edge to edge with it. The server re-checks every placement and removal; the ghost is
 * only the local player's prediction. Test access: until the Builder's Plan item exists, Build Mode opens without it, and a
 * foundation costs nothing (cost TBD, owner). Reach and snapping sizes are tuning.
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
    /** Place the foundation where the ghost is, or remove the aimed piece in demolish mode (what the place key does). */
    UFUNCTION(BlueprintCallable, Category="Build") void Confirm();

    UFUNCTION(BlueprintPure, Category="Build") EEWBuildMode GetMode() const { return Mode; }
    UFUNCTION(BlueprintPure, Category="Build") bool IsAimPlaceable() const { return bAimOk; }
    UFUNCTION(BlueprintPure, Category="Build") FString GetAimReason() const { return AimReason; }
    UFUNCTION(BlueprintPure, Category="Build") FVector GetAimLocation() const { return AimLocation; }
    UFUNCTION(BlueprintPure, Category="Build") float GetAimYaw() const { return YawDegrees; }
    UFUNCTION(BlueprintPure, Category="Build") bool IsGhostShowing() const;
    UFUNCTION(BlueprintPure, Category="Build") AEWBuildPiece* GetAimedPiece() const { return AimedPiece; }

    /** Tuning. */
    static constexpr float Reach = 1000.f;          // cm from the survivor to a piece
    static constexpr float SnapGrid = 50.f;         // cm, free placement
    static constexpr float SnapPieceRange = 250.f;  // cm: how near an edge slot must be to the aim to snap to it

    UFUNCTION(Server, Reliable) void ServerPlace(FVector Location, float InYawDegrees);
    UFUNCTION(Server, Reliable) void ServerDemolish(AEWBuildPiece* Piece);

private:
    EEWBuildMode Mode = EEWBuildMode::Off;
    float YawDegrees = 0.f;
    bool bAimOk = false;
    FString AimReason;
    FVector AimLocation = FVector::ZeroVector;
    UPROPERTY(Transient) TObjectPtr<AEWBuildPiece> AimedPiece;
    UPROPERTY(Transient) TObjectPtr<AStaticMeshActor> GhostActor;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Glow;

    void SetMode(EEWBuildMode NewMode);
    void UpdateAim();
    void ShowGhost(const FVector& Centre, float Yaw, float TopZ, float BottomZ, bool bOk);
    class AEWCharacter* GetSurvivor() const;
    static bool PlacementAllowed(UWorld* World, const FVector& Location, float Yaw, float& OutTop, float& OutBottom, FString& Reason);
};
