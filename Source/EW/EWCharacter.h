// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Logging/LogMacros.h"
#include "TimerManager.h"
#include "Characters/EWAppearance.h"
#include "EWWorkFeedback.h"
#include "EWCharacter.generated.h"

enum class EEWSound : uint8;

class USpringArmComponent;
class UCameraComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UPointLightComponent;
class UInputAction;
class UEWSurvivalComponent;
class UEWProgressionComponent;
class UEWInventoryComponent;
class UEWEquipmentComponent;
class UEWHotbarComponent;
class UEWFootprintComponent;
class UEWWalletComponent;
class UEWArrivalComponent;
struct FInputActionValue;
class FLifetimeProperty;
class AEWShip;
class UEWItemDefinition;
class AEWFish;
class AEWAnimal;

DECLARE_LOG_CATEGORY_EXTERN(LogTemplateCharacter, Log, All);

/** High-level locomotion states exposed to animation and presentation systems. */
UENUM(BlueprintType)
enum class EEWLocomotionState : uint8
{
	Standing,
	Walking,
	Sprinting,
	Crouching,
	Prone,
	Airborne,
	Swimming
};

/**
 *  A simple player-controllable third person character
 *  Implements a controllable orbiting camera
 */
/** A survivor's hold on a ship's ladder. */
USTRUCT()
struct FEWLadderHold
{
    GENERATED_BODY()
    UPROPERTY()
    TObjectPtr<AEWShip> Ship = nullptr;
    UPROPERTY()
    int32 Index = INDEX_NONE;
    UPROPERTY()
    float Height = 0.f;
};

UCLASS(abstract)
class EW_API AEWCharacter : public ACharacter
{
	GENERATED_BODY()

    friend class UEWCharacterMovementComponent;
    friend class FEWSavedMove;

	/** Camera boom positioning the camera behind the character */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	USpringArmComponent* CameraBoom;

	/** Follow camera */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FollowCamera;

	/** The main-hand item, in the right hand, on every screen. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UStaticMeshComponent* HeldItem;

	/** The held item's own light, when it has one (a torch). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UPointLightComponent* HeldLight;
	/** The held item's flame while it burns (a lit torch). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	UStaticMeshComponent* HeldFlame;

	/** Dedicated local first-person camera. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FirstPersonCamera;

	/** Server-authoritative survival values for this character. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	UEWSurvivalComponent* SurvivalComponent;

	/** Level, experience and stat points. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Progression", meta=(AllowPrivateAccess="true"))
	UEWProgressionComponent* ProgressionComponent;

	/** Server-authoritative item stacks and carried weight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	UEWInventoryComponent* InventoryComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
    UEWEquipmentComponent* EquipmentComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
    UEWHotbarComponent* HotbarComponent;
    /** Footprints in the ground, by surface. */
    UPROPERTY(VisibleAnywhere, Category="Footprints") UEWFootprintComponent* FootprintComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Wallet", meta=(AllowPrivateAccess="true")) UEWWalletComponent* WalletComponent;
    /** The arrival prompts this survivor has been through (Phase 1). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Arrival", meta=(AllowPrivateAccess="true")) UEWArrivalComponent* ArrivalComponent;
	
protected:

	/** Jump Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* JumpAction;

	/** Move Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* MoveAction;

	/** Look Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* LookAction;

	/** Mouse Look Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* MouseLookAction;

	/** Sprint Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* SprintAction;

	/** Shared crouch / prone Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* StanceAction;

	/** First-/third-person toggle Input Action */
	UPROPERTY(EditAnywhere, Category="Input")
	UInputAction* TogglePerspectiveAction;

	/** Normal grounded movement speed. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Movement|Speed", meta=(ClampMin="0.0", Units="cm/s"))
	float WalkingSpeed = 500.0f;

	/** Grounded movement speed while sprinting. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Movement|Speed", meta=(ClampMin="0.0", Units="cm/s"))
	float SprintSpeed = 750.0f;

	/** Grounded movement speed while crouched. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Movement|Speed", meta=(ClampMin="0.0", Units="cm/s"))
	float CrouchSpeed = 300.0f;

	/** Grounded movement speed while prone. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Movement|Speed", meta=(ClampMin="0.0", Units="cm/s"))
	float ProneSpeed = 150.0f;

	/** Time the stance input must be held before entering prone. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Movement|Stance", meta=(ClampMin="0.1", Units="s"))
	float StanceHoldDuration = 0.35f;

	/** Whether this character is currently requesting sprint movement. */
	UPROPERTY(ReplicatedUsing=OnRep_IsSprinting, BlueprintReadOnly, Category="Movement|Sprint", meta=(AllowPrivateAccess="true"))
	bool bIsSprinting = false;

