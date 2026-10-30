#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWShipTypes.h"
#include "EWInventoryComponent.h"
#include "EWShip.generated.h"

class AEWCharacter;
class UBoxComponent;
class UEWInventoryComponent;
class UEWItemDefinition;
class UEWShipDefinition;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UEWShipSoundComponent;
class UEWWakeTrailComponent;
class UEWBowWaveComponent;
class AEWShipSurgeon;

/** One cannon on its mount: who mans it, where it is aimed (degrees from its rest, up is positive pitch) and
 *  whether it is loaded or being loaded. Replicated with the ship. */
USTRUCT(BlueprintType)
struct FEWCannonState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    FName MountId;
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    TObjectPtr<AEWCharacter> Gunner;
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    float Yaw = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    float Pitch = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    bool bLoaded = false;
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    bool bLoading = false;
    /** A hired gunner (a Port NPC signed on with Gunner Articles) serves this cannon: loads it from the hold and fires
     *  with the volley whenever a survivor fires a cannon of this ship (owner, October 18). */
    UPROPERTY(BlueprintReadOnly, Category="Cannon")
    bool bCrewed = false;
};

/** Where round shot holed the hull, in the ship's space, and which way the planking faced there. */
USTRUCT(BlueprintType)
struct FEWHullHole
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Hull")
    FVector_NetQuantize10 Local;
    UPROPERTY(BlueprintReadOnly, Category="Hull")
    FVector_NetQuantizeNormal Normal;
};

UENUM(BlueprintType)
enum class EEWFittingResult : uint8 { Installed, Removed, Busy, NotAllowed, NoMount, Occupied, NoFitting, InventoryFull, NeedsRailing, RailingHoldsCannons };

/** How much sail is set. The helmsman steps through five positions and trims to the wind separately. */
UENUM(BlueprintType)
enum class EEWSailState : uint8 { Furled, Quarter, Half, ThreeQuarter, Full };

/** One sail's own setting and who works it (owner, October 18: crew dependency). A sail with a hired sailhand follows the
 *  helm's orders; any sail can be worked by hand at its lines (the pin rail at the foot of its mast). Replicated. */
USTRUCT(BlueprintType)
struct FEWSailLine
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Sail")
    FName MountId;
    UPROPERTY(BlueprintReadOnly, Category="Sail")
    EEWSailState State = EEWSailState::Furled;
    /** A hired sailhand (a Port NPC signed on with Sailhand's Articles) stands at these lines. */
    UPROPERTY(BlueprintReadOnly, Category="Sail")
    bool bCrewed = false;
    /** A survivor working these lines by hand, if any. */
    UPROPERTY(BlueprintReadOnly, Category="Sail")
    TObjectPtr<AEWCharacter> Worker;
};

/**
 * A ship as a save keeps her (M7 persistence, October 30): where she lies, her class, what is fitted, her hold, her hull (health,
 * holes, water aboard), her anchor, every sail's setting and hired hand, every cannon's hired gunner and charge, and which ports are
 * open. Nobody aboard is kept here (survivors are saved on their own); a ship placed in the map is matched by its name.
 */
