// Copyright Epic Games, Inc. All Rights Reserved.

#include "EWCharacter.h"
#include "EWCharacterMovementComponent.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWSurvivalComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/Controller.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputActionValue.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include "EW.h"
#include "EWPlayerController.h"

AEWCharacter::AEWCharacter(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer.SetDefaultSubobjectClass<UEWCharacterMovementComponent>(ACharacter::CharacterMovementComponentName))
{
	PrimaryActorTick.bCanEverTick = true;
	SurvivalComponent = CreateDefaultSubobject<UEWSurvivalComponent>(TEXT("SurvivalComponent"));
	InventoryComponent = CreateDefaultSubobject<UEWInventoryComponent>(TEXT("InventoryComponent"));
    EquipmentComponent = CreateDefaultSubobject<UEWEquipmentComponent>(TEXT("EquipmentComponent"));
    HotbarComponent = CreateDefaultSubobject<UEWHotbarComponent>(TEXT("HotbarComponent"));

	// Set size for collision capsule
	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.0f);
		
	// Don't rotate when the controller rotates. Let that just affect the camera.
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	// Configure character movement
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.0f, 500.0f, 0.0f);
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;

	// Note: For faster iteration times these variables, and many more, can be tweaked in the Character Blueprint
	// instead of recompiling to adjust them
	GetCharacterMovement()->JumpZVelocity = 500.f;
	GetCharacterMovement()->AirControl = 0.35f;
	GetCharacterMovement()->MaxWalkSpeed = WalkingSpeed;
	GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
	GetCharacterMovement()->MinAnalogWalkSpeed = 20.f;
	GetCharacterMovement()->BrakingDecelerationWalking = 2000.f;
	GetCharacterMovement()->BrakingDecelerationFalling = 1500.0f;

	// Create a camera boom (pulls in towards the player if there is a collision)
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 400.0f;
	CameraBoom->bUsePawnControlRotation = true;

	// Create a follow camera
	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	// Keep first-person presentation separate from the third-person boom.
	FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
	FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
	FirstPersonCamera->SetRelativeLocation(FVector(10.0f, 0.0f, 64.0f));
	FirstPersonCamera->bUsePawnControlRotation = true;
	FirstPersonCamera->SetActive(false);

	// Note: The skeletal mesh and anim blueprint references on the Mesh component (inherited from Character) 
	// are set in the derived blueprint asset named ThirdPersonCharacter (to avoid direct content references in C++)
}

void AEWCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	// Set up action bindings
	if (UEnhancedInputComponent* EnhancedInputComponent = Cast<UEnhancedInputComponent>(PlayerInputComponent)) {
		
		// Jumping
		EnhancedInputComponent->BindAction(JumpAction, ETriggerEvent::Started, this, &AEWCharacter::DoJumpStart);
		EnhancedInputComponent->BindAction(JumpAction, ETriggerEvent::Completed, this, &AEWCharacter::DoJumpEnd);

		// Moving
		EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AEWCharacter::Move);
		EnhancedInputComponent->BindAction(MouseLookAction, ETriggerEvent::Triggered, this, &AEWCharacter::Look);

		// Looking
		EnhancedInputComponent->BindAction(LookAction, ETriggerEvent::Triggered, this, &AEWCharacter::Look);

		// Sprinting
		if (SprintAction)
		{
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Started, this, &AEWCharacter::StartSprint);
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Completed, this, &AEWCharacter::StopSprint);
			EnhancedInputComponent->BindAction(SprintAction, ETriggerEvent::Canceled, this, &AEWCharacter::StopSprint);
		}

		// Crouching and prone
		if (StanceAction)
		{
			EnhancedInputComponent->BindAction(StanceAction, ETriggerEvent::Started, this, &AEWCharacter::StartStanceInput);
			EnhancedInputComponent->BindAction(StanceAction, ETriggerEvent::Completed, this, &AEWCharacter::StopStanceInput);
			EnhancedInputComponent->BindAction(StanceAction, ETriggerEvent::Canceled, this, &AEWCharacter::CancelStanceInput);
		}

		// Perspective switching
		if (TogglePerspectiveAction)
		{
			EnhancedInputComponent->BindAction(TogglePerspectiveAction, ETriggerEvent::Started, this, &AEWCharacter::TogglePerspective);
		}
	}
	else
	{
		UE_LOG(LogEW, Error, TEXT("'%s' Failed to find an Enhanced Input component! This template is built to use the Enhanced Input system. If you intend to use the legacy system, then you will need to update this C++ file."), *GetNameSafe(this));
	}
}