	/** Whether this character is currently prone. */
	UPROPERTY(ReplicatedUsing=OnRep_IsProne, BlueprintReadOnly, Category="Movement|Stance", meta=(AllowPrivateAccess="true"))
	bool bIsProne = false;

	/** Tracks whether the local player is still holding the stance input. */
	bool bStanceInputHeld = false;

    bool bSprintInputHeld = false;
    /** Controller sprint: one click of the left stick starts it and it runs until the stick is clicked again, movement stops or stamina runs out. */
    bool bSprintLatched = false;
    float SprintLatchIdle = 0.f;
    /** Local swim ascent intent; movement acceleration uses the standard saved-move path. */
    bool bSwimAscendInputHeld = false;

	/** Whether the locally controlled player is using the first-person camera. */
	UPROPERTY(BlueprintReadOnly, Category="Camera", meta=(AllowPrivateAccess="true"))
	bool bIsFirstPerson = false;

	/** Show temporary movement-state text while the locomotion foundation is validated. */
	UPROPERTY(EditDefaultsOnly, Category="Debug")
	bool bShowMovementDebug = false;

	/** Delays prone entry so a quick press remains a crouch toggle. */
	FTimerHandle StanceHoldTimer;

public:
    void CancelRestrictedActions() { bSprintLatched=false; StopSprint(); CancelStanceInput(); }

    /** True once health has run out and until the server brings the survivor back (owner, October 22). */
    UFUNCTION(BlueprintPure, Category="Death")
    bool IsDead() const;
    /** Authority only. A dead survivor's belongings drop in a bag where they fell (it stays 30 real minutes), they leave any helm, gun or ladder, and they return to
     *  life, rested and fed to half, at a safe randomized spot: ground in the same region, a meaningful distance from where they died. False if not dead. */
    bool RespawnAfterDeath();
    /** A safe place to respawn, found by tracing random points in a ring round the death spot: walkable, above the sea, clear of ships and bodies, in the same region
     *  (any region, when they died at sea). Falls back to the level's player start. */
    bool FindRespawnPoint(const FVector& DeathSpot, FVector& OutLocation) const;
    /** How far from the death spot the survivor may come back, cm (owner: a meaningful distance; tuning). The ring widens when no ground is found. */
    UPROPERTY(EditDefaultsOnly, Category="Death", meta=(ClampMin="0"))
    float RespawnMinDistance = 6000.f;
    UPROPERTY(EditDefaultsOnly, Category="Death", meta=(ClampMin="0"))
    float RespawnMaxDistance = 20000.f;
    /** How far a respawn spot keeps from any living aggressive animal, cm (Phase 1 slice 4; tuning). */
    static constexpr float RespawnHostileClearance = 3000.f;

    /** The ship whose helm this survivor holds, if any. */
    UFUNCTION(BlueprintPure, Category="Ship")
    AEWShip* GetHelmShip() const { return HelmShip; }
    /** Authority only; called by the ship when the helm is taken or left. */
    void SetHelmShip(AEWShip* Ship);
    UFUNCTION(Server, Reliable)
    void ServerHelmRudder(float Rudder);
    UFUNCTION(Server, Reliable)
    void ServerSetFacingView(bool bFace);
    UFUNCTION(Server, Reliable)
    void ServerSailStep(int8 Direction);
    UFUNCTION(Server, Reliable)
    void ServerSailTrim(int8 Direction);
    /** True while the helmsman holds the sprint key: left and right then swing the sails instead of the rudder. */
    UFUNCTION(BlueprintPure, Category="Ship")
    bool IsTrimmingSails() const { return bHelmTrimHeld; }

    /** The animal this survivor rides, if any (a rideable animal: the spider). */
    UFUNCTION(BlueprintPure, Category="Animal")
    AEWAnimal* GetMount() const { return Mount; }
    bool IsMounted() const { return Mount != nullptr; }
    /** Authority only; called by the animal when it is mounted (or with null when its rider gets off). */
    void SetMount(AEWAnimal* Animal);
    /** The rider's steering as a world-space direction on the ground (length 0 to 1). */
    UFUNCTION(Server, Unreliable)
    void ServerRideSteer(FVector2D Direction);
    UFUNCTION(Server, Reliable)
    void ServerDismount();