USTRUCT(BlueprintType)
struct FEWSavedShip
{
    GENERATED_BODY()
    /** The placed ship's name in the map; none for a ship bought or spawned in play. */
    UPROPERTY(BlueprintReadOnly, Category="Save") FName MapName;
    UPROPERTY(BlueprintReadOnly, Category="Save") TSubclassOf<class AEWShip> ShipClass;
    UPROPERTY(BlueprintReadOnly, Category="Save") TObjectPtr<UEWShipDefinition> Definition;
    UPROPERTY(BlueprintReadOnly, Category="Save") FTransform Transform;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWInstalledFitting> Fittings;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWInventoryEntry> Cargo;
    UPROPERTY(BlueprintReadOnly, Category="Save") float HullHealth = -1.f;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWHullHole> Holes;
    UPROPERTY(BlueprintReadOnly, Category="Save") float WaterAboard = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Save") bool bAnchored = true;
    UPROPERTY(BlueprintReadOnly, Category="Save") EEWSailState SailState = EEWSailState::Furled;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSailLine> SailLines;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWCannonState> Cannons;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FName> OpenGunports;
};

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
    /** Her creaks and rigging, her going down and the bucket's splash, on every screen near (Source/EW/Ships/EWShipSoundComponent). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWShipSoundComponent> Sounds;
    /** The foam she leaves on the water, about 20 m of it along her track (Source/EW/Ships/EWWakeTrailComponent). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWWakeTrailComponent> WakeTrail;
    /** The water her hull pushes aside: bow waves and the wash along her sides (Source/EW/Ships/EWBowWaveComponent). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWBowWaveComponent> BowWave;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> HullVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> RiggingVisual;
    /** Foam on the water behind the stern, stronger the faster the ship goes; drawn on every machine. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UStaticMeshComponent> WakeVisual;
    /** Height of the sea surface the ship floats in, in world cm. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    float SurfaceZ = -65.f;
    /** How far the ship leans to leeward under sail now, in degrees (part of its roll). */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetHeel() const { return Heel; }
    /** The swell and the heel, as a roll and pitch in degrees and a rise in cm, for a moment of the ship's own time. */
    void GetSwayAt(float Time, float& OutRoll, float& OutPitch, float& OutRise) const;
    /** How hard the swell rocks a sloop-sized hull, and how far full sail heels it, at most (tuning); smaller
     *  hulls rock more. */
    static constexpr float SwellRoll = 1.4f;
    static constexpr float SwellPitch = .8f;
    static constexpr float SwellRise = 6.f;
    static constexpr float MaxHeel = 6.f;
    /** 0-1: how strongly the wake shows now. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetWakeStrength() const { return WakeStrength; }
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
    /** Which way a ladder faces out from the hull, in ship space (level, unit): out of its side, or aft or forward for
     *  one on the centreline. */
    FVector GetLadderOutward(int32 BoardingIndex) const;
    /** The point on a ladder's rung line (its boarding point's offset) at a height, in ship space. */
    FVector GetLadderLineLocal(int32 BoardingIndex, float Height) const;
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
    /** The anchor's chain (owner, October 16: a ship at anchor that is pushed on moves at first, takes up the chain's
     *  slack, then the chain goes taut with a clank and slows her to a stop). Where the anchor lies on the bottom,
     *  how far the bow may range from it before the chain is taut, how many times it has come taut, and whether it
     *  is taut now. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    FVector GetAnchorBed() const { return AnchorBed; }
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    float GetChainReach() const { return ChainReach; }
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    int32 GetChainCatches() const { return ChainCatches; }
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    bool IsChainTaut() const { return bChainTaut; }
    /** Where the chain leaves the bow (the hawse), in the world. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    FVector GetHawseWorld() const;
    /** For the checks: how much of the chain is drawn out (0 stowed, 1 all out), and how many links are drawn. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    float GetChainShownOut() const { return ChainOut; }
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    int32 GetChainLinkCount() const;
    /** Tuning: the chain's slack is twice the depth under the bow, from 10 m to 40 m; tension starts slowing the ship
     *  over the last fifth of it. */
    static constexpr float ChainSlackPerDepth = 2.f;
    static constexpr float MinChainSlack = 1000.f;
    static constexpr float MaxChainSlack = 4000.f;
    static constexpr float ChainTensionShare = .2f;

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
    /** Fraction of available sail currently set, in 25% steps. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetSailFraction() const;
    static constexpr float SailFractionForState(EEWSailState State) { return static_cast<uint8>(State) * .25f; }
    /** Forward speed in cm/s. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetSpeed() const { return Speed; }
    /** Where the helmsman has put the rudder: -1 hard to port, +1 hard to starboard. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetRudder() const { return Rudder; }
    /** Where the rudder blade actually is, swinging toward GetRudder() at RudderRate; it is what turns the ship. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetRudderAngle() const { return RudderAngle; }
    /** How fast the rudder swings, in full deflections per second (tuning): from centre to hard over in 0.8 s. */
    static constexpr float RudderRate = 1.25f;
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
    /** How a fitted sail is drawn in the wind, -1 to 1 (owner, October 16: sails fill and billow when they catch the
     *  wind, go slack and flap when they don't): its size is how squarely the world's wind strikes the cloth, its
     *  sign which side the belly is blown to. 0 for a furled sail or none. Every machine works it out for itself. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float GetSailFill(FName MountId) const { return SailFill.FindRef(MountId); }
    /** Flags (owner, October 17): a flag on its mount, 0 new to 1 destroyed, or -1 for none. Flags wear only in combat:
     *  every round shot that strikes the ship frays all of its flags a little, and one that strikes near a flag tears it
     *  badly. A destroyed flag's cloth is gone (nothing comes back) and its staff stays; a torn flag taken down is lost
     *  too, so wear is never undone: there is no repair, only a newly crafted flag. */
    UFUNCTION(BlueprintPure, Category="Ship|Flags")
    float GetFlagWear(FName MountId) const;
    /** Which way a flag streams from its staff, as a world yaw in degrees: downwind of the wind it feels aboard (the
     *  world's wind less the ship's own way). Every machine works it out for itself. */
    UFUNCTION(BlueprintPure, Category="Ship|Flags")
    float GetFlagYaw(FName MountId) const { return FlagYaw.FindRef(MountId); }
    /** Tuning: how much one round shot striking the ship wears each of its flags, how much more a strike within
     *  FlagNearHitRange (cm) of a flag adds, the wind's speed for a flag's apparent wind (cm/s), and how fast a flag
     *  swings to it (degrees a second). */
    static constexpr float FlagWearPerHit = .12f;
    static constexpr float FlagWearNearHit = .45f;
    static constexpr float FlagNearHitRange = 500.f;
    static constexpr float FlagWindSpeed = 800.f;
    static constexpr float FlagSwingRate = 120.f;
    /** Whether a mount is there to use: always, unless it belongs to a railing module (FEWShipMount::ParentMount),
     *  when the module fitted on that railing must open its place (UEWItemDefinition::FittingCannonSlots). */
    UFUNCTION(BlueprintPure, Category="Ship")
    bool IsMountOpen(FName MountId) const;
    /** True when the ship is moved by sails (not paddled) and so has sails to trim. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    bool HasTrimmableSails() const;
    /** The speed the ship is accelerating toward, from its sails, fittings and heading to the wind. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    float ComputeTargetSpeed() const;
    /** Where the helmsman stands, relative to the ship. */
    FVector GetHelmSeatLocal(float CapsuleHalfHeight) const;

    /** Authority only. The survivor must be able to act and the helm must be installed and free. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool TakeHelm(AEWCharacter* Character);
    /** Authority only. Fails if the exit spot is blocked, unless forced. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool LeaveHelm(AEWCharacter* Character, bool bForce = false);
    /** Authority only, from the helmsman: -1 hard to port, +1 hard to starboard. Held until changed. */
    bool SetRudder(AEWCharacter* Character, float NewRudder);
    /** Authority only, from the helmsman: +1 sets more sail, -1 takes it in. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool StepSails(AEWCharacter* Character, int32 Direction);
    /** Authority only, from the helmsman: +1 swings the sails toward starboard, -1 toward port, 0 holds them.
     *  Held until changed. */
    bool SetSailTrim(AEWCharacter* Character, int32 Direction);
    /** Each sail's own setting: the helm's order for a crewed sail, whatever was last set by hand otherwise. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    EEWSailState GetMountSailState(FName MountId) const;
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    bool IsSailCrewed(FName MountId) const;
    /** Sail mounts with a sailhand; the helm commands only these (owner, October 18). */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    int32 GetCrewedSailCount() const;
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    AEWCharacter* GetLinesWorker(FName MountId) const;
    /** Authority only: a sailhand joins this sail mount; false if it has one already or is no sail. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool SignOnSailhand(FName MountId);
    /** Authority only (checks and test setups): a sailhand on every sail mount. Returns how many joined. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    int32 CrewEverySail();
    /** Authority only: a survivor takes a sail's lines, then Up/Down raise or lower that sail a step at a time. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool TakeLines(AEWCharacter* Character, FName MountId);
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool LeaveLines(AEWCharacter* Character);
    /** Authority only, from the survivor at the lines: +1 sets more of that sail, -1 takes it in. */
    UFUNCTION(BlueprintCallable, Category="Ship|Sailing")
    bool StepSailByHand(AEWCharacter* Character, int32 Direction);
    /** Where a sail's lines are, in the ship's space: on a pin rail at the foot of its mast. */
    UFUNCTION(BlueprintPure, Category="Ship|Sailing")
    FVector GetLinesLocal(FName MountId) const;
    /** Authority only, for Play checks: fits an item at a mount without a survivor carrying it. */
    UFUNCTION(BlueprintCallable, Category="Ship|Verification")
    bool VerificationInstallFitting(FName MountId, UEWItemDefinition* Item);
    /** Tuning: how far from the lines a survivor may stray before letting go, and how long a sailhand hauls after an order. */
    static constexpr float LinesReach = 300.f;
    static constexpr float HaulSeconds = 1.5f;
    /** How far the sails swing either side of the centreline, and how fast, in degrees and degrees per second (tuning). */
    /** The sails swing 90 degrees to either side of square across the hull: 180 in all (owner, October 16). */
    static constexpr float MaxSailAngle = 90.f;
    static constexpr float SailTrimRate = 45.f;
    /** How fast a sail's drawn fill follows the wind (FInterpTo speed, tuning): most of the way in about a second. */
    static constexpr float SailFillRate = 2.f;
    /** Authority only. Advances movement in fixed steps, carrying leftover time to the next call. */
    void SimulateSailing(float DeltaSeconds);

    /** Simulation and handling tuning. */
    static constexpr float SimulationStep = .05f;
    /** Owner, October 16: sailing from island to island took too long, so every sailing ship goes this much faster
     *  than its definition's top speed (the paddled raft keeps its pace). Tuning. */
    static constexpr float SailingPace = 1.6f;
    static constexpr float MaxCatchUpSeconds = .5f;
    static constexpr float Acceleration = 240.f;   // was 150 before the faster crossings (owner, October 16)
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
    virtual float GetHoldDurationFor_Implementation(AEWCharacter* Character) const override;
    virtual void HoldChanged_Implementation(AEWCharacter* Character, bool bHolding) override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** Tuning: how long Interact is held to install or remove a fitting. */
    static constexpr float FittingHoldSeconds = .75f;
    /** Tuning: how long Interact is held at a capstan to raise or drop the anchor, and how fast the capstan turns
     *  meanwhile, in degrees per second (it runs out half as fast again when the anchor is let go). */
    static constexpr float AnchorHoldSeconds = 3.f;
    static constexpr float CapstanTurnRate = 90.f;
    /** The survivor turning the capstan now, if any: every machine shows them pushing its bars as it turns. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    AEWCharacter* GetCapstanWorker() const { return CapstanWorker; }
    /** How far the capstan's head has turned, in degrees. */
    UFUNCTION(BlueprintPure, Category="Ship|Anchor")
    float GetCapstanTurn() const { return CapstanYaw; }

    /** Tuning: how far a cannon swings either side of its port, dips below and lifts above level (the port's
     *  opening limits it), how fast its shot leaves the muzzle in cm/s, and how long loading it takes. */
    static constexpr float CannonTraverse = 15.f;
    static constexpr float CannonDepression = 5.f;
    static constexpr float CannonElevation = 8.f;
    static constexpr float CannonMuzzleSpeed = 6000.f;
    static constexpr float CannonLoadSeconds = 5.f;
    /** Cannon mounts sit this far above the deck their carriage stands on. */
    static constexpr float CannonMountHeight = 40.f;
    /** Authority only. A survivor mans an installed cannon from behind it, aims it with the view and fires it;
     *  while they man it, it loads itself from the round shot they carry. */
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool ManCannon(AEWCharacter* Character, FName MountId);
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool LeaveCannon(AEWCharacter* Character, bool bForce = false);
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool AimCannon(AEWCharacter* Character, float Yaw, float Pitch);
    /** Authority only, from the cannon's gunner. Every hired gunner whose cannon is loaded, bears on the shot's mark and
     *  has a clear line to it fires with it (the volley). */
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool FireCannon(AEWCharacter* Character);
    /** Hired gunners (owner, October 18: Port NPCs assigned to any deck's cannons). */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    bool IsCannonCrewed(FName MountId) const;
    /** Authority only: a gunner joins an installed cannon; false if it has one or there is no cannon there. */
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool SignOnGunner(FName MountId);
    /** Authority only (checks and test setups): a gunner on every installed cannon. Returns how many joined. */
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    int32 CrewEveryCannon();
    /** Server: how many hired gunners fired with the last shot a survivor fired from this ship. */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    int32 GetLastVolley() const { return LastVolley; }
    /** Tuning: how far ahead of the muzzle the volley's mark is sought, and the slack a hired gunner's aim allows
     *  beyond its cannon's swing before it holds fire (degrees). */
    static constexpr float VolleyRange = 20000.f;
    static constexpr float VolleyAimSlack = 3.f;
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    AEWCharacter* GetCannonGunner(FName MountId) const;
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    bool IsCannonLoaded(FName MountId) const;
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    bool IsCannonLoading(FName MountId) const;
    /** Hull gunports (owner, October 17): each has a sliding dark glass cover that its cannon's gunner opens (Up) and
     *  shuts (Down), one port at a time; ports start shut. A cannon cannot fire through a shut port; it runs out as its
     *  port opens and in as it shuts, and fires only once fully run out. A railing's cannon has no port: always open. */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    bool IsGunportOpen(FName MountId) const;
    /** How far open a port is drawn, 0 shut with its cannon run in to 1 open and run out. Every machine eases it the
     *  same way from the replicated open ports. */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    float GetGunportOpening(FName MountId) const;
    /** Authority only, from the gunner of that port's cannon. */
    UFUNCTION(BlueprintCallable, Category="Ship|Cannon")
    bool SetGunportOpen(AEWCharacter* Character, bool bOpen);
    /** Tuning: how fast a port opens or shuts (of the way a second), and how far its cannon runs in, cm. */
    static constexpr float GunportRate = .8f;
    static constexpr float CannonRunIn = 50.f;
    /** Pitch and yaw from the cannon's rest, in degrees. */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    FRotator GetCannonAim(FName MountId) const;
    /** The muzzle in the world, facing where a shot would leave it. */
    UFUNCTION(BlueprintPure, Category="Ship|Cannon")
    FTransform GetCannonMuzzleWorld(FName MountId) const;
    /** Where a gunner stands, behind the cannon on the deck, in the ship's space. */
    FTransform GetGunnerSeatLocal(FName MountId, float HalfHeight) const;

    /** Tuning: how much hull health one round shot takes. */
    static constexpr float RoundShotDamage = 100.f;
    /** Holes beyond this many still cost health but are not drawn. */
    static constexpr int32 MaxShownHoles = 40;
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    float GetHullHealth() const { return HullHealth; }
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    float GetMaxHullHealth() const;
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    int32 GetHoleCount() const { return Holes.Num(); }
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    FEWHullHole GetHole(int32 Index) const { return Holes.IsValidIndex(Index) ? Holes[Index] : FEWHullHole(); }
    /** Authority only: round shot struck the hull at Where (world), the planking facing Normal there. */
    UFUNCTION(BlueprintCallable, Category="Ship|Hull")
    void TakeRoundShot(const FVector& Where, const FVector& Normal, AEWCharacter* Gunner);
    /** Authority: a shipyard makes her whole (owner, October 30: the Freeport shipwright repairs ships): full hull health, every
     *  hole patched and the water pumped out. */
    UFUNCTION(BlueprintCallable, Category="Ship|Hull")
    void RepairAtShipyard();
    /** Authority: a harbor's pilots bring her to Where (a berth, or the harbor mouth for departure): her anchor comes up, she is moved
     *  (kept at her own height on the water) and the anchor goes down there. Survivors standing aboard come with her; anyone at
     *  the helm, a cannon or the lines lets go first. False while she is sinking. */
    UFUNCTION(BlueprintCallable, Category="Ship|Anchor")
    bool TowTo(const FTransform& Where);
    /** Saving (M7): this ship as a save keeps her, and putting a saved state back on her (authority). */
    FEWSavedShip CaptureForSave() const;
    void RestoreFromSave(const FEWSavedShip& Saved);
    /** Authority: every ship afloat in World (none going down), for a save. */
    static void CaptureAll(UWorld* World, TArray<FEWSavedShip>& Out);
    /** Authority: puts the saved ships back: placed ones by name, the rest launched anew; a placed ship the save does not have was
     *  lost and is taken away. Returns how many ships were put back. */
    static int32 RestoreAll(UWorld* World, const TArray<FEWSavedShip>& Ships);
    /** Authority: a shipyard fits an item at a mount of a new hull (the same rule as fitting one by hand). */
    bool FitAtShipyard(FName MountId, UEWItemDefinition* Item) { return VerificationInstallFitting(MountId, Item); }

    /** Tuning: water each hole below the waterline lets in, kg (litres) a second. */
    static constexpr float LeakPerHole = 6.f;
    /** Tuning: water one stroke of the bucket throws over the side, kg. */
    static constexpr float BailPerStroke = 25.f;
    /** Tuning: seconds of holding Interact at the bucket for one stroke. */
    static constexpr float BailHoldSeconds = 1.f;
    /** Tuning: how much deeper the ship sits with a full load of water in her (as much as her weight capacity), cm. */
    static constexpr float MaxSettle = 60.f;
    /** Holes counted as below the waterline lie lower than this above it (the sea washes over them), cm. */
    static constexpr float WaterlineWash = 15.f;
    /** Water in the hull, kg (litres). It weighs on the ship like cargo: she settles, slows and can be swamped. */
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    float GetWaterAboard() const { return WaterAboard; }
    /** Holes below the waterline, letting water in now. */
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    int32 GetLeakCount() const;
    /** How much deeper than empty the water aboard makes her sit, cm. */
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    float GetSettle() const;
    bool IsAimingAtBucket(const AEWCharacter* Character) const;
    /** Going down: her hull was destroyed or she filled with water. Nothing aboard can be used. */
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    bool IsSinking() const { return bSinking; }
    /** Tuning: how long she takes to go under, s; how far down she goes before she is gone, cm; how far her bow dips. */
    static constexpr float SinkSeconds = 30.f;
    static constexpr float SinkDepth = 1800.f;
    static constexpr float SinkPitch = 25.f;
    /** The bailing bucket on deck, in the world. */
    UFUNCTION(BlueprintPure, Category="Ship|Hull")
    FVector GetBucketWorld() const;