void AEWCharacter::BeginPlay()
{
	Super::BeginPlay();

	// Older Blueprint defaults can retain the template's non-crouching navigation flag.
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;
	SetFirstPerson(false);
	ApplyMovementSpeed();
}

void AEWCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (HasAuthority() && SurvivalComponent)
	{
		SurvivalComponent->UpdateStamina(bIsSprinting, DeltaSeconds);

		if (bIsSprinting && !SurvivalComponent->CanSprint())
		{
			SetSprinting(false);
		}
	}

#if !UE_BUILD_SHIPPING
	if (bShowMovementDebug && IsLocallyControlled() && GEngine)
	{
		const UEnum* LocomotionEnum = StaticEnum<EEWLocomotionState>();
		const FString StateName = LocomotionEnum
			? LocomotionEnum->GetDisplayNameTextByValue(static_cast<int64>(GetLocomotionState())).ToString()
			: TEXT("Unknown");
		const FString PerspectiveName = bIsFirstPerson ? TEXT("First Person") : TEXT("Third Person");
		const FString DebugText = FString::Printf(
			TEXT("Perspective: %s  |  Movement State: %s  |  Stamina: %.0f / %.0f"),
			*PerspectiveName,
			*StateName,
			SurvivalComponent ? SurvivalComponent->GetStamina() : 0.0f,
			SurvivalComponent ? SurvivalComponent->GetMaxStamina() : 0.0f);

		GEngine->AddOnScreenDebugMessage(
			static_cast<int32>(GetUniqueID()),
			0.0f,
			FColor::Cyan,
			DebugText);
	}
#endif
}

void AEWCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(AEWCharacter, bIsSprinting);
	DOREPLIFETIME(AEWCharacter, bIsProne);
}

void AEWCharacter::OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	ApplyMovementSpeed();
}

void AEWCharacter::OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
	Super::OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
	if (bSprintInputHeld && (IsLocallyControlled() || HasAuthority())) SetSprinting(true);
	ApplyMovementSpeed();
}

void AEWCharacter::Move(const FInputActionValue& Value)
{
	// input is a Vector2D
	FVector2D MovementVector = Value.Get<FVector2D>();

	// route the input
	DoMove(MovementVector.X, MovementVector.Y);
}

void AEWCharacter::Look(const FInputActionValue& Value)
{
	// input is a Vector2D
	FVector2D LookAxisVector = Value.Get<FVector2D>();

	// route the input
	DoLook(LookAxisVector.X, LookAxisVector.Y);
}

void AEWCharacter::StartSprint()
{
    if (const auto* PC = Cast<AEWPlayerController>(GetController()); PC && (PC->IsMapOpen() || PC->IsSessionMenuOpen())) return;
	bSprintInputHeld = true;
	if (bIsProne)
	{
		SetProne(false);
	}

	if (bIsCrouched)
	{
		UnCrouch();
	}

	SetSprinting(true);
}

void AEWCharacter::StopSprint()
{
	bSprintInputHeld = false;
	SetSprinting(false);
}

void AEWCharacter::StartStanceInput()
{
    if (const auto* PC = Cast<AEWPlayerController>(GetController()); PC && (PC->IsMapOpen() || PC->IsSessionMenuOpen())) return;
	bStanceInputHeld = true;
	bSprintInputHeld = false;
	SetSprinting(false);

	GetWorldTimerManager().SetTimer(
		StanceHoldTimer,
		this,
		&AEWCharacter::HandleProneHold,
		StanceHoldDuration,
		false);
}

void AEWCharacter::StopStanceInput()
{
	bStanceInputHeld = false;

	if (GetWorldTimerManager().IsTimerActive(StanceHoldTimer))
	{
		GetWorldTimerManager().ClearTimer(StanceHoldTimer);
		ToggleCrouch();
	}
}

void AEWCharacter::CancelStanceInput()
{
	bStanceInputHeld = false;
	GetWorldTimerManager().ClearTimer(StanceHoldTimer);
}

void AEWCharacter::TogglePerspective()
{
	SetFirstPerson(!bIsFirstPerson);
}

void AEWCharacter::SetFirstPerson(bool bNewFirstPerson)
{
	bIsFirstPerson = bNewFirstPerson;

	FirstPersonCamera->SetActive(bIsFirstPerson);
	FollowCamera->SetActive(!bIsFirstPerson);
	GetMesh()->SetOwnerNoSee(bIsFirstPerson);
}

void AEWCharacter::HandleProneHold()
{
	if (bStanceInputHeld)
	{
		SetProne(true);
	}
}

