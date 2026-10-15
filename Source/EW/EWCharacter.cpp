// Copyright Epic Games, Inc. All Rights Reserved.

#include "EWCharacter.h"
#include "AnimationRuntime.h"
#include "EWCharacterMovementComponent.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWSurvivalComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "EWItemDefinition.h"
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
#include "Wildlife/EWFish.h"
#include "Wildlife/EWAnimal.h"
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
    BodyRoster = TSoftObjectPtr<UEWBodyRoster>(FSoftObjectPath(TEXT("/Game/Elitewake/Characters/DA_BodyRoster.DA_BodyRoster")));
    HeldItem = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeldItem"));
    HeldItem->SetupAttachment(GetMesh(), TEXT("hand_r"));
    HeldItem->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    HeldItem->SetGenerateOverlapEvents(false);
    HeldLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("HeldLight"));
    HeldLight->SetupAttachment(HeldItem);
    HeldLight->SetLightColor(FLinearColor(1.f, .62f, .3f));
    HeldLight->SetAttenuationRadius(1200.f);
    HeldLight->SetCastShadows(false);
    HeldLight->SetVisibility(false);
	HeldFlame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeldFlame"));
	HeldFlame->SetupAttachment(HeldItem);
	HeldFlame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HeldFlame->SetCastShadow(false);
	HeldFlame->SetVisibility(false);

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
	// Your own arms and the ground at your feet are close enough that full motion blur smears them (tuning).
	FirstPersonCamera->PostProcessSettings.bOverride_MotionBlurAmount = true;
	FirstPersonCamera->PostProcessSettings.MotionBlurAmount = .15f;

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
    EquipmentComponent->OnEquipmentChanged.AddUniqueDynamic(this, &AEWCharacter::RefreshHeldItem);
    RefreshHeldItem();
    OnRep_Appearance();
}

void AEWCharacter::SetAppearance(const FEWAppearance& NewAppearance)
{
    if (!HasAuthority()) return;
    Appearance = NewAppearance.Clamped(BodyRoster.LoadSynchronous());
    OnRep_Appearance();
    ForceNetUpdate();
}

void AEWCharacter::OnRep_Appearance()
{
    // Survivors who never chose keep the body their blueprint was made with.
    if (Appearance == FEWAppearance()) return;
    Appearance.ApplyTo(GetMesh(), BodyRoster.LoadSynchronous());
    // A new body brings its head back; hide it again from its own first-person camera.
    if (bIsFirstPerson) ShowFirstPersonBody();
}

void AEWCharacter::RefreshHeldItem()
{
    const UEWItemDefinition* Item = EquipmentComponent ? EquipmentComponent->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    if (IsValid(HelmShip))
        for (const FEWInstalledFitting& Fitting : HelmShip->GetInstalledFittings())
            if (Fitting.Item && Fitting.Item->FittingMountType == EEWShipMountType::Helm && !Fitting.Item->HeldMesh.IsNull())
                Item = Fitting.Item;
    UStaticMesh* Held = Item ? Item->HeldMesh.LoadSynchronous() : nullptr;
    HeldItem->SetStaticMesh(Held);
    HeldItem->SetVisibility(Held != nullptr);
    if (Held) HeldItem->SetRelativeTransform(Item->HeldMeshTransform);
    // A torch gives light only while it burns; it is lit with Left Mouse once in hand.
    const bool bLit = Held && Item->HeldLightIntensity > 0.f && bHeldItemLit;
    HeldLight->SetVisibility(bLit);
    UStaticMesh* Flame = bLit ? Item->HeldFlameMesh.LoadSynchronous() : nullptr;
    HeldFlame->SetStaticMesh(Flame);
    HeldFlame->SetVisibility(Flame != nullptr);
    if (bLit)
    {
        HeldLight->SetIntensityUnits(ELightUnits::Candelas);
        HeldLight->SetIntensity(Item->HeldLightIntensity);
        HeldLight->SetRelativeLocation(Item->HeldLightOffset);
        HeldFlame->SetRelativeLocation(Item->HeldLightOffset - FVector(0, 0, 6.f));
    }
    // Drawing a newly equipped item; a different item in hand puts out the old one's flame.
    if (Item != ShownHeldItem.Get())
    {
        // A skin filled or emptied in the hand is the same thing, not a new tool drawn.
        const UEWItemDefinition* Was = ShownHeldItem.Get();
        const bool bSameSkin = Was && Item && (Was->FilledVersion.Get() == Item || Was->EmptiedVersion.Get() == Item);
        if (Item && HasActorBegunPlay() && !bSameSkin) PlayToolAnimation(EquipAnimation);
        ShownHeldItem = Item;
        if (HasAuthority() && bHeldItemLit && !(Item && Item->HeldLightIntensity > 0.f)) bHeldItemLit = false;
    }
}