public:
    /** The permanent surgeon aboard (server side; null where the hull has no deck below). */
    UFUNCTION(BlueprintPure, Category="Ship|Interior") AEWShipSurgeon* GetSurgeon() const { return Surgeon; }
private:
    UPROPERTY() TObjectPtr<AEWShipSurgeon> Surgeon;
    UPROPERTY(ReplicatedUsing=OnRep_Fittings)
    TArray<FEWInstalledFitting> Fittings;
    /** Local query boxes, one per mount, rebuilt from the definition on every machine. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UBoxComponent>> MountTargets;
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> FittingVisuals;
    /** Each fitted sail assembly's mast (FEWShipMount::MastMesh), standing in the socket while a sail is fitted. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> MastVisuals;
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
    FVector AnchorBed = FVector::ZeroVector;
    UPROPERTY(Replicated)
    float ChainReach = 0.f;
    UPROPERTY(Replicated)
    uint8 ChainCatches = 0;
    UPROPERTY(Replicated)
    bool bChainTaut = false;
    /** The bow's dip when the chain snubs her up (degrees, easing back to 0). */
    float ChainJerk = 0.f;
    uint8 ShownChainCatches = 0;
    /** The chain as drawn: how much is out (paying out after a drop, coming in at the capstan), and its links. */
    float ChainOut = 0.f;
    bool bShownAnchored = false;
    UPROPERTY(Transient)
    TObjectPtr<class UInstancedStaticMeshComponent> ChainLinks;
    FVector HawseLocal() const;
    void LayAnchor();
    void ShowChain(float DeltaSeconds);
    float ChainLength() const;
    UPROPERTY(ReplicatedUsing=OnRep_CapstanWorker)
    TObjectPtr<AEWCharacter> CapstanWorker;
    /** The worker this machine last told it was at the capstan. */
    TWeakObjectPtr<AEWCharacter> ShownCapstanWorker;
    UFUNCTION()
    void OnRep_CapstanWorker();
    void SetCapstanWorker(AEWCharacter* Worker);
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> CapstanVisual;
    float CapstanYaw = 0.f;
    UPROPERTY(Replicated)
    TArray<FEWCannonState> Cannons;
    /** Set whole from the definition as play begins, on the server; never saved with the map. */
    UPROPERTY(Replicated, Transient)
    float HullHealth = -1.f;
    /** The lanterns' lights in her cabins and holds (UEWShipDefinition::LanternLights). */
    UPROPERTY(Transient)
    TArray<TObjectPtr<class UPointLightComponent>> LanternVisuals;
    /** Tuning: a lantern's light (candelas), reach (cm) and colour. */
    static constexpr float LanternIntensity = 18.f;
    static constexpr float LanternReach = 650.f;
    /** Which hull gunports are open (FEWShipMount::bGunport); the rest are shut. */
    UPROPERTY(Replicated)
    TArray<FName> OpenGunports;
    /** Each port's drawn opening (GetGunportOpening), easing toward open or shut. */
    TMap<FName, float> GunportOpening;
    /** The gunports' covers. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> CoverVisuals;
    void ShowGunports(float DeltaSeconds);
    /** A cannon mount's transform with its cannon run in as far as its port is shut. */
    FTransform GunMountTransform(const FEWShipMount& Mount) const;
    UPROPERTY(ReplicatedUsing=OnRep_Holes)
    TArray<FEWHullHole> Holes;
    UPROPERTY(Replicated)
    float WaterAboard = 0.f;
    UPROPERTY(Replicated)
    bool bSinking = false;
    float SinkingFor = 0.f;
    /** Server: she goes down; her hold and fittings float up in wreck crates. */
    void StartSinking();
    /** Server: let water in through the holes below the waterline. */
    void UpdateLeaks(float DeltaSeconds);
    UPROPERTY(Transient)
    TObjectPtr<UBoxComponent> BucketTarget;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> BucketVisual;
    FVector BucketPoint() const;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UStaticMeshComponent>> HoleVisuals;
    UFUNCTION()
    void OnRep_Holes();
    /** Server: seconds until each loading cannon is ready. */
    TMap<FName, float> CannonLoadLeft;
    int32 LastVolley = 0;
    /** Spawns a round shot from a cannon's muzzle as aimed; the cannon is then empty. */
    bool LaunchShot(FName MountId, AEWCharacter* Shooter);
    /** Hired gunners lay their cannons on Mark and fire where they can (not Except, the survivor's own cannon). */
    int32 FireVolley(const FVector& Mark, const AActor* MarkActor, FName Except, AEWCharacter* Caller);
    bool TraceVolleyLine(FHitResult& Hit, const FVector& From, const FVector& To) const;
    /** The placeholder hired gunners standing behind their cannons, and when each last fired (for its lean). */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> GunnerVisuals;
    void ShowHiredGunners();
    static UEWItemDefinition* FindCarriedGunnerArticles(const AEWCharacter* Character);
    FEWCannonState* FindCannon(FName MountId) { return Cannons.FindByPredicate([MountId](const FEWCannonState& C) { return C.MountId == MountId; }); }
    const FEWCannonState* FindCannon(FName MountId) const { return Cannons.FindByPredicate([MountId](const FEWCannonState& C) { return C.MountId == MountId; }); }
    /** The installed cannon's barrel pivot at rest, in the ship's space; false if no cannon is fitted there. */
    bool GetCannonFrame(FName MountId, FTransform& Frame) const;
    /** Server: drop gunners who can no longer man, and load and finish loading manned cannons. */
    void UpdateCannons(float DeltaSeconds);
    bool IsGunnerHere(const AEWCharacter* Character) const;
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
    UPROPERTY(ReplicatedUsing=OnRep_SailLines)
    TArray<FEWSailLine> SailLines;
    UFUNCTION()
    void OnRep_SailLines();
    FEWSailLine* FindLine(FName MountId) { return SailLines.FindByPredicate([MountId](const FEWSailLine& L) { return L.MountId == MountId; }); }
    const FEWSailLine* FindLine(FName MountId) const { return SailLines.FindByPredicate([MountId](const FEWSailLine& L) { return L.MountId == MountId; }); }
    FEWSailLine& FindOrAddLine(FName MountId);
    FName FindAimedLines(const AEWCharacter* Character) const;
    /** Sailhand's Articles in the pack (an item with bSignsOnSailhand), or none. */
    static UEWItemDefinition* FindCarriedArticles(const AEWCharacter* Character);
    /** Server: let go for survivors who walked off or can no longer work; everywhere: the sailhands haul. */
    void UpdateSailLines(float DeltaSeconds);
    void BuildLineVisuals();
    /** The pin rail (aim target and stand-in look) and the placeholder sailhand at each sail's lines. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UBoxComponent>> LineTargets;
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> LineVisuals;
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> SailhandVisuals;
    /** Seconds each sailhand still hauls (shown), and the state last seen, to start hauling when it changes. */
    TMap<FName, float> HaulLeft;
    TMap<FName, EEWSailState> HaulSeen;
    UPROPERTY(Replicated)
    float Speed = 0.f;
    UPROPERTY(Replicated)
    float Rudder = 0.f;
    UPROPERTY(Replicated)
    float SailAngle = 0.f;
    UPROPERTY(Replicated)
    float RudderAngle = 0.f;
    int8 SailTrimDirection = 0;
    /** The angle the sails are drawn at, easing toward SailAngle so they swing smoothly between updates. */
    float ShownSailAngle = 0.f;
    /** The plain railings standing at empty railing hardpoints (FEWShipMount::EmptyMesh). */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> EmptyMountVisuals;
    /** Railings stop people (not the ship's own movement): pawns collide with them, nothing else does. */
    static void MakeRailingSolid(UStaticMeshComponent* Visual);
    /** Each fitted sail's look relative to its mount, before it is swung to its trim. */
    TMap<FName, FTransform> SailLooks;
    /** Each fitted sail's fill as drawn (GetSailFill), easing toward the wind's. */
    TMap<FName, float> SailFill;
    void ShowSailFill(float DeltaSeconds);
    /** Each flag's drawn yaw (GetFlagYaw), swinging toward downwind of its apparent wind. */
    TMap<FName, float> FlagYaw;
    void ShowFlags(float DeltaSeconds);
    /** Authority only: a round shot struck at Where (world); wears every flag, more near it, and drops destroyed ones. */
    void WearFlags(const FVector& Where);
    /** A flag mount's flag, where it flies in the world (the fitting's look on its mount). */
    FTransform GetFlagLookWorld(const FEWShipMount& Mount, const UEWItemDefinition* Item) const;
    /** Helm parts that turn with the rudder, where they rest centred, and the rudder angle they show. */
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<UStaticMeshComponent>> TurningVisuals;
    TMap<FName, FTransform> TurningRest;
    float ShownRudderAngle = 0.f;
    void ShowTurning(float DeltaSeconds);
    void ShowSailTrim();
    float SimulationRemainder = 0.f;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> WakeMaterial;
    float WakeStrength = 0.f;
    /** Server: the ship's own clock for its swell, its resting height and its current heel. */
    float SwayTime = 0.f;
    float RestZ = 0.f;
    bool bHasRestZ = false;
    float Heel = 0.f;
    /** How much more a hull this size rocks than a sloop. */
    float SwayScale() const;
    void PlaceWake();
    void ShowWake(float DeltaSeconds);
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
