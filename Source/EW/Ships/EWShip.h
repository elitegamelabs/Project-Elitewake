#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWShipTypes.h"
#include "EWShip.generated.h"

class AEWCharacter;
class UBoxComponent;
class UEWItemDefinition;
class UEWShipDefinition;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EEWFittingResult : uint8 { Installed, Removed, Busy, NotAllowed, NoMount, Occupied, NoFitting, InventoryFull };

/** How much sail is set. The helmsman steps between these; trim is automatic. */
UENUM(BlueprintType)
enum class EEWSailState : uint8 { Furled, Half, Full };

/**
 * A vessel built from a ship definition: a complete hull with fixed mounts. Players install fittings
 * (helm, sails, cannons, utility attachments) carried in their inventory at matching empty mounts.
 * The server owns every change; clients rebuild visuals from the replicated definition and fitting list.
 * The actor origin is the centre of the hull collision box.
 *
 * Sailing: a survivor holds Interact at an installed helm to take it. Their controls arrive as state
 * changes (sail steps, rudder position) that persist until changed, never as input that expires.
 * The server steps the ship in fixed increments, so speed does not depend on frame rate.
 */
UCLASS(Blueprintable)
class EW_API AEWShip : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWShip();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UBoxComponent> HullCollision;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> HullVisual;
    /** Set in the level or before FinishSpawning; it is not meant to change during play. */
    UPROPERTY(EditAnywhere, ReplicatedUsing=OnRep_Definition, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWShipDefinition> Definition;

    UFUNCTION(BlueprintPure, Category="Ship")
    TArray<FEWInstalledFitting> GetInstalledFittings() const { return Fittings; }
    UFUNCTION(BlueprintPure, Category="Ship")
    UEWItemDefinition* GetFitting(FName MountId) const;
    /** True when at least one installed fitting is of this type. */
    UFUNCTION(BlueprintPure, Category="Ship")
    bool HasFittingOfType(EEWShipMountType Type) const;
    /** The mount under the character's interaction aim, or None. Uses the shared interaction trace. */
    UFUNCTION(BlueprintPure, Category="Ship")
    FName FindAimedMount(const AEWCharacter* Character) const;
    UFUNCTION(BlueprintPure, Category="Ship")
    FTransform GetMountWorldTransform(FName MountId) const;
    /** The boarding ladder under the character's aim, or INDEX_NONE. */
    UFUNCTION(BlueprintPure, Category="Ship")
    int32 FindAimedBoardingPoint(const AEWCharacter* Character) const;
    UFUNCTION(BlueprintPure, Category="Ship")
    FVector GetBoardingPointWorld(int32 Index) const;
    /** True when the character stands on this ship's deck or rides its movement. */
    UFUNCTION(BlueprintPure, Category="Ship")
    bool IsAboard(const AEWCharacter* Character) const;
    /** Authority only. Lifts a survivor from the water or a dock onto the deck beside the ladder. */
    bool ClimbAboard(AEWCharacter* Character, int32 BoardingIndex);

    /** An anchored ship cannot sail. Ships start anchored so a moored ship never drifts. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    bool IsAnchored() const { return bAnchored; }
    /** True when the character is aiming at the anchor capstan. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    bool IsAimingAtAnchor(const AEWCharacter* Character) const;
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    FVector GetAnchorPointWorld() const;
    /** Authority only. Raises or drops the anchor; anyone able to act may work the capstan. */
    bool SetAnchored(AEWCharacter* Character, bool bNewAnchored);
    /** Tuning: how hard a dropped anchor slows the ship, in cm/s per second. */
    static constexpr float AnchorDrag = 500.f;

    /** Authority only. Moves the first carried fitting this mount accepts from the inventory onto the ship. */
    EEWFittingResult InstallFitting(AEWCharacter* Character, FName MountId);
    /** Authority only. Returns an installed fitting to the inventory; fails without loss if it is full. */
    EEWFittingResult RemoveFitting(AEWCharacter* Character, FName MountId);

    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    AEWCharacter* GetHelmsman() const { return Helmsman; }
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    EEWSailState GetSailState() const { return SailState; }
    /** Forward speed in cm/s. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetSpeed() const { return Speed; }
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetRudder() const { return Rudder; }
    /** 0–1: how much of the hull's sail capacity is fitted, weighted by sail size. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetFittedSailFraction() const;
    /** The speed the ship is accelerating toward, from its sails, fittings and heading to the wind. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float ComputeTargetSpeed() const;
    /** Where the helmsman stands, relative to the ship. */
    FVector GetHelmSeatLocal(float CapsuleHalfHeight) const;

    /** Authority only. The survivor must be able to act and the helm must be installed and free. */
    bool TakeHelm(AEWCharacter* Character);
    /** Authority only. Fails if the exit spot is blocked, unless forced. */
    bool LeaveHelm(AEWCharacter* Character, bool bForce = false);
    /** Authority only, from the helmsman: -1 hard to port, +1 hard to starboard. Held until changed. */
    bool SetRudder(AEWCharacter* Character, float NewRudder);
    /** Authority only, from the helmsman: +1 sets more sail, -1 takes it in. */
    bool StepSails(AEWCharacter* Character, int32 Direction);
    /** Authority only. Advances movement in fixed steps, carrying leftover time to the next call. */
    void SimulateSailing(float DeltaSeconds);

    /** Simulation and handling tuning. */
    static constexpr float SimulationStep = .05f;
    static constexpr float MaxCatchUpSeconds = .5f;
    static constexpr float Acceleration = 150.f;
    static constexpr float Deceleration = 250.f;
    /** The rudder bites fully from this speed (cm/s). */
    static constexpr float FullSteerageSpeed = 200.f;
    /** Turning still possible when stopped, as a fraction of full, so a ship pinned on land can turn away. */
    static constexpr float MinSteerage = .2f;

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Hold; }
    virtual float GetHoldDuration_Implementation() const override { return FittingHoldSeconds; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** Tuning: how long Interact is held to install or remove a fitting. */
    static constexpr float FittingHoldSeconds = .75f;

private:
    UPROPERTY(ReplicatedUsing=OnRep_Fittings)
    TArray<FEWInstalledFitting> Fittings;
    /** Local query boxes, one per mount, rebuilt from the definition on every machine. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UBoxComponent>> MountTargets;
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> FittingVisuals;
    /** Local query boxes and stand-in visuals for the built-in boarding ladders. */
    UPROPERTY(Transient)
    TArray<TObjectPtr<UBoxComponent>> BoardingTargets;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UStaticMeshComponent>> LadderVisuals;
    UPROPERTY(Transient)
    TObjectPtr<UBoxComponent> AnchorTarget;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> AnchorVisual;
    UPROPERTY(Replicated)
    bool bAnchored = true;
    bool bChangingFittings = false;

    UPROPERTY(Replicated)
    TObjectPtr<AEWCharacter> Helmsman;
    UPROPERTY(Replicated)
    EEWSailState SailState = EEWSailState::Furled;
    UPROPERTY(Replicated)
    float Speed = 0.f;
    UPROPERTY(Replicated)
    float Rudder = 0.f;
    float SimulationRemainder = 0.f;
    /** Set while pressed against an obstacle, so the contact is logged once rather than every step. */
    bool bAgainstObstacle = false;

    const FEWShipMount* FindHelmMount() const;
    /** The ship component under the character's interaction aim, if any. */
    const UPrimitiveComponent* TraceAimedComponent(const AEWCharacter* Character) const;
    bool IsValidHelmsman(const AEWCharacter* Character) const;
    void StepSimulation(float Step);

    UFUNCTION()
    void OnRep_Definition();
    UFUNCTION()
    void OnRep_Fittings();
    void ApplyDefinition();
    void RefreshFittingVisuals();
    /** Who may change fittings. Ship ownership and Company permissions will narrow this later. */
    bool CanModifyFittings(const AEWCharacter* Character) const;
    UEWItemDefinition* FindCarriedFitting(const AEWCharacter* Character, const FEWShipMount& Mount) const;
};
