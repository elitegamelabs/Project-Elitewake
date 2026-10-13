#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWShipTypes.h"
#include "EWShip.generated.h"

class AEWCharacter;
class UBoxComponent;
class UEWInventoryComponent;
class UEWItemDefinition;
class UEWShipDefinition;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EEWFittingResult : uint8 { Installed, Removed, Busy, NotAllowed, NoMount, Occupied, NoFitting, InventoryFull };

/** How much sail is set. The helmsman steps between these, and trims the sails to the wind separately. */
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
    virtual void PostInitializeComponents() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    /** Clients glide to each replicated position instead of jumping to it (see SmoothClientMotion). */
    virtual void PostNetReceiveLocationAndRotation() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UBoxComponent> HullCollision;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> HullVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> RiggingVisual;
    /** The ship's hold. Separate from anything a survivor carries. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship|Cargo")
    TObjectPtr<UEWInventoryComponent> Cargo;
    /** Set in the level or before FinishSpawning; it is not meant to change during play. */
    UPROPERTY(EditAnywhere, ReplicatedUsing=OnRep_Definition, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWShipDefinition> Definition;

    /** Deck height above the ship's origin, in cm. */
    UFUNCTION(BlueprintPure, Category="Ship")
    float GetDeckHeight() const;
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
    /** Authority only: the survivor takes hold of this ladder where they are, to climb it with forward and back. */
    bool StartClimb(AEWCharacter* Character, int32 BoardingIndex);
    /** A ladder's climbable span: heights (ship space) of a climber's middle at its foot, in the water, and at its
     *  head, by the rail. */
    void GetLadderSpan(int32 BoardingIndex, float& Bottom, float& Top) const;
    /** Where a climber of the given radius hangs on a ladder at a height, facing the hull, in ship space. */
    FTransform GetLadderPoseLocal(int32 BoardingIndex, float Height, float Radius) const;
    /** Climbing speed on a ladder, cm/s (tuning). */
    static constexpr float LadderClimbSpeed = 130.f;

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

    UFUNCTION(BlueprintPure, Category="Ship|Cargo")
    UEWInventoryComponent* GetCargo() const { return Cargo; }
    UFUNCTION(BlueprintPure, Category="Ship|Cargo")
    bool IsAimingAtCargoHatch(const AEWCharacter* Character) const;
    UFUNCTION(BlueprintPure, Category="Ship|Cargo")
    FVector GetCargoHatchWorld() const;
    /** Whether this survivor may move items in and out of the hold: alive, and aboard or at the hatch. */
    UFUNCTION(BlueprintPure, Category="Ship|Cargo")
    bool CanAccessCargo(const AEWCharacter* Character) const;
    /** Tuning: how far from the hatch a survivor not aboard may still reach the hold, in cm. */
    static constexpr float CargoReach = 400.f;

    /** Ship load: everything in the hold plus installed fittings, in kg. Survivors' carried weight is separate. */
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    float GetLoad() const;
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    float GetWeightCapacity() const;
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    bool IsOverloaded() const { return bOverloaded; }
    /** Too heavy for too long: the ship cannot sail until it is lightened below capacity. */
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    bool IsSwamped() const { return bSwamped; }
    /** Seconds left to lighten an overloaded ship before it is swamped. */
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    float GetOverloadSecondsLeft() const { return OverloadSecondsLeft; }
    /** Speed multiplier from load: 1 up to half capacity, easing to 0.6 when full, 0.4 when overloaded (tuning). */
    UFUNCTION(BlueprintPure, Category="Ship|Weight")
    float GetLoadSpeedFactor() const;
    /** Authority only. Re-reads the load, updates the overload state and advances its countdown. */
    void UpdateLoad(float DeltaSeconds);
    /** Tuning: how long an overloaded ship can sail before it is swamped. */
    static constexpr float OverloadGraceSeconds = 60.f;

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
    /** Where the sails are swung, in degrees from the centreline: positive with their booms out to starboard. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetSailAngle() const { return SailAngle; }
    /** The sail angle that would draw best on this heading: booms out to leeward, square across running before the
     *  wind and sheeted in toward the centreline heading into it. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetBestSailAngle() const;
    /** 0-1: how well the sails are trimmed to the wind; 1 at the best angle, 0 from 60 degrees away. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetTrimQuality() const;
    /** The wind's share of top speed on this heading and trim: from MinUpwindFactor up to 1 (see UEWWindSubsystem). */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetWindFactor() const;
    /** True when the ship is moved by sails (not paddled) and so has sails to trim. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    bool HasTrimmableSails() const;
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
    /** Authority only, from the helmsman: +1 swings the sails toward starboard, -1 toward port, 0 holds them.
     *  Held until changed. */
    bool SetSailTrim(AEWCharacter* Character, int32 Direction);
    /** How far the sails swing either side of the centreline, and how fast, in degrees and degrees per second (tuning). */
    static constexpr float MaxSailAngle = 85.f;
    static constexpr float SailTrimRate = 45.f;
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
    /** Clients: how quickly the shown ship closes on where the server has it (per second), how far ahead of the
     *  last update it may be predicted (s), and how far off it may be before it simply jumps there (cm). */
    static constexpr float ClientCatchUpRate = 12.f;
    static constexpr float MaxClientPrediction = .3f;
    static constexpr float ClientSnapDistance = 500.f;

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Hold; }
    virtual EEWInteractionMode GetInteractionModeFor_Implementation(AEWCharacter* Character) const override;
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
    UPROPERTY(Transient)
    TObjectPtr<UBoxComponent> CargoHatchTarget;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> CargoHatchVisual;
    UPROPERTY(Replicated)
    bool bAnchored = true;
    UPROPERTY(Replicated)
    float Load = 0.f;
    UPROPERTY(Replicated)
    bool bOverloaded = false;
    UPROPERTY(Replicated)
    bool bSwamped = false;
    UPROPERTY(Replicated)
    float OverloadSecondsLeft = OverloadGraceSeconds;
    bool bChangingFittings = false;

    UPROPERTY(Replicated)
    TObjectPtr<AEWCharacter> Helmsman;
    UPROPERTY(ReplicatedUsing=OnRep_SailState)
    EEWSailState SailState = EEWSailState::Furled;
    UPROPERTY(Replicated)
    float Speed = 0.f;
    UPROPERTY(Replicated)
    float Rudder = 0.f;
    UPROPERTY(Replicated)
    float SailAngle = 0.f;
    int8 SailTrimDirection = 0;
    /** The angle the sails are drawn at, easing toward SailAngle so they swing smoothly between updates. */
    float ShownSailAngle = 0.f;
    /** Each fitted sail's look relative to its mount, before it is swung to its trim. */
    TMap<FName, FTransform> SailLooks;
    void ShowSailTrim();
    float SimulationRemainder = 0.f;
    /** Authority: the pose after the latest fixed step and the one before it. Each frame shows the ship between
     *  the two, so it moves smoothly at any frame rate while the simulation keeps its fixed steps. */
    FTransform SimulatedPose;
    FTransform PreviousSimulatedPose;
    /** The blended pose last shown; if the actor is found elsewhere, something moved it and the steps restart there. */
    FTransform ShownPose;
    bool bHasSimulatedPose = false;
    /** Clients: the latest replicated pose and when it arrived. */
    FTransform NetPose;
    double NetPoseTime = 0.0;
    bool bHasNetPose = false;
    /** Set while pressed against an obstacle, so the contact is logged once rather than every step. */
    bool bAgainstObstacle = false;
    /** The definition supplies a hull mesh: crew collide with it rather than with the extent box. */
    bool bModelledHull = false;

    const FEWShipMount* FindHelmMount() const;
    /** The ship component under the character's interaction aim, if any. */
    const UPrimitiveComponent* TraceAimedComponent(const AEWCharacter* Character) const;
    bool IsValidHelmsman(const AEWCharacter* Character) const;
    void StepSimulation(float Step);
    /** Degrees per second the ship turns at its current speed and rudder. */
    float CurrentTurnRate() const;
    void ShowSimulatedPose();
    void SmoothClientMotion(float DeltaSeconds);

    UFUNCTION()
    void OnRep_Definition();
    UFUNCTION()
    void OnRep_Fittings();
    UFUNCTION()
    void OnRep_SailState();
    void ApplyDefinition();
    void RefreshFittingVisuals();
    /** Who may change fittings. Ship ownership and Company permissions will narrow this later. */
    bool CanModifyFittings(const AEWCharacter* Character) const;
    UEWItemDefinition* FindCarriedFitting(const AEWCharacter* Character, const FEWShipMount& Mount) const;
};
