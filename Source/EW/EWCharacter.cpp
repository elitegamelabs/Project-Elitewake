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
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"

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
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanSwim = true;
	GetCharacterMovement()->MaxSwimSpeed = 450.f;
	// Above 1 a survivor floats with head and shoulders out of the water and drifts back up after a dive (tuning).
	GetCharacterMovement()->Buoyancy = 1.3f;

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
	GetCharacterMovement()->GetNavAgentPropertiesRef().bCanSwim = true;
	SetFirstPerson(false);
	ApplyMovementSpeed();
}

void AEWCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
    if (IsOnLadder())
    {
        if (IsLocallyControlled())
        {
            // Forward and back, or the Up and Down arrows, climb; the server is told only when that changes.
            const float Input = FMath::Abs(LadderArrowInput) > .5f ? LadderArrowInput : PendingLadderForward;
            const int8 Direction = Input > .5f ? 1 : Input < -.5f ? -1 : 0;
            if (Direction != SentLadderDirection) { ServerLadderClimb(Direction); SentLadderDirection = Direction; }
            PendingLadderForward = 0.f;
        }
        if (HasAuthority())
        {
            float Bottom, Top;
            Ladder.Ship->GetLadderSpan(Ladder.Index, Bottom, Top);
            Ladder.Height = FMath::Clamp(Ladder.Height + LadderDirection * AEWShip::LadderClimbSpeed * DeltaSeconds, Bottom, Top);
            if (LadderDirection > 0 && Ladder.Height >= Top) ReleaseLadder(true);
            else if (LadderDirection < 0 && Ladder.Height <= Bottom) ReleaseLadder(false);
        }
        ApplyLadderPose();
    }
    if (IsLocallyControlled() && IsValid(HelmShip))
    {
        // Send helm controls only when they change. The ship holds them until the next change,
        // so slow frames or a lost frame of input never stop it.
        // With the sprint key held, left and right swing the sails; otherwise they put the rudder over.
        const bool bTrim = bHelmTrimHeld && HelmShip->HasTrimmableSails();
        const int8 Trim = !bTrim ? 0 : PendingHelmRight > .5f ? 1 : PendingHelmRight < -.5f ? -1 : 0;
        if (Trim != SentSailTrim) { ServerSailTrim(Trim); SentSailTrim = Trim; }
        const float NewRudder = bTrim ? 0.f : FMath::Clamp(PendingHelmRight, -1.f, 1.f);
        if (!FMath::IsNearlyEqual(NewRudder, SentHelmRudder, .05f) || (NewRudder == 0.f && SentHelmRudder != 0.f))
        {
            ServerHelmRudder(NewRudder);
            SentHelmRudder = NewRudder;
        }
        const int8 ForwardSign = PendingHelmForward > .5f ? 1 : PendingHelmForward < -.5f ? -1 : 0;
        if (ForwardSign != 0 && ForwardSign != LastHelmForwardSign) ServerSailStep(ForwardSign);
        LastHelmForwardSign = ForwardSign;
        PendingHelmRight = PendingHelmForward = 0.f;
    }
	if (GetCharacterMovement()->IsSwimming())
	{
		CancelRestrictedActions();
		// Rising only while fully under: at the surface, buoyancy holds the survivor and Space must not launch them out.
		if (IsLocallyControlled() && bSwimAscendInputHeld && GetCharacterMovement()->ImmersionDepth() >= .99f)
			AddMovementInput(FVector::UpVector);
	}

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

bool AEWCharacter::IsSwimming() const
{
	return GetCharacterMovement() && GetCharacterMovement()->IsSwimming();
}

void AEWCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(AEWCharacter, bIsSprinting);
	DOREPLIFETIME(AEWCharacter, bIsProne);
    DOREPLIFETIME(AEWCharacter, HelmShip);
    DOREPLIFETIME(AEWCharacter, Ladder);
}

void AEWCharacter::SetHelmShip(AEWShip* Ship)
{
    if (!HasAuthority()) return;
    HelmShip = Ship;
    OnRep_HelmShip();
    ForceNetUpdate();
}