    /** The dead fish this survivor carries, if any. */
    UFUNCTION(BlueprintPure, Category="Fish")
    AEWFish* GetCarriedFish() const { return CarriedFish; }
    /** Authority only; called by the fish when it is picked up or set down. */
    void SetCarriedFish(AEWFish* Fish) { CarriedFish = Fish; ForceNetUpdate(); }

    /** The ship and mount of the cannon this survivor mans, if any. */
    UFUNCTION(BlueprintPure, Category="Ship")
    AEWShip* GetGunShip() const { return GunShip; }
    /** The ship whose sail lines this survivor is working by hand (AEWShip::TakeLines), if any. */
    UFUNCTION(BlueprintPure, Category="Ship")
    AEWShip* GetLinesShip() const { return LinesShip; }
    FName GetLinesMount() const { return LinesMount; }
    /** Authority only, from the ship. */
    void SetLinesPost(AEWShip* Ship, FName MountId) { LinesShip = Ship; LinesMount = MountId; ForceNetUpdate(); }
    UFUNCTION(BlueprintPure, Category="Ship")
    FName GetGunMount() const { return GunMount; }
    /** Authority only; called by the ship when a cannon is manned or left. */
    void SetGunPost(AEWShip* Ship, FName MountId);
    UFUNCTION(Server, Unreliable)
    void ServerCannonAim(float Yaw, float Pitch);
    UFUNCTION(Server, Reliable)
    void ServerFireCannon();
    /** At a cannon: mark the ship it is laid on as the hired gunners' target, or clear the mark (AEWShip::MarkTarget). */
    UFUNCTION(Server, Reliable)
    void ServerMarkTarget();
    /** The gunner opens (true) or shuts their cannon's hull gunport (AEWShip::SetGunportOpen). */
    UFUNCTION(Server, Reliable)
    void ServerSetGunport(bool bOpen);

    /** True while hanging on a ship's ladder. */
    UFUNCTION(BlueprintPure, Category="Ship")
    bool IsOnLadder() const { return Ladder.Ship != nullptr; }
    UFUNCTION(BlueprintPure, Category="Ship")
    AEWShip* GetLadderShip() const { return Ladder.Ship; }
    /** Height on the ladder in the ship's space (the climber's middle). */
    UFUNCTION(BlueprintPure, Category="Ship")
    float GetLadderHeight() const { return Ladder.Height; }
    /** Authority only; called by the ship when a survivor takes hold of its ladder. */
    void SetLadder(AEWShip* Ship, int32 BoardingIndex, float Height);
    /** Local: the Up and Down arrows (or a pad's d-pad) climbing: +1 up, -1 down, 0 still. */
    void SetLadderArrowInput(float Direction) { LadderArrowInput = Direction; }
    /** Local: Up/Down or the pad's d-pad held at a helm progressively raises or lowers sail. */
    void SetSailStepInput(float Direction) { SailStepInput = Direction; }
    /** Left/Right Arrow or LB/RB held (-1 left, +1 right, 0 none): swings the sails while at a helm, nothing otherwise. */
    void SetSailArrowInput(float Direction) { SailArrowInput = Direction; }
    UFUNCTION(Server, Reliable)
    void ServerLadderClimb(int8 Direction);
    UFUNCTION(Server, Reliable)
    void ServerLetGoOfLadder();
private:
    UPROPERTY(ReplicatedUsing=OnRep_Mount)
    TObjectPtr<AEWAnimal> Mount;
    UFUNCTION()
    void OnRep_Mount();
    FVector2D PendingRide = FVector2D::ZeroVector;
    FVector2D SentRide = FVector2D::ZeroVector;
    double SentRideAt = 0.0;
    /** Authority: leave the ladder, onto the deck at its head or into the water. */
    void ReleaseLadder(bool bOntoDeck);
    void ApplyLadderPose();
    UPROPERTY(ReplicatedUsing=OnRep_Ladder)
    FEWLadderHold Ladder;
    UFUNCTION()
    void OnRep_Ladder();
    bool bAttachedToLadder = false;
    float PendingLadderForward = 0.f;
    float LadderArrowInput = 0.f;
    float SailArrowInput = 0.f;
    int8 SentLadderDirection = 0;
    int8 LadderDirection = 0;
    UPROPERTY(ReplicatedUsing=OnRep_HelmShip)
    TObjectPtr<AEWShip> HelmShip;
    UPROPERTY(ReplicatedUsing=OnRep_GunPost)
    TObjectPtr<AEWShip> GunShip;
    UPROPERTY(Replicated)
    TObjectPtr<AEWShip> LinesShip;
    UPROPERTY(Replicated)
    FName LinesMount;
    UPROPERTY(Replicated)
    TObjectPtr<AEWFish> CarriedFish;
    UPROPERTY(Replicated)
    FName GunMount;
    UFUNCTION()
    void OnRep_GunPost();
    /** Local: the aim last sent to the server, and when. */
    FRotator SentCannonAim = FRotator(1000.f, 0.f, 0.f);
    double SentCannonAimAt = 0.0;
    UFUNCTION()
    void OnRep_HelmShip();
    /** Local helm controls gathered from movement input, sent as state changes in Tick. */
    float PendingHelmRight = 0.f;
    float PendingHelmForward = 0.f;
    float SentHelmRudder = 0.f;
    int8 LastHelmForwardSign = 0;
    float SailStepInput = 0.f;
    int8 ActiveSailStepSign = 0;
    double NextSailStepTime = 0.0;
    static constexpr double SailStepInterval = .6;
    bool bHelmTrimHeld = false;
    int8 SentSailTrim = 0;
    /** At the helm the camera stands back over the ship to show its sails and the water ahead; these restore it. */
    void SetHelmCamera(bool bAtHelm);
    float SavedArmLength = -1.f;
    FVector SavedTargetOffset = FVector::ZeroVector;
    bool bSavedCameraCollision = true;
public:

	/** Constructor */
	AEWCharacter(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

    /** Only movement changes the accepted stance after collision checks succeed. */
    void SetProneFromMovement(bool bNewIsProne);

	/** Update temporary movement-state diagnostics. */
	virtual void Tick(float DeltaSeconds) override;

protected:

	/** Enforce runtime movement capabilities that derived Blueprints may have serialized previously. */
	virtual void BeginPlay() override;

	/** Initialize input action bindings */
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	/** Register replicated character state. */
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Refresh stance-dependent movement when crouch begins. */
	virtual void OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

	/** Refresh stance-dependent movement when crouch ends. */
	virtual void OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust) override;

protected:

	/** Called for movement input */
	void Move(const FInputActionValue& Value);

	/** Called for looking input */
	void Look(const FInputActionValue& Value);

	/** One click of the left stick (L3) latches sprint on or off. */
	void ToggleSprintLatch();

	/** Begin sprint input. */
	void StartSprint();

	/** End sprint input. */
	void StopSprint();

	/** Begin timing a tap versus hold stance input. */
	void StartStanceInput();

	/** Resolve a short stance press as a crouch toggle. */
	void StopStanceInput();

	/** Clear stance timing when input is canceled without treating it as a tap. */
	void CancelStanceInput();

	/** Switch between the dedicated third- and first-person cameras. */
	void TogglePerspective();

	/** Apply the requested local camera presentation. */
	void SetFirstPerson(bool bNewFirstPerson);
	/** Local: in first person, puts the eyes at the animated head and hides the head from its own camera. */
	void ShowFirstPersonBody();
	void UpdateFirstPersonCamera(float DeltaSeconds);
	/** Every machine: the body turns with the view when facing it, and with its movement otherwise. */
	void ApplyFacing();
	/** Replicated so the server and every screen turn the body the way its owner sees it. */
	UPROPERTY(Replicated)
	bool bFacingView = false;

	/** Enter prone after the stance input has been held long enough. */
	void HandleProneHold();

	/** Toggle between standing and crouching, or rise from prone into crouch. */
	void ToggleCrouch();

	/** Apply sprint state locally and to character movement. */
	void SetSprinting(bool bNewIsSprinting);

	/** Apply prone state locally and to character movement. */
	void SetProne(bool bNewIsProne);

	/** Apply the configured movement speed for the current sprint state. */
	void ApplyMovementSpeed();

	/** Receive sprint intent on the authoritative server. */
	UFUNCTION(Server, Reliable)
	void ServerSetSprinting(bool bNewIsSprinting);

