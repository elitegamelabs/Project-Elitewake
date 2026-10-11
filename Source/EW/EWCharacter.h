// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Logging/LogMacros.h"
#include "TimerManager.h"
#include "EWCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UInputAction;
class UEWSurvivalComponent;
class UEWInventoryComponent;
class UEWEquipmentComponent;
class UEWHotbarComponent;
struct FInputActionValue;
class FLifetimeProperty;

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

	/** Dedicated local first-person camera. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta = (AllowPrivateAccess = "true"))
	UCameraComponent* FirstPersonCamera;

	/** Server-authoritative survival values for this character. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	UEWSurvivalComponent* SurvivalComponent;

	/** Server-authoritative item stacks and carried weight. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
	UEWInventoryComponent* InventoryComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
    UEWEquipmentComponent* EquipmentComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components", meta=(AllowPrivateAccess="true"))
    UEWHotbarComponent* HotbarComponent;
	
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
    /** Local swim ascent intent; movement acceleration uses the standard saved-move path. */
    bool bSwimAscendInputHeld = false;

	/** Whether the locally controlled player is using the first-person camera. */
	UPROPERTY(BlueprintReadOnly, Category="Camera", meta=(AllowPrivateAccess="true"))
	bool bIsFirstPerson = false;

	/** Show temporary movement-state text while the locomotion foundation is validated. */
	UPROPERTY(EditDefaultsOnly, Category="Debug")
	bool bShowMovementDebug = true;

	/** Delays prone entry so a quick press remains a crouch toggle. */
	FTimerHandle StanceHoldTimer;

public:
    void CancelRestrictedActions() { StopSprint(); CancelStanceInput(); }

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

	/** Returns whether the local player is using first person. */
	UFUNCTION(BlueprintPure, Category="Camera")
	bool IsFirstPerson() const { return bIsFirstPerson; }

	/** Returns the high-level state used by animation and presentation systems. */
	UFUNCTION(BlueprintPure, Category="Movement|Animation")
	EEWLocomotionState GetLocomotionState() const;

public:

	/** Returns CameraBoom subobject **/
	FORCEINLINE class USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	/** Returns FollowCamera subobject **/
	FORCEINLINE class UCameraComponent* GetFollowCamera() const { return FollowCamera; }

	/** Returns FirstPersonCamera subobject **/
	FORCEINLINE class UCameraComponent* GetFirstPersonCamera() const { return FirstPersonCamera; }

	/** Returns the survival-stat component. */
	UFUNCTION(BlueprintPure, Category="Survival")
	UEWSurvivalComponent* GetSurvivalComponent() const { return SurvivalComponent; }

	/** Returns the character inventory component. */
	UFUNCTION(BlueprintPure, Category="Inventory")
	UEWInventoryComponent* GetInventoryComponent() const { return InventoryComponent; }
    UFUNCTION(BlueprintPure, Category="Equipment")
    UEWEquipmentComponent* GetEquipmentComponent() const { return EquipmentComponent; }
    UFUNCTION(BlueprintPure, Category="Hotbar")
    UEWHotbarComponent* GetHotbarComponent() const { return HotbarComponent; }
};