void AEWCharacter::OnRep_HelmShip()
{
    CancelRestrictedActions();
    bSwimAscendInputHeld = false;
    StopJumping();
    PendingHelmRight = PendingHelmForward = SentHelmRudder = 0.f;
    LastHelmForwardSign = SentSailTrim = 0;
    bHelmTrimHeld = false;
    GetCharacterMovement()->StopMovementImmediately();
    if (IsValid(HelmShip))
    {
        // The helmsman rides the ship at the wheel; the ship owns all motion while they steer.
        GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        AttachToActor(HelmShip, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        SetActorRelativeLocation(HelmShip->GetHelmSeatLocal(GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
        SetActorRelativeRotation(FRotator::ZeroRotator);
    }
    else
    {
        DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    }
    SetHelmCamera(IsValid(HelmShip));
}

void AEWCharacter::SetHelmCamera(bool bAtHelm)
{
    if (!CameraBoom) return;
    if (bAtHelm)
    {
        if (SavedArmLength < 0.f)
        {
            SavedArmLength = CameraBoom->TargetArmLength;
            SavedTargetOffset = CameraBoom->TargetOffset;
            bSavedCameraCollision = CameraBoom->bDoCollisionTest;
        }
        // Back and up by the ship's size, clear of its own rails and rigging (tuning).
        const float Length = HelmShip->Definition ? HelmShip->Definition->HullExtent.X : 400.f;
        CameraBoom->TargetArmLength = FMath::Clamp(Length * 1.6f, 600.f, 2400.f);
        CameraBoom->TargetOffset = FVector(0, 0, FMath::Clamp(Length * .45f, 150.f, 700.f));
        CameraBoom->bDoCollisionTest = false;
    }
    else if (SavedArmLength >= 0.f)
    {
        CameraBoom->TargetArmLength = SavedArmLength;
        CameraBoom->TargetOffset = SavedTargetOffset;
        CameraBoom->bDoCollisionTest = bSavedCameraCollision;
        SavedArmLength = -1.f;
    }
}

void AEWCharacter::SetLadder(AEWShip* Ship, int32 BoardingIndex, float Height)
{
    if (!HasAuthority()) return;
    Ladder.Ship = Ship;
    Ladder.Index = BoardingIndex;
    Ladder.Height = Height;
    LadderDirection = 0;
    OnRep_Ladder();
    ForceNetUpdate();
}

void AEWCharacter::OnRep_Ladder()
{
    if (IsOnLadder() && !bAttachedToLadder)
    {
        // The climber rides the ship on its ladder; climbing, not walking, moves them.
        CancelRestrictedActions();
        bSwimAscendInputHeld = false;
        StopJumping();
        GetCharacterMovement()->StopMovementImmediately();
        GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        AttachToActor(Ladder.Ship, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        bAttachedToLadder = true;
        SentLadderDirection = 0;
    }
    else if (!IsOnLadder() && bAttachedToLadder)
    {
        DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
        bAttachedToLadder = false;
    }
    ApplyLadderPose();
}

void AEWCharacter::ApplyLadderPose()
{
    if (!IsOnLadder() || !bAttachedToLadder) return;
    const FTransform Pose = Ladder.Ship->GetLadderPoseLocal(Ladder.Index, Ladder.Height, GetCapsuleComponent()->GetScaledCapsuleRadius());
    SetActorRelativeLocation(Pose.GetLocation());
    SetActorRelativeRotation(Pose.Rotator());
}

void AEWCharacter::ServerLadderClimb_Implementation(int8 Direction)
{
    LadderDirection = FMath::Clamp<int8>(Direction, -1, 1);
}

void AEWCharacter::ServerLetGoOfLadder_Implementation()
{
    if (IsOnLadder()) ReleaseLadder(false);
}

void AEWCharacter::ReleaseLadder(bool bOntoDeck)
{
    if (!HasAuthority() || !IsOnLadder()) return;
    AEWShip* Ship = Ladder.Ship;
    const int32 Index = Ladder.Index;
    Ladder = FEWLadderHold();
    LadderDirection = 0;
    OnRep_Ladder();
    // At the head of the ladder, step inboard onto the deck; if that spot is taken, hang on at the top.
    if (bOntoDeck && !Ship->ClimbAboard(this, Index))
    {
        float Bottom, Top;
        Ship->GetLadderSpan(Index, Bottom, Top);
        SetLadder(Ship, Index, Top);
        return;
    }
    ForceNetUpdate();
}

void AEWCharacter::ServerHelmRudder_Implementation(float NewRudder)
{
    if (IsValid(HelmShip)) HelmShip->SetRudder(this, NewRudder);
}

void AEWCharacter::ServerSailTrim_Implementation(int8 Direction)
{
    if (IsValid(HelmShip)) HelmShip->SetSailTrim(this, Direction);
}

void AEWCharacter::ServerSailStep_Implementation(int8 Direction)
{
    if (IsValid(HelmShip)) HelmShip->StepSails(this, Direction);
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
    if (HelmShip) { bHelmTrimHeld = true; return; }
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
    bHelmTrimHeld = false;
	bSprintInputHeld = false;
	SetSprinting(false);
}

void AEWCharacter::StartStanceInput()
{
    if (HelmShip) return;
	if (GetCharacterMovement()->IsSwimming()) return;
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
		&& !GetCharacterMovement()->IsSwimming()
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
	if (GetCharacterMovement()->IsSwimming()) return EEWLocomotionState::Swimming;
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
    if (IsOnLadder())
    {
        PendingLadderForward = Forward;
        return;
    }
    if (HelmShip)
    {
        PendingHelmRight = Right;
        PendingHelmForward = Forward;
        return;
    }
	if (GetController() != nullptr)
	{
		// find out which way is forward
		const FRotator Rotation = GetController()->GetControlRotation();
		const FRotator YawRotation(0, Rotation.Yaw, 0);

		// get forward vector. Swimmers follow the camera's pitch only when it clearly looks up or down (tuning),
		// so the usual slightly lowered camera swims level instead of diving.
		const bool bDiveOrClimb = GetCharacterMovement()->IsSwimming() && FMath::Abs(FRotator::NormalizeAxis(Rotation.Pitch)) > 25.f;
		const FVector ForwardDirection = FRotationMatrix(bDiveOrClimb ? Rotation : YawRotation).GetUnitAxis(EAxis::X);

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
    if (HelmShip) return;
    // Space lets go of a ladder.
    if (IsOnLadder()) { ServerLetGoOfLadder(); return; }
	bSwimAscendInputHeld = true;
	if (GetCharacterMovement()->IsSwimming()) return;
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
	bSwimAscendInputHeld = false;
	// signal the character to stop jumping
	StopJumping();
}

bool AEWCharacter::CanAttack() const
{
    return SurvivalComponent && SurvivalComponent->GetHealth() > 0.f && !bIsProne && !HelmShip && !IsOnLadder() && !IsSwimming();
}

void AEWCharacter::PlayOneShot(UAnimSequenceBase* Animation) const
{
    if (!Animation || !GetMesh()) return;
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
        Anim->PlaySlotAnimationAsDynamicMontage(Animation, TEXT("DefaultSlot"), .1f, .15f);
}

void AEWCharacter::PlayAttackAnimation(int32 Variant)
{
    if (AttackAnimations.Num()) PlayOneShot(AttackAnimations[FMath::Abs(Variant) % AttackAnimations.Num()]);
}

void AEWCharacter::BroadcastAttack(int32 Variant)
{
    if (HasAuthority()) MulticastAttack(Variant);
}

void AEWCharacter::MulticastAttack_Implementation(int32 Variant)
{
    // The owner already swung the moment the button went down.
    if (!IsLocallyControlled()) PlayAttackAnimation(Variant);
}

void AEWCharacter::MulticastHitReact_Implementation()
{
    PlayOneShot(HitReactAnimation);
}

AEWCharacter* AEWCharacter::MeleeStrike()
{
    if (!HasAuthority() || !CanAttack() || !GetWorld()) return nullptr;
    FVector Eye; FRotator View;
    GetActorEyesViewPoint(Eye, View);
    // From the chest along where the survivor looks; the first thing in the way takes the blow, so walls shield.
    const FVector From = GetActorLocation() + FVector(0, 0, BaseEyeHeight * .5f);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWMelee), false, this);
    FHitResult Hit;
    if (!GetWorld()->SweepSingleByChannel(Hit, From, From + View.Vector() * MeleeReach, FQuat::Identity, ECC_Pawn,
            FCollisionShape::MakeSphere(MeleeRadius), Query)) return nullptr;
    auto* Victim = Cast<AEWCharacter>(Hit.GetActor());
    if (!Victim || !Victim->SurvivalComponent || Victim->SurvivalComponent->GetHealth() <= 0.f) return nullptr;
    Victim->SurvivalComponent->ApplyDamage(FistDamage);
    Victim->MulticastHitReact();
    return Victim;
}