	/** Refresh movement speed when sprint state replicates. */
	UFUNCTION()
	void OnRep_IsSprinting();

	/** Refresh movement speed when prone state replicates. */
	UFUNCTION()
	void OnRep_IsProne();

public:

	/** Handles move inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoMove(float Right, float Forward);

	/** Handles look inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoLook(float Yaw, float Pitch);

	/** Handles jump pressed inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpStart();

	/** Handles jump pressed inputs from either controls or UI interfaces */
	UFUNCTION(BlueprintCallable, Category="Input")
	virtual void DoJumpEnd();

	/** Returns whether the character is currently sprinting. */
	UFUNCTION(BlueprintPure, Category="Movement|Sprint")
	bool IsSprinting() const { return bIsSprinting; }

	/** Returns whether the character is currently prone. */
	UFUNCTION(BlueprintPure, Category="Movement|Stance")
	bool IsProne() const { return bIsProne; }

	/** Returns whether the character is swimming; drives the swim animations. */
	UFUNCTION(BlueprintPure, Category="Movement|Swimming")
	bool IsSwimming() const;

	/** Returns whether the local player is using first person. */
	UFUNCTION(BlueprintPure, Category="Camera")
	bool IsFirstPerson() const { return bIsFirstPerson; }
	/** True while the body turns with the view, as it does in first person (off on a ladder or at a helm). */
	UFUNCTION(BlueprintPure, Category="Camera")
	bool IsFacingView() const { return bFacingView; }
	/** Local: switches between the third- and first-person cameras; in first person the survivor sees their own body. */
	UFUNCTION(BlueprintCallable, Category="Camera")
	void SetFirstPersonView(bool bNewFirstPerson) { SetFirstPerson(bNewFirstPerson); }
	/** Tuning: in first person the eyes sit this far ahead of the torso and above where the head starts, and lean
	 *  further forward as the survivor looks down, so the chest does not hide the feet; the camera follows this quickly. */
	static constexpr float FirstPersonEyeForward = 10.f;
	static constexpr float FirstPersonEyeUp = 6.f;
	static constexpr float FirstPersonLookDownForward = 16.f;
	static constexpr float FirstPersonFollowRate = 18.f;
	/** Tuning: how quickly the first-person eyes follow the body across (a lunge, a stride), slower than up and down. */
	static constexpr float FirstPersonSwayRate = 4.f;

	/** Returns the high-level state used by animation and presentation systems. */
	UFUNCTION(BlueprintPure, Category="Movement|Animation")
	EEWLocomotionState GetLocomotionState() const;

public:

	/** Returns CameraBoom subobject **/
	FORCEINLINE class USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	/** Returns FollowCamera subobject **/
	FORCEINLINE class UCameraComponent* GetFollowCamera() const { return FollowCamera; }
	/** The local screen's nausea, 0 to 1 (for the checks). */
	UFUNCTION(BlueprintPure, Category="Survival") float GetNausea() const { return Nausea; }

	/** Returns FirstPersonCamera subobject **/
	FORCEINLINE class UCameraComponent* GetFirstPersonCamera() const { return FirstPersonCamera; }

	/** Returns the survival-stat component. */
	UFUNCTION(BlueprintPure, Category="Survival")
	UEWSurvivalComponent* GetSurvivalComponent() const { return SurvivalComponent; }

	/** Returns the level, experience and stat-point component. */
	UFUNCTION(BlueprintPure, Category="Progression")
	UEWProgressionComponent* GetProgressionComponent() const { return ProgressionComponent; }

	/** Returns the character inventory component. */
	UFUNCTION(BlueprintPure, Category="Inventory")
	UEWInventoryComponent* GetInventoryComponent() const { return InventoryComponent; }
    UFUNCTION(BlueprintPure, Category="Wallet")
    UEWWalletComponent* GetWalletComponent() const { return WalletComponent; }
    UFUNCTION(BlueprintPure, Category="Arrival")
    UEWArrivalComponent* GetArrivalComponent() const { return ArrivalComponent; }
    UFUNCTION(BlueprintPure, Category="Equipment")
    UEWEquipmentComponent* GetEquipmentComponent() const { return EquipmentComponent; }
    UFUNCTION(BlueprintPure, Category="Hotbar")
    UEWHotbarComponent* GetHotbarComponent() const { return HotbarComponent; }