void AEWCharacter::ToggleCrouch()
{
	if (bIsProne)
	{
		SetProne(false);
		Crouch();
	}
	else if (bIsCrouched)
	{
		UnCrouch();
	}
	else
	{
		Crouch();
	}
}

void AEWCharacter::SetSprinting(bool bNewIsSprinting)
{
	const auto* PC = Cast<AEWPlayerController>(GetController());
	bNewIsSprinting = bNewIsSprinting && (!PC || (!PC->IsMapOpen() && !PC->IsSessionMenuOpen()))
		&& !bIsProne
		&& !bIsCrouched
		&& (!SurvivalComponent || SurvivalComponent->CanSprint());

	if (bIsSprinting == bNewIsSprinting)
	{
		return;
	}

	bIsSprinting = bNewIsSprinting;
	ApplyMovementSpeed();

	if (!HasAuthority())
	{
		ServerSetSprinting(bNewIsSprinting);
	}
}

void AEWCharacter::SetProne(bool bNewIsProne)
{
	UEWCharacterMovementComponent* Movement = CastChecked<UEWCharacterMovementComponent>(GetCharacterMovement());
	Movement->bWantsToProne = bNewIsProne;
	if (bNewIsProne)
	{
		SetSprinting(false);
		Crouch();
	}
}

void AEWCharacter::SetProneFromMovement(bool bNewIsProne)
{
	bIsProne = bNewIsProne;
	ApplyMovementSpeed();
}

void AEWCharacter::ServerSetSprinting_Implementation(bool bNewIsSprinting)
{
	SetSprinting(bNewIsSprinting);
}

void AEWCharacter::OnRep_IsSprinting()
{
	ApplyMovementSpeed();
}

void AEWCharacter::OnRep_IsProne()
{
	CastChecked<UEWCharacterMovementComponent>(GetCharacterMovement())->RefreshProxyStance();
	ApplyMovementSpeed();
}

void AEWCharacter::ApplyMovementSpeed()
{
	float TargetSpeed = WalkingSpeed;

	if (bIsProne)
	{
		TargetSpeed = ProneSpeed;
	}
	else if (bIsCrouched)
	{
		TargetSpeed = CrouchSpeed;
	}
	else if (bIsSprinting)
	{
		TargetSpeed = SprintSpeed;
	}

	GetCharacterMovement()->MaxWalkSpeed = TargetSpeed;
	GetCharacterMovement()->MaxWalkSpeedCrouched = bIsProne ? ProneSpeed : CrouchSpeed;
	const float CapsuleHalfHeight = GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	const float EyeHeight = bIsProne ? 40.f : (bIsCrouched ? 96.f : CapsuleHalfHeight + 64.f);
	FirstPersonCamera->SetRelativeLocation(FVector(10.f, 0.f, EyeHeight - CapsuleHalfHeight));
}

EEWLocomotionState AEWCharacter::GetLocomotionState() const
{
	if (bIsProne)
	{
		return EEWLocomotionState::Prone;
	}

	if (bIsCrouched)
	{
		return EEWLocomotionState::Crouching;
	}

	if (GetCharacterMovement()->IsFalling())
	{
		return EEWLocomotionState::Airborne;
	}

	if (GetVelocity().SizeSquared2D() > 1.0f)
	{
		return bIsSprinting ? EEWLocomotionState::Sprinting : EEWLocomotionState::Walking;
	}

	return EEWLocomotionState::Standing;
}

void AEWCharacter::DoMove(float Right, float Forward)
{
	if (GetController() != nullptr)
	{
		// find out which way is forward
		const FRotator Rotation = GetController()->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);

		// get forward vector
		const FVector ForwardDirection = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);

		// get right vector 
		const FVector RightDirection = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);

		// add movement 
		AddMovementInput(ForwardDirection, Forward);
		AddMovementInput(RightDirection, Right);
	}
}

void AEWCharacter::DoLook(float Yaw, float Pitch)
{
	if (GetController() != nullptr)
	{
		// add yaw and pitch input to controller
		AddControllerYawInput(Yaw);
		AddControllerPitchInput(Pitch);
	}
}

void AEWCharacter::DoJumpStart()
{
	if (bIsProne)
	{
		SetProne(false);
	}

	if (bIsCrouched)
	{
		UnCrouch();
		// Resolve clearance before Character checks this frame's jump. A deferred
		// uncrouch would otherwise consume a one-frame jump press while still low.
		CastChecked<UEWCharacterMovementComponent>(GetCharacterMovement())->UnCrouch();
	}

	// signal the character to jump
	Jump();
}

void AEWCharacter::DoJumpEnd()
{
	// signal the character to stop jumping
	StopJumping();
}