bool AEWCharacter::HasUsableHeldItem() const
{
    const UEWItemDefinition* Item = EquipmentComponent ? EquipmentComponent->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    return Item && (Item->HeldLightIntensity > 0.f || !Item->EmptiedVersion.IsNull() || !Item->FilledVersion.IsNull());
}

void AEWCharacter::ServerUseHeldItem_Implementation()
{
    UEWItemDefinition* Item = EquipmentComponent ? EquipmentComponent->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    if (!Item || !SurvivalComponent || SurvivalComponent->GetHealth() <= 0.f || IsValid(HelmShip) || IsValid(GunShip) || IsOnLadder()) return;
    if (Item->HeldLightIntensity > 0.f)
    {
        // Light the torch, or put it out.
        bHeldItemLit = !bHeldItemLit;
        RefreshHeldItem();
        ForceNetUpdate();
        if (bHeldItemLit) MulticastToolAnimation(IgniteAnimation);
        return;
    }
    if (UEWItemDefinition* Empty = Item->EmptiedVersion.LoadSynchronous())
    {
        // A full waterskin is drunk dry: it quenches as drinking at fresh water does (its capacity is open).
        if (EquipmentComponent->ChangeEquippedState(EEWEquipmentSlot::MainHand, Empty))
        {
            SurvivalComponent->SetHydration(100.f);
            ForceNetUpdate();
            MulticastToolAnimation(DrinkAnimation);
        }
    }
}

bool AEWCharacter::FillHeldWaterskin()
{
    UEWItemDefinition* Item = EquipmentComponent ? EquipmentComponent->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    UEWItemDefinition* Full = Item ? Item->FilledVersion.LoadSynchronous() : nullptr;
    if (!HasAuthority() || !Full || !EquipmentComponent->ChangeEquippedState(EEWEquipmentSlot::MainHand, Full)) return false;
    MulticastToolAnimation(FillAnimation);
    return true;
}

void AEWCharacter::MulticastToolAnimation_Implementation(UAnimSequenceBase* Animation)
{
    PlayToolAnimation(Animation);
}

void AEWCharacter::PlayToolAnimation(UAnimSequenceBase* Animation)
{
    if (!Animation) return;
    LastToolAnimation = Animation;
    PlayOneShot(Animation);
}

void AEWCharacter::UpdateLoopAnimation(float DeltaSeconds)
{
    UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
    if (!Anim) return;
    UAnimSequenceBase* Wanted = nullptr;
    float Rate = 1.f;
    if (IsValid(HelmShip) && HelmShip->Definition)
    {
        // Paddlers stroke at their stroke's pace and rest with the paddle in hand; a helmsman holds the wheel.
        if (HelmShip->Definition->bPaddled)
        {
            const EEWSailState Stroke = HelmShip->GetSailState();
            Wanted = Stroke == EEWSailState::Furled ? nullptr : PaddleAnimation.Get();
            Rate = Stroke == EEWSailState::Full ? 1.25f : .8f;
        }
        else Wanted = HelmHoldAnimation;
    }
    else if (IsOnLadder())
    {
        // Judged from the height itself, which every machine has, so watchers see the same climb.
        const float Moved = Ladder.Height - LastLadderHeight;
        LastLadderHeight = Ladder.Height;
        LadderStillSeconds = FMath::Abs(Moved) > KINDA_SMALL_NUMBER ? 0.f : LadderStillSeconds + DeltaSeconds;
        Wanted = LadderStillSeconds > .15f ? LadderIdleAnimation.Get()
            : Moved > 0.f ? LadderUpAnimation.Get() : Moved < 0.f ? LadderDownAnimation.Get() : PlayingLoopAnimation.Get();
        if (!Wanted) Wanted = LadderIdleAnimation;
    }
    else if (CapstanShip.IsValid() && CapstanShip->GetCapstanWorker() == this) Wanted = CapstanAnimation;
    else if (IsValid(GunShip)) Wanted = HelmHoldAnimation;   // hands on the cannon (stand-in until a gunner's pose)
    if (Wanted == PlayingLoopAnimation && Rate == PlayingLoopRate) return;
    if (PlayingLoopAnimation) Anim->StopSlotAnimation(.15f, TEXT("DefaultSlot"));
    PlayingLoopAnimation = Wanted;
    PlayingLoopRate = Rate;
    if (Wanted) Anim->PlaySlotAnimationAsDynamicMontage(Wanted, TEXT("DefaultSlot"), .2f, .2f, Rate, 100000);
}