    /** Attack (Left Mouse / RT): a swing everyone sees. With nothing to gather in front, it strikes the survivor
     *  there. Swings the owner predicts locally first; the server decides every hit. */
    /** Whether this survivor may swing now: alive, on their feet, crouched or swimming, and not at a helm or on a ladder. */
    UFUNCTION(BlueprintPure, Category="Combat")
    bool CanAttack() const;
    /** Plays a swing on this machine. Variant's lowest two bits are the kind of swing (0 a plain swing or punch,
     *  1 a hatchet's chop at a tree, 2 a pickaxe's blow at a rock); the rest picks among the plain swings. */
    void PlayAttackAnimation(int32 Variant);
    /** The kind of swing this survivor makes at Target with what is in hand (see PlayAttackAnimation). */
    int32 SwingKindAt(const AActor* Target) const;
    /** Authority: a work blow reached Target at Point: chips and a shake on every screen, after the swing's
     *  contact moment, and for the striker the hit marker with what it gave or why it gave nothing. */
    void ShowWorkImpact(AActor* Target, const FVector& Point, const FVector& Normal, EEWWorkSurface Surface,
        const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal, int32 SwingKind);
    /** Authority: the survivor stoops or reaches to take something by hand (bBush: from a bush), and is told what it gave. */
    void PlayGatherMotion(bool bBush, const TArray<FEWGatherGain>& Gains);
    UFUNCTION(Client, Unreliable)
    void ClientGathered(const TArray<FEWGatherGain>& Gains);
    /** For the checks: the swing last played on this machine, and how many blows it has shown landing. */
    UFUNCTION(BlueprintPure, Category="Combat") UAnimSequenceBase* GetLastSwingAnimation() const { return LastSwingAnimation; }
    UFUNCTION(BlueprintPure, Category="Combat") int32 GetWorkImpactCount() const { return WorkImpactCount; }
    /** The warmth of everything worn (clothing insulation; none is made yet). */
    UFUNCTION(BlueprintPure, Category="Survival|Temperature") float GetClothingInsulation() const;
    /** The hatchet's chop and the pickaxe's blow, the hand gathers, and when in each swing the blow lands. */
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> ChopAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> MineAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> GatherGroundAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> GatherBushAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    float ChopContactSeconds = .45f;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    float MineContactSeconds = .5f;
    /** Authority: plays the swing for everyone else and, unless the owner already did, for the owner. */
    void BroadcastAttack(int32 Variant);
    /** Authority: strikes the first survivor within reach where this one is looking. Returns who was hit. */
    UFUNCTION(BlueprintCallable, Category="Combat")
    AEWCharacter* MeleeStrike();
    /** Authority: the survivor flinches on every screen, as from a blow. */
    void ReactToHit() { if (HasAuthority()) MulticastHitReact(); }

    /** Bare-handed damage (confirmed) and the reach of a swing (tuning). Weapons bring their own damage later. */
    static constexpr float FistDamage = 10.f;
    static constexpr float MeleeReach = 170.f;
    static constexpr float MeleeRadius = 30.f;

    /** Swing animations, played in turn, and the flinch of a survivor who is struck. */
    UPROPERTY(EditDefaultsOnly, Category="Combat")
    TArray<TObjectPtr<UAnimSequenceBase>> AttackAnimations;
    /** Swings with a tool or weapon in hand, played in turn instead of the bare-handed ones. */
    UPROPERTY(EditDefaultsOnly, Category="Combat")
    TArray<TObjectPtr<UAnimSequenceBase>> ToolSwingAnimations;
    /** Loops played on a ladder: climbing up, climbing down and holding still. */
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> LadderUpAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> LadderDownAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> LadderIdleAnimation;
    /** At a helm: hands on the wheel or tiller, and a paddle stroke on a paddled boat (played faster at a hard
     *  stroke than an easy one). */
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> HelmHoldAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> PaddleAnimation;
    /** Leaning into a capstan's bars while the anchor is worked. */
    UPROPERTY(EditDefaultsOnly, Category="Ship")
    TObjectPtr<UAnimSequenceBase> CapstanAnimation;
    /** Every machine: the ship whose capstan this survivor is turning, told by the ship. */
    void SetCapstanShip(AEWShip* Ship);
    /** The ladder or helm loop playing now, if any. */
    UFUNCTION(BlueprintPure, Category="Ship")
    UAnimSequenceBase* GetLoopAnimation() const { return PlayingLoopAnimation; }
    /** The item shown in the right hand, if any. */
    UFUNCTION(BlueprintPure, Category="Combat")
    UStaticMesh* GetHeldMesh() const;

    /** The bodies and tones survivors are made from. */
    UPROPERTY(EditDefaultsOnly, Category="Appearance")
    TSoftObjectPtr<UEWBodyRoster> BodyRoster;
    UFUNCTION(BlueprintPure, Category="Appearance")
    FEWAppearance GetAppearance() const { return Appearance; }
    /** Authority only: changes how this survivor looks on every screen. */
    void SetAppearance(const FEWAppearance& NewAppearance);
    UPROPERTY(EditDefaultsOnly, Category="Combat")
    TObjectPtr<UAnimSequenceBase> HitReactAnimation;
    /** One-shots for the core tools: drawing a newly equipped item, putting flame to a torch, drinking from a
     *  waterskin and filling one at fresh water. */
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> EquipAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> IgniteAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> DrinkAnimation;
    UPROPERTY(EditDefaultsOnly, Category="Tools")
    TObjectPtr<UAnimSequenceBase> FillAnimation;
    /** True while the held item burns. */
    UFUNCTION(BlueprintPure, Category="Tools")
    bool IsHeldItemLit() const { return bHeldItemLit; }
    /** True if Left Mouse uses the held item (lights a torch, drinks a waterskin) rather than swinging it. */
    UFUNCTION(BlueprintPure, Category="Tools")
    bool HasUsableHeldItem() const;
    /** Authority: Left Mouse with a usable item in hand. */
    UFUNCTION(Server, Reliable)
    void ServerUseHeldItem();
    /** Authority: the survivor fills the empty waterskin in their hand at fresh water. */
    bool FillHeldWaterskin();
    /** The last tool one-shot played on this machine, for the checks. */
    UFUNCTION(BlueprintPure, Category="Tools")
    UAnimSequenceBase* GetLastToolAnimation() const { return LastToolAnimation; }
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastToolAnimation(UAnimSequenceBase* Animation);

private:
    /** Shows the main-hand item in the right hand; runs whenever equipment changes, on every machine. */
    UFUNCTION()
    void RefreshHeldItem();
    UPROPERTY(ReplicatedUsing=OnRep_Appearance)
    FEWAppearance Appearance;
    UFUNCTION()
    void OnRep_Appearance();
    UPROPERTY(ReplicatedUsing=OnRep_HeldItemLit)
    bool bHeldItemLit = false;
    UFUNCTION()
    void OnRep_HeldItemLit() { RefreshHeldItem(); }
    void PlayToolAnimation(UAnimSequenceBase* Animation);
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequenceBase> LastToolAnimation;
    /** The main-hand item last shown, to play the draw when it changes. */
    TWeakObjectPtr<const UEWItemDefinition> ShownHeldItem;
    float FlickerTime = 0.f;
    /** Every machine: plays the loop for what the survivor is doing on a ladder, at a helm or at a capstan, or stops it. */
    void UpdateLoopAnimation(float DeltaSeconds);
    TWeakObjectPtr<AEWShip> CapstanShip;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequenceBase> PlayingLoopAnimation;
    float PlayingLoopRate = 1.f;
    float LastLadderHeight = 0.f;
    float LadderStillSeconds = 0.f;
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastAttack(int32 Variant);
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastWorkImpact(AActor* Target, FVector_NetQuantize Point, FVector_NetQuantizeNormal Normal, EEWWorkSurface Surface,
        const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal, uint8 SwingKind);
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequenceBase> LastSwingAnimation;
    int32 WorkImpactCount = 0;
    float ClimateClock = 0.f;
    /** The local screen's food-sickness queasiness, 0 to 1: the picture greys and greens and the colours fringe and sway while sick (owner, October 22: nausea). */
    float Nausea = 0.f;
    void UpdateNauseaLook(float DeltaSeconds);
    /** Every machine: a footstep each stride (wood on deck, sand, snow in the Winter region) or a stroke while swimming. */
    void UpdateFootsteps(float DeltaSeconds);
    /** The step for the ground under the survivor's feet. */
    EEWSound FootstepSurface() const;
    float StrideTravel = 0.f;
    /** The rustle of hands in the plants, heard by everyone near. */
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastGatherSound();
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastHitReact();
    void PlayOneShot(UAnimSequenceBase* Animation) const;
};