void AEWCharacter::SetCapstanShip(AEWShip* Ship)
{
    CapstanShip = Ship;
}

UStaticMesh* AEWCharacter::GetHeldMesh() const
{
    return HeldItem ? HeldItem->GetStaticMesh() : nullptr;
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
    UpdateLoopAnimation(DeltaSeconds);
    ApplyFacing();
    if (HeldLight->IsVisible())
    {
        // A flame's light wavers: two slow waves and a quicker one, never below most of its strength.
        FlickerTime += DeltaSeconds;
        const UEWItemDefinition* Lit = EquipmentComponent ? EquipmentComponent->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
        const float Base = Lit ? Lit->HeldLightIntensity : HeldLight->Intensity;
        const float Waver = .08f * FMath::Sin(FlickerTime * 7.3f) + .06f * FMath::Sin(FlickerTime * 13.1f + 1.7f) + .04f * FMath::Sin(FlickerTime * 23.f);
        HeldLight->SetIntensity(Base * (.9f + Waver));
    }
    if (bIsFirstPerson && IsLocallyControlled()) UpdateFirstPersonCamera(DeltaSeconds);
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
    if (IsLocallyControlled() && IsValid(GunShip))
    {
        // The view aims the cannon: its direction relative to the gun's rest, sent when it changes.
        FTransform Frame = FTransform(GunShip->GetGunnerSeatLocal(GunMount, 0.f).GetRotation()) * GunShip->GetActorTransform();
        const FRotator Local = Frame.InverseTransformRotation(GetControlRotation().Quaternion()).Rotator();
        const FRotator Aim(FMath::Clamp(Local.Pitch, -AEWShip::CannonDepression, AEWShip::CannonElevation),
                           FMath::Clamp(Local.Yaw, -AEWShip::CannonTraverse, AEWShip::CannonTraverse), 0.f);
        const double Now = GetWorld()->GetTimeSeconds();
        if (!Aim.Equals(SentCannonAim, .25f) && Now - SentCannonAimAt > .05)
        {
            ServerCannonAim(Aim.Yaw, Aim.Pitch);
            SentCannonAim = Aim;
            SentCannonAimAt = Now;
        }
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
    DOREPLIFETIME(AEWCharacter, GunShip);
    DOREPLIFETIME(AEWCharacter, GunMount);
    DOREPLIFETIME(AEWCharacter, bHeldItemLit);
    DOREPLIFETIME(AEWCharacter, CarriedFish);
    DOREPLIFETIME(AEWCharacter, Ladder);
    DOREPLIFETIME(AEWCharacter, Appearance);
    DOREPLIFETIME_CONDITION(AEWCharacter, bFacingView, COND_SkipOwner);
}

void AEWCharacter::SetHelmShip(AEWShip* Ship)
{
    if (!HasAuthority()) return;
    HelmShip = Ship;
    OnRep_HelmShip();
    ForceNetUpdate();
}

void AEWCharacter::SetGunPost(AEWShip* Ship, FName MountId)
{
    if (!HasAuthority()) return;
    GunMount = MountId;
    GunShip = Ship;
    OnRep_GunPost();
    ForceNetUpdate();
}

void AEWCharacter::OnRep_GunPost()
{
    CancelRestrictedActions();
    bSwimAscendInputHeld = false;
    StopJumping();
    SentCannonAim = FRotator(1000.f, 0.f, 0.f);
    GetCharacterMovement()->StopMovementImmediately();
    if (IsValid(GunShip))
    {
        // The gunner stands behind the carriage and rides the ship while they man the cannon.
        GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        AttachToActor(GunShip, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        const FTransform Seat = GunShip->GetGunnerSeatLocal(GunMount, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
        SetActorRelativeLocation(Seat.GetLocation());
        SetActorRelativeRotation(Seat.GetRotation());
        if (IsLocallyControlled() && GetController())
            GetController()->SetControlRotation(FRotator(0.f, GetActorRotation().Yaw, 0.f));
    }
    else if (GetAttachParentActor() && !IsValid(HelmShip))
    {
        DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    }
}

void AEWCharacter::ServerCannonAim_Implementation(float Yaw, float Pitch)
{
    if (IsValid(GunShip)) GunShip->AimCannon(this, Yaw, Pitch);
}

void AEWCharacter::ServerFireCannon_Implementation()
{
    if (IsValid(GunShip)) GunShip->FireCannon(this);
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
    RefreshHeldItem();
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
	// The body stays in view: looking down shows the survivor's own arms, legs and feet. Only the head is hidden,
	// and only here, since every other screen draws this survivor from its own copy.
	ShowFirstPersonBody();
	if (IsLocallyControlled() && bFacingView != bIsFirstPerson)
	{
		bFacingView = bIsFirstPerson;
		if (!HasAuthority()) ServerSetFacingView(bFacingView);
	}
	ApplyFacing();
}

void AEWCharacter::ServerSetFacingView_Implementation(bool bFace)
{
	bFacingView = bFace;
	ApplyFacing();
}

void AEWCharacter::ShowFirstPersonBody()
{
	// Hidden from the base of the neck, so the collar closes over it rather than leaving the inside of the neck to
	// be seen when looking straight down.
	static const FName Neck(TEXT("neck_01"));
	USkeletalMeshComponent* Body = GetMesh();
	if (!Body) return;
	Body->SetOwnerNoSee(false);
	const bool bHide = bIsFirstPerson && IsLocallyControlled();
	if (Body->GetBoneIndex(Neck) == INDEX_NONE) return;
	if (bHide && !Body->IsBoneHiddenByName(Neck)) Body->HideBoneByName(Neck, PBO_None);
	else if (!bHide && Body->IsBoneHiddenByName(Neck)) Body->UnHideBoneByName(Neck);
	if (bHide) UpdateFirstPersonCamera(0.f);
}

void AEWCharacter::UpdateFirstPersonCamera(float DeltaSeconds)
{
	// The head is hidden, and a hidden bone's place is no longer updated, so the eyes are carried by the torso: up
	// the line from the hips to the upper chest as far as they sit along it in the rest pose, and ahead of it. That
	// line leans when crouching and lies flat when prone, but hardly moves when a swing twists the chest, so the
	// view stays steady.
	static const FName Hips(TEXT("pelvis")), Chest(TEXT("spine_05")), Head(TEXT("head"));
	USkeletalMeshComponent* Body = GetMesh();
	const USkeletalMesh* Asset = Body ? Body->GetSkeletalMeshAsset() : nullptr;
	const int32 HipsIndex = Body ? Body->GetBoneIndex(Hips) : INDEX_NONE;
	const int32 ChestIndex = Body ? Body->GetBoneIndex(Chest) : INDEX_NONE;
	const int32 HeadIndex = Body ? Body->GetBoneIndex(Head) : INDEX_NONE;
	if (!Asset || HipsIndex == INDEX_NONE || ChestIndex == INDEX_NONE || HeadIndex == INDEX_NONE) return;
	const FReferenceSkeleton& Skeleton = Asset->GetRefSkeleton();
	const FVector HipsRest = FAnimationRuntime::GetComponentSpaceTransformRefPose(Skeleton, HipsIndex).GetLocation();
	const FVector ChestRest = FAnimationRuntime::GetComponentSpaceTransformRefPose(Skeleton, ChestIndex).GetLocation();
	const FVector HeadRest = FAnimationRuntime::GetComponentSpaceTransformRefPose(Skeleton, HeadIndex).GetLocation();
	const float Along = ((HeadRest - ChestRest) | (ChestRest - HipsRest).GetSafeNormal()) * Body->GetComponentScale().Z;
	const FVector HipsNow = Body->GetBoneLocation(Hips), ChestNow = Body->GetBoneLocation(Chest);
	const FRotator View = GetControlRotation();
	const FVector Ahead = FRotator(0, View.Yaw, 0).Vector();
	// Looking down, the eyes lean out over the chest so the feet come into view.
	const float LookingDown = FMath::Clamp(-FRotator::NormalizeAxis(View.Pitch) / 90.f, 0.f, 1.f);
	const FVector Eyes = ChestNow + (ChestNow - HipsNow).GetSafeNormal() * (Along + FirstPersonEyeUp)
		+ Ahead * (FirstPersonEyeForward + FirstPersonLookDownForward * LookingDown);
	const FVector Wanted = GetCapsuleComponent()->GetComponentTransform().InverseTransformPosition(Eyes);
	// Up and down the eyes keep up with the body; across they follow slowly, as a head steadies itself through a
	// lunge or a stride, yet still settle where a crouch or lying prone puts them.
	FVector Shown = Wanted;
	if (DeltaSeconds > 0.f)
	{
		const FVector Was = FirstPersonCamera->GetRelativeLocation();
		Shown.X = FMath::FInterpTo(Was.X, Wanted.X, DeltaSeconds, FirstPersonSwayRate);
		Shown.Y = FMath::FInterpTo(Was.Y, Wanted.Y, DeltaSeconds, FirstPersonSwayRate);
		Shown.Z = FMath::FInterpTo(Was.Z, Wanted.Z, DeltaSeconds, FirstPersonFollowRate);
	}
	FirstPersonCamera->SetRelativeLocation(Shown);
}

void AEWCharacter::ApplyFacing()
{
	const bool bFace = bFacingView && !IsOnLadder() && !IsValid(HelmShip) && !IsValid(GunShip);
	bUseControllerRotationYaw = bFace;
	GetCharacterMovement()->bOrientRotationToMovement = !bFace;
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
    if (GunShip) return;
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
    if (HelmShip || GunShip) return;
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
    return SurvivalComponent && SurvivalComponent->GetHealth() > 0.f && !bIsProne && !HelmShip && !GunShip && !IsOnLadder() && !CarriedFish;
}

void AEWCharacter::PlayOneShot(UAnimSequenceBase* Animation) const
{
    if (!Animation || !GetMesh()) return;
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
        Anim->PlaySlotAnimationAsDynamicMontage(Animation, TEXT("DefaultSlot"), .1f, .15f);
}

void AEWCharacter::PlayAttackAnimation(int32 Variant)
{
    // A tool or weapon in hand swings as one; bare hands punch.
    const TArray<TObjectPtr<UAnimSequenceBase>>& Swings = GetHeldMesh() && ToolSwingAnimations.Num() ? ToolSwingAnimations : AttackAnimations;
    if (Swings.Num()) PlayOneShot(Swings[FMath::Abs(Variant) % Swings.Num()]);
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
    const bool bHit = GetWorld()->SweepSingleByChannel(Hit, From, From + View.Vector() * MeleeReach, FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeSphere(MeleeRadius), Query);
    auto* Victim = bHit ? Cast<AEWCharacter>(Hit.GetActor()) : nullptr;
    // Fish, sea creatures and land animals take blows too, when no survivor is in the way first.
    if (!Victim)
    {
        const float Reach = bHit ? FMath::Min(MeleeReach, Hit.Distance + MeleeRadius) : MeleeReach;
        if (AEWFish* Fish = AEWFish::FindStruck(this, Reach)) Fish->TakeStrike(this, FistDamage);
        else if (AEWAnimal* Animal = AEWAnimal::FindStruck(this, Reach)) Animal->TakeStrike(this, FistDamage);
        return nullptr;
    }
    if (!Victim || !Victim->SurvivalComponent || Victim->SurvivalComponent->GetHealth() <= 0.f) return nullptr;
    Victim->SurvivalComponent->ApplyDamage(FistDamage);
    Victim->MulticastHitReact();
    return Victim;
}
