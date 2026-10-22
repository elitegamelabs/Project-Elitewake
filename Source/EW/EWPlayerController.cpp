// Copyright Epic Games, Inc. All Rights Reserved.


#include "EWPlayerController.h"
#include "Ships/EWWreckCrate.h"
#include "Wildlife/EWFish.h"
#include "Wildlife/EWAnimal.h"
#include "EWObjectiveComponent.h"
#include "EWSoundscapeComponent.h"
#include "EWPlacementPreviewComponent.h"
#include "EWCompanyComponent.h"
#include "EWContainerWidget.h"
#include "Ships/EWShip.h"
#include "EWObjectiveWidget.h"
#include "EWMapWidget.h"
#include "EWSessionWidget.h"
#include "EWGameInstance.h"
#include "EWSurvivalComponent.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedInputComponent.h"
#include "Engine/LocalPlayer.h"
#include "InputAction.h"
#include "InputCoreTypes.h"
#include "InputMappingContext.h"
#include "Blueprint/UserWidget.h"
#include "EW.h"
#include "EWInventoryWidget.h"
#include "EWShipMarkersWidget.h"
#include "EWCompassWidget.h"
#include "EWHotbarWidget.h"
#include "EWSurvivalWidget.h"
#include "EWDeathWidget.h"
#include "EWProgressionComponent.h"
#include "InputKeyEventArgs.h"
#include "EWOptionsWidget.h"
#include "EWSurvivorSave.h"
#include "Engine/Engine.h"
#include "Misc/ConfigCacheIni.h"
#include "Kismet/GameplayStatics.h"
#include "EWCharacter.h"
#include "EWPickup.h"
#include "EWInteractable.h"
#include "EWInteractionComponent.h"
#include "EWInteractionWidget.h"
#include "Gathering/EWHarvestTree.h"
#include "Gathering/EWMineable.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Engine/AssetManager.h"
#include "Widgets/Input/SVirtualJoystick.h"

AEWPlayerController::AEWPlayerController()
{
    CompanyComponent = CreateDefaultSubobject<UEWCompanyComponent>(TEXT("Company"));
    ObjectiveComponent = CreateDefaultSubobject<UEWObjectiveComponent>(TEXT("Objectives"));
    InteractionComponent = CreateDefaultSubobject<UEWInteractionComponent>(TEXT("Interaction"));
    SoundscapeComponent = CreateDefaultSubobject<UEWSoundscapeComponent>(TEXT("Soundscape"));
    PlacementPreview = CreateDefaultSubobject<UEWPlacementPreviewComponent>(TEXT("PlacementPreview"));
}

void AEWPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    if (ObjectiveComponent) ObjectiveComponent->ApplyCompletionRecipes();
    if (auto* SurvivorCharacter = Cast<AEWCharacter>(InPawn)) SurvivorCharacter->ApplyUserBrightness(UserBrightness);
}

void AEWPlayerController::BeginPlay()
{
	Super::BeginPlay();
    if (GConfig)
    {
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("BrightnessGamma"), UserBrightness, GGameUserSettingsIni);
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("MouseLookSensitivity"), MouseLookSensitivity, GGameUserSettingsIni);
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("ControllerLookSensitivity"), ControllerLookSensitivity, GGameUserSettingsIni);
        UserBrightness = FMath::Clamp(UserBrightness, -.5f, .5f);
        MouseLookSensitivity = FMath::Clamp(MouseLookSensitivity, .1f, 3.f);
        ControllerLookSensitivity = FMath::Clamp(ControllerLookSensitivity, .1f, 3.f);
    }
    if (auto* SurvivorCharacter = Cast<AEWCharacter>(GetPawn())) SurvivorCharacter->ApplyUserBrightness(UserBrightness);
    if (IsLocalPlayerController())
    {
        ObjectiveWidget = CreateWidget<UEWObjectiveWidget>(this, UEWObjectiveWidget::StaticClass());
        if (ObjectiveWidget) ObjectiveWidget->AddToPlayerScreen(2);
        HotbarWidget = CreateWidget<UEWHotbarWidget>(this, UEWHotbarWidget::StaticClass());
        if (HotbarWidget) HotbarWidget->AddToPlayerScreen(1);
        SurvivalWidget = CreateWidget<UEWSurvivalWidget>(this, UEWSurvivalWidget::StaticClass());
        if (SurvivalWidget) SurvivalWidget->AddToPlayerScreen(2);
        InteractionWidget = CreateWidget<UEWInteractionWidget>(this, UEWInteractionWidget::StaticClass());
        if (InteractionWidget) InteractionWidget->AddToPlayerScreen(3);
        ShipMarkersWidget = CreateWidget<UEWShipMarkersWidget>(this, UEWShipMarkersWidget::StaticClass());
        if (ShipMarkersWidget) ShipMarkersWidget->AddToPlayerScreen(1);
        CompassWidget = CreateWidget<UEWCompassWidget>(this, UEWCompassWidget::StaticClass());
        if (CompassWidget) CompassWidget->AddToPlayerScreen(1);
        DeathWidget = CreateWidget<UEWDeathWidget>(this, UEWDeathWidget::StaticClass());
        if (DeathWidget) DeathWidget->AddToPlayerScreen(90);
        HitMarkerWidget = CreateWidget<UEWHitMarkerWidget>(this, UEWHitMarkerWidget::StaticClass());
        if (HitMarkerWidget) HitMarkerWidget->AddToPlayerScreen(4);
        if (auto* Instance=GetGameInstance<UEWGameInstance>()) Instance->LocalControllerReady(this);
    }

	// only spawn touch controls on local player controllers
	if (IsLocalPlayerController() && ShouldUseTouchControls())
	{
		// spawn the mobile controls widget
		MobileControlsWidget = CreateWidget<UUserWidget>(this, MobileControlsWidgetClass);

		if (MobileControlsWidget)
		{
			// add the controls to the player screen
			MobileControlsWidget->AddToPlayerScreen(0);

		} else {

			UE_LOG(LogEW, Error, TEXT("Could not spawn mobile controls widget."));

		}

	}
}

void AEWPlayerController::SetUserBrightness(float Value)
{
    if (!IsLocalPlayerController()) return;
    UserBrightness = FMath::Clamp(Value, -.5f, .5f);
    if (auto* SurvivorCharacter = Cast<AEWCharacter>(GetPawn())) SurvivorCharacter->ApplyUserBrightness(UserBrightness);
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), TEXT("BrightnessGamma"), UserBrightness, GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

void AEWPlayerController::SetMouseLookSensitivity(float Value)
{
    if (!IsLocalPlayerController()) return;
    MouseLookSensitivity = FMath::Clamp(Value, .1f, 3.f);
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), TEXT("MouseLookSensitivity"), MouseLookSensitivity, GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

void AEWPlayerController::SetControllerLookSensitivity(float Value)
{
    if (!IsLocalPlayerController()) return;
    ControllerLookSensitivity = FMath::Clamp(Value, .1f, 3.f);
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), TEXT("ControllerLookSensitivity"), ControllerLookSensitivity, GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

void AEWPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

    AttackAction = NewObject<UInputAction>(this, TEXT("IA_Attack_Runtime"));
    AttackAction->ValueType = EInputActionValueType::Boolean;
    RuntimeAttackMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Attack_Runtime"));
    RuntimeAttackMappingContext->MapKey(AttackAction, EKeys::LeftMouseButton);
    RuntimeAttackMappingContext->MapKey(AttackAction, EKeys::Gamepad_RightTrigger);
    ClimbUpAction = NewObject<UInputAction>(this, TEXT("IA_ClimbUp_Runtime"));
    ClimbUpAction->ValueType = EInputActionValueType::Boolean;
    ClimbDownAction = NewObject<UInputAction>(this, TEXT("IA_ClimbDown_Runtime"));
    ClimbDownAction->ValueType = EInputActionValueType::Boolean;
    RuntimeAttackMappingContext->MapKey(ClimbUpAction, EKeys::Up);
    RuntimeAttackMappingContext->MapKey(ClimbUpAction, EKeys::Gamepad_DPad_Up);
    RuntimeAttackMappingContext->MapKey(ClimbDownAction, EKeys::Down);
    RuntimeAttackMappingContext->MapKey(ClimbDownAction, EKeys::Gamepad_DPad_Down);
    SailLeftAction = NewObject<UInputAction>(this, TEXT("IA_SailLeft_Runtime"));
    SailLeftAction->ValueType = EInputActionValueType::Boolean;
    SailRightAction = NewObject<UInputAction>(this, TEXT("IA_SailRight_Runtime"));
    SailRightAction->ValueType = EInputActionValueType::Boolean;
    RuntimeAttackMappingContext->MapKey(SailLeftAction, EKeys::Left);
    RuntimeAttackMappingContext->MapKey(SailLeftAction, EKeys::Gamepad_LeftShoulder);
    RuntimeAttackMappingContext->MapKey(SailRightAction, EKeys::Right);
    RuntimeAttackMappingContext->MapKey(SailRightAction, EKeys::Gamepad_RightShoulder);

    if (!InteractAction)
    {
        InteractAction = NewObject<UInputAction>(this, TEXT("IA_Interact_Runtime"));
        InteractAction->ValueType = EInputActionValueType::Boolean;
        RuntimeInteractionMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Interact_Runtime"));
        RuntimeInteractionMappingContext->MapKey(InteractAction, EKeys::E);
        RuntimeInteractionMappingContext->MapKey(InteractAction, EKeys::Gamepad_FaceButton_Left);
    }

	// Milestone 5 fallback: create an Enhanced Input action in code so the draft works
	// immediately. A designer-authored IA_Inventory asset can be assigned later.
	if (!InventoryAction)
	{
		InventoryAction = NewObject<UInputAction>(this, TEXT("IA_Inventory_Runtime"));
		InventoryAction->ValueType = EInputActionValueType::Boolean;
		RuntimeInventoryMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Inventory_Runtime"));
		RuntimeInventoryMappingContext->MapKey(InventoryAction, EKeys::I);
        RuntimeInventoryMappingContext->MapKey(InventoryAction, EKeys::Gamepad_FaceButton_Top);
	}

	if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(InputComponent))
	{
        EnhancedInput->BindAction(AttackAction, ETriggerEvent::Started, this, &AEWPlayerController::Attack);
        EnhancedInput->BindAction(ClimbUpAction, ETriggerEvent::Started, this, &AEWPlayerController::ClimbUp);
        EnhancedInput->BindAction(ClimbUpAction, ETriggerEvent::Completed, this, &AEWPlayerController::ClimbStop);
        EnhancedInput->BindAction(ClimbDownAction, ETriggerEvent::Started, this, &AEWPlayerController::ClimbDown);
        EnhancedInput->BindAction(ClimbDownAction, ETriggerEvent::Completed, this, &AEWPlayerController::ClimbStop);
        EnhancedInput->BindAction(SailLeftAction, ETriggerEvent::Started, this, &AEWPlayerController::SailLeft);
        EnhancedInput->BindAction(SailLeftAction, ETriggerEvent::Completed, this, &AEWPlayerController::SailStop);
        EnhancedInput->BindAction(SailRightAction, ETriggerEvent::Started, this, &AEWPlayerController::SailRight);
        EnhancedInput->BindAction(SailRightAction, ETriggerEvent::Completed, this, &AEWPlayerController::SailStop);
        EnhancedInput->BindAction(InteractAction, ETriggerEvent::Started, this, &AEWPlayerController::Interact);
        EnhancedInput->BindAction(InteractAction, ETriggerEvent::Completed, this, &AEWPlayerController::ReleaseInteraction);
        EnhancedInput->BindAction(InteractAction, ETriggerEvent::Canceled, this, &AEWPlayerController::ReleaseInteraction);
		if (InventoryAction)
		{
			EnhancedInput->BindAction(InventoryAction, ETriggerEvent::Started, this, &AEWPlayerController::ToggleInventory);
		}
	}

	// only add IMCs for local player controllers
	if (IsLocalPlayerController())
	{
		// Add Input Mapping Contexts
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
		{

            if (RuntimeInteractionMappingContext)
                Subsystem->AddMappingContext(RuntimeInteractionMappingContext, 1);
            Subsystem->AddMappingContext(RuntimeAttackMappingContext, 1);
			if (RuntimeInventoryMappingContext)
			{
				Subsystem->AddMappingContext(RuntimeInventoryMappingContext, 1);
			}

			for (UInputMappingContext* CurrentContext : DefaultMappingContexts)
			{
				Subsystem->AddMappingContext(CurrentContext, 0);
			}

			// only add these IMCs if we're not using mobile touch input
			if (!ShouldUseTouchControls())
			{
				for (UInputMappingContext* CurrentContext : MobileExcludedMappingContexts)
				{
					Subsystem->AddMappingContext(CurrentContext, 0);
				}
			}
		}
	}
}

void AEWPlayerController::SetClimbInput(float Direction)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor) return;
    // A gunner opens their port with Up and shuts it with Down (owner, October 17).
    if (Survivor->GetGunShip())
    {
        if (Direction != 0.f && !IsMapOpen() && !IsSessionMenuOpen()) Survivor->ServerSetGunport(Direction > 0.f);
        return;
    }
    // At a helm, holding Up/Down (or the D-pad) raises/lowers sail one 25% step at a time.
    if (Survivor->GetHelmShip())
    {
        Survivor->SetSailStepInput(IsMapOpen() || IsSessionMenuOpen() ? 0.f : Direction);
        return;
    }
    Survivor->SetLadderArrowInput(Direction);
}

void AEWPlayerController::SetSailInput(float Direction)
{
    // The survivor uses it only while at a helm; anywhere else these keys do nothing.
    if (auto* Survivor = Cast<AEWCharacter>(GetPawn())) Survivor->SetSailArrowInput(IsMapOpen() || IsSessionMenuOpen() ? 0.f : Direction);
}

void AEWPlayerController::Attack()
{
    if (!IsLocalPlayerController() || IsInventoryOpen() || IsMapOpen() || IsSessionMenuOpen()) return;
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (Survivor && Survivor->GetGunShip()) { Survivor->ServerFireCannon(); return; }
    // A torch is lit and a waterskin drunk with Left Mouse rather than swung.
    // Anything in hand strikes a creature it is aimed at, a torch or a waterskin included.
    if (Survivor && Survivor->HasUsableHeldItem() && !AEWFish::FindStruck(Survivor, AEWCharacter::MeleeReach)
        && !AEWAnimal::FindStruck(Survivor, AEWCharacter::MeleeReach)) { Survivor->ServerUseHeldItem(); return; }
    if (!Survivor || !Survivor->CanAttack()) return;
    // Swing at once on this screen, at the pace the server allows; the server decides what it hits.
    const double Now = GetWorld()->GetTimeSeconds();
    if (Now - LastLocalAttackTime < AttackInterval) return;
    LastLocalAttackTime = Now;
    AActor* Target = FEWInteractionTargeting::FindTarget(Survivor);
    const int32 Variant = ((++AttackVariant) << 2) | Survivor->SwingKindAt(Target);
    Survivor->PlayAttackAnimation(Variant);
    ServerAttack(Target, Variant);
}

void AEWPlayerController::ServerAttack_Implementation(AActor* Target, int32 Variant)
{
    const double Now = GetWorld()->GetTimeSeconds();
    // Per-controller admission, across targets, a little looser than the owner's own pacing so that network
    // timing never refuses a swing the owner saw.
    if (Now - LastHarvestAttackTime < AttackInterval - .1) return;
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || !Survivor->CanAttack()) return;
    if (InteractionComponent->IsMenuBlocked() || InteractionComponent->GetHoldState().Target) return;
    LastHarvestAttackTime = Now;
    // The swing the server shows is the one its tool and target call for, whatever the client sent.
    const int32 Kind = Survivor->SwingKindAt(Target);
    Survivor->BroadcastAttack((Variant & ~3) | Kind);
    auto* Tree = Cast<AEWHarvestTree>(Target);
    auto* Node = Cast<AEWMineable>(Target);
    if (!Tree && !Node) { Survivor->MeleeStrike(); return; }
    // Only what the survivor is aimed at and close enough to work takes the blow.
    if (FEWInteractionTargeting::FindTarget(Survivor) != Target) return;
    UEWInventoryComponent* Pack = Survivor->GetInventoryComponent();
    TArray<UEWItemDefinition*> Watched;
    if (Tree) { Watched = {Tree->Wood, Tree->Thatch}; }
    else { Watched = {Node->Resource}; }
    TArray<int32> Before;
    for (UEWItemDefinition* Item : Watched) Before.Add(Item && Pack ? Pack->GetItemCount(Item) : 0);
    EEWWorkRefusal Refusal = EEWWorkRefusal::None;
    if (Tree && Tree->CanAccessSource(Survivor) && !Tree->CanHarvest(Survivor)) Refusal = EEWWorkRefusal::NeedsHatchet;
    if (Node && Node->CanAccessSource(Survivor) && !Node->CanMine(Survivor)) Refusal = EEWWorkRefusal::NeedsPickaxe;
    const int32 Got = Tree ? Tree->TryHarvest(Survivor) : Node->TryMine(Survivor);
    TArray<FEWGatherGain> Gains;
    for (int32 i = 0; i < Watched.Num(); ++i)
    {
        const int32 Delta = Watched[i] && Pack ? Pack->GetItemCount(Watched[i]) - Before[i] : 0;
        if (Delta > 0) { FEWGatherGain Gain; Gain.Item = Watched[i]; Gain.Count = Delta; Gains.Add(Gain); }
    }
    if (Got <= 0 && Refusal == EEWWorkRefusal::None) Refusal = EEWWorkRefusal::PackFull;
    // Where the blow lands: the face of the trunk or rock where the survivor is looking.
    FVector Eye; FRotator View;
    Survivor->GetActorEyesViewPoint(Eye, View);
    FVector Point = Target->GetComponentsBoundingBox().GetClosestPointTo(Eye);
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWWorkImpact), true, Survivor);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + View.Vector() * 600.f, ECC_Visibility, Query) && Hit.GetActor() == Target)
        Point = Hit.ImpactPoint;
    const FVector Normal = (Survivor->GetActorLocation() - Point).GetSafeNormal2D();
    Survivor->ShowWorkImpact(Target, Point, Normal, Tree ? EEWWorkSurface::Wood : EEWWorkSurface::Stone, Gains, Refusal, Kind);
}

void AEWPlayerController::ShowWorkHit(bool bGave, const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal)
{
    if (HitMarkerWidget) HitMarkerWidget->ShowHit(bGave, Gains, Refusal);
}

void AEWPlayerController::ShowGains(const TArray<FEWGatherGain>& Gains)
{
    if (HitMarkerWidget) HitMarkerWidget->ShowGains(Gains);
}

void AEWPlayerController::RequestAppearance(const FEWAppearance& Appearance)
{
    if (IsLocalController()) ServerSetAppearance(Appearance);
}

void AEWPlayerController::ServerSetAppearance_Implementation(const FEWAppearance& Appearance)
{
    if (auto* Survivor = Cast<AEWCharacter>(GetPawn())) Survivor->SetAppearance(Appearance);
}

void AEWPlayerController::AcknowledgePossession(APawn* P)
{
    Super::AcknowledgePossession(P);
    const auto* Instance = Cast<UEWGameInstance>(GetGameInstance());
    if (Instance && Instance->HasChosenAppearance() && Cast<AEWCharacter>(P)) RequestAppearance(Instance->GetChosenAppearance());
}

void AEWPlayerController::Interact()
{
    if (!IsLocalPlayerController() || IsMapOpen() || IsSessionMenuOpen() || (InventoryWidget && InventoryWidget->IsInViewport())) return;
    bLocalInteractionIntent = true;
    if (AActor* Target = FEWInteractionTargeting::FindTarget(Cast<AEWCharacter>(GetPawn())))
        ServerInteract(Target);
}

void AEWPlayerController::ReleaseInteraction()
{
    if (!IsLocalPlayerController() || !bLocalInteractionIntent) return;
    bLocalInteractionIntent = false;
    ServerCancelInteraction();
}

void AEWPlayerController::ServerCancelInteraction_Implementation()
{
    InteractionComponent->Cancel();
}
void AEWPlayerController::ServerSetInteractionMenuBlocked_Implementation(bool bBlocked)
{
    InteractionComponent->SetMenuBlocked(bBlocked || IsMapOpen() || IsSessionMenuOpen());
}

int32 AEWPlayerController::HotbarSlotForKey(const FKey& Key, bool bControllerModifier)
{
    static const FKey Numbers[] = {EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight};
    static const FKey ControllerKeys[] = {EKeys::Gamepad_DPad_Left,EKeys::Gamepad_DPad_Up,
        EKeys::Gamepad_DPad_Right,EKeys::Gamepad_DPad_Down,
        EKeys::Gamepad_FaceButton_Bottom,EKeys::Gamepad_FaceButton_Left,
        EKeys::Gamepad_FaceButton_Right,EKeys::Gamepad_FaceButton_Top};
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
        if (Key==Numbers[i] || (i < 4 && Key==ControllerKeys[i]) || (i >= 4 && bControllerModifier && Key==ControllerKeys[i])) return i;
    return INDEX_NONE;
}

bool AEWPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
    if (Params.Key==EKeys::F10)
    {
        if (Params.Event==IE_Pressed) SetSessionMenuOpen(!IsSessionMenuOpen());
        return true;
    }
    if (IsSessionMenuOpen() || IsOptionsMenuOpen()) return true;
    if (bMapOpen)
    {
        // The map owns right-stick panning and trigger zoom while open, so those inputs
        // cannot leak into gameplay actions such as attack or weapon selection.
        if (Params.Key == EKeys::Gamepad_RightX || Params.Key == EKeys::Gamepad_RightY)
        {
            if (MapWidget)
            {
                MapWidget->SetPanAxis(Params.Key == EKeys::Gamepad_RightX, Params.AmountDepressed
                    * (Params.Key == EKeys::Gamepad_RightX ? 1.f : -1.f));
            }
            return true;
        }
        if (Params.Key == EKeys::Gamepad_RightTriggerAxis || Params.Key == EKeys::Gamepad_LeftTriggerAxis)
        {
            if (MapWidget) MapWidget->SetZoomInput((Params.Key == EKeys::Gamepad_RightTriggerAxis ? 1.f : -1.f)
                * FMath::Max(0.f, Params.AmountDepressed));
            return true;
        }
    }
    if (Params.Key == EKeys::M)
    {
        if (Params.Event == IE_Pressed) SetMapOpen(!bMapOpen);
        return true;
    }
    if (Params.Key == EKeys::Escape || Params.Key == EKeys::Gamepad_Special_Right)
    {
        // Escape closes the map first; otherwise it brings up OPTIONS.
        if (Params.Event == IE_Pressed) { if (bMapOpen) SetMapOpen(false); else SetOptionsMenuOpen(true); }
        return true;
    }
    if (bMapOpen && (Params.Key == EKeys::I || Params.Key == EKeys::C || Params.Key == EKeys::LeftShift
        || HotbarSlotForKey(Params.Key,bHotbarModifierHeld) != INDEX_NONE)) return true;
    // Ignore neutral stick/trigger samples so an idle controller cannot steal keyboard prompts.
    if (Params.Event != IE_Released && Params.Key.IsValid()
        && (Params.Event != IE_Axis || FMath::Abs(Params.AmountDepressed) > (Params.Key.IsGamepadKey() ? .2f : KINDA_SMALL_NUMBER)))
        RecordInputDevice(Params.Key);
    if (SuppressedHotbarKeys.Contains(Params.Key))
    {
        if (Params.Event==IE_Released) SuppressedHotbarKeys.Remove(Params.Key);
        return true;
    }
    if (Params.Key==EKeys::Gamepad_LeftShoulder)
    {
        if (Params.Event==IE_Pressed) bHotbarModifierHeld=true;
        if (Params.Event==IE_Released) bHotbarModifierHeld=false;
        return true;
    }
    if (!InventoryWidget || !InventoryWidget->IsInViewport())
    {
        const int32 Slot = HotbarSlotForKey(Params.Key,bHotbarModifierHeld);
        const AEWCharacter* Survivor = Cast<AEWCharacter>(GetPawn());
        const bool bClimbDirection = Survivor && Survivor->IsOnLadder()
            && (Params.Key == EKeys::Gamepad_DPad_Up || Params.Key == EKeys::Gamepad_DPad_Down);
        if (Slot!=INDEX_NONE && !bClimbDirection && Params.Event==IE_Pressed)
        {
            // Consume the complete chord, including releases after LB is released, before Enhanced Input.
            SuppressedHotbarKeys.Add(Params.Key);
            RequestHotbarActivation(Slot);
            return true;
        }
        if (Slot!=INDEX_NONE && !bClimbDirection && Params.Event==IE_Repeat) return true;
    }
    return Super::InputKey(Params);
}

void AEWPlayerController::FlushPressedKeys()
{
    ReleaseInteraction();
    // The engine also flushes on viewport focus loss; custom chord state must follow it.
    bHotbarModifierHeld=false;
    SuppressedHotbarKeys.Reset();
    Super::FlushPressedKeys();
}

void AEWPlayerController::RequestHotbarBinding(int32 Slot, UEWItemDefinition* Item)
{
    if (IsLocalPlayerController() && !IsMapOpen() && !IsSessionMenuOpen()) ServerBindHotbar(Slot,Item);
}
void AEWPlayerController::RequestConsumeFood(UEWItemDefinition* Item)
{
    if (IsLocalPlayerController()) ServerConsumeFood(Item);
}

void AEWPlayerController::RequestCraft(UEWCraftingRecipe* Recipe)
{
    if (IsLocalPlayerController() && !IsMapOpen() && !IsSessionMenuOpen()) ServerCraft(Recipe);
}
void AEWPlayerController::ServerSpendStatPoint_Implementation(EEWStat Stat)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (Survivor && Survivor->GetProgressionComponent() && !Survivor->IsDead()) Survivor->GetProgressionComponent()->SpendPoint(Stat);
}

void AEWPlayerController::ServerRequestRespawn_Implementation()
{
    if (auto* Survivor = Cast<AEWCharacter>(GetPawn())) Survivor->RespawnAfterDeath();
}

void AEWPlayerController::ServerCraft_Implementation(UEWCraftingRecipe* Recipe)
{
    auto* OwnedCrafter = Cast<AEWCharacter>(GetPawn());
    if (IsMapOpen() || IsSessionMenuOpen() || !OwnedCrafter || OwnedCrafter->GetController() != this || OwnedCrafter->GetSurvivalComponent()->GetHealth() <= 0.f)
    { ClientCraftResult(EEWCraftResult::Busy); return; }
    const EEWCraftResult Result = OwnedCrafter->GetInventoryComponent()->CraftItem(Recipe);
    if (Result == EEWCraftResult::Success && OwnedCrafter->GetProgressionComponent()) OwnedCrafter->GetProgressionComponent()->Award(EEWExperienceSource::Craft);
    ClientCraftResult(Result);
}
void AEWPlayerController::ClientCraftResult_Implementation(EEWCraftResult Result)
{
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowCraftResult(Result);
}
void AEWPlayerController::ServerConsumeFood_Implementation(UEWItemDefinition* Item)
{
    auto* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientFoodResult(OwnedCharacter && OwnedCharacter->GetController() == this
        ? OwnedCharacter->GetInventoryComponent()->ConsumeFood(Item) : EEWFoodUseResult::NotOwned);
}
void AEWPlayerController::ClientFoodResult_Implementation(EEWFoodUseResult Result)
{
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowFoodResult(Result);
}
void AEWPlayerController::RequestHotbarActivation(int32 Slot)
{
    if (IsLocalPlayerController() && (!InventoryWidget || !InventoryWidget->IsInViewport())) ServerActivateHotbar(Slot);
}
void AEWPlayerController::ServerBindHotbar_Implementation(int32 Slot, UEWItemDefinition* Item)
{
    if (IsMapOpen() || IsSessionMenuOpen()) return;
    auto* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientHotbarResult(OwnedCharacter && OwnedCharacter->GetController()==this
        ? OwnedCharacter->GetHotbarComponent()->BindItem(Slot,Item) : EEWHotbarResult::NotOwned);
}
void AEWPlayerController::ServerActivateHotbar_Implementation(int32 Slot)
{
    if (IsMapOpen() || IsSessionMenuOpen()) return;
    auto* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientHotbarResult(OwnedCharacter && OwnedCharacter->GetController()==this
        ? (InteractionComponent->IsMenuBlocked() ? EEWHotbarResult::Busy : OwnedCharacter->GetHotbarComponent()->ActivateSlot(Slot)) : EEWHotbarResult::NotOwned);
}
void AEWPlayerController::ClientHotbarResult_Implementation(EEWHotbarResult Result)
{
    if (HotbarWidget) HotbarWidget->ShowResult(Result);
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowHotbarResult(Result);
}
void AEWPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bHotbarModifierHeld=false; SuppressedHotbarKeys.Reset();
    if (SessionWidget) SessionWidget->RemoveFromParent();
    if (MapWidget) MapWidget->RemoveFromParent();
    if (ObjectiveWidget) ObjectiveWidget->RemoveFromParent();
    if (HotbarWidget) HotbarWidget->RemoveFromParent();
    if (SurvivalWidget) SurvivalWidget->RemoveFromParent();
    if (InteractionWidget) InteractionWidget->RemoveFromParent();
    Super::EndPlay(EndPlayReason);
}

void AEWPlayerController::RequestEquipItem(UEWItemDefinition* Item, EEWEquipmentSlot Slot)
{
    if (IsLocalPlayerController()) ServerEquipItem(Item, Slot);
}

void AEWPlayerController::RequestUnequipItem(EEWEquipmentSlot Slot)
{
    if (IsLocalPlayerController()) ServerUnequipItem(Slot);
}

void AEWPlayerController::ServerEquipItem_Implementation(UEWItemDefinition* Item, EEWEquipmentSlot Slot)
{
    AEWCharacter* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    const EEWEquipmentResult Result = OwnedCharacter && OwnedCharacter->GetController() == this
        ? OwnedCharacter->GetEquipmentComponent()->EquipItem(Item, Slot) : EEWEquipmentResult::NotOwned;
    UE_LOG(LogEW, Verbose, TEXT("Equip intent %s slot %d result %d pawn %s"), *GetNameSafe(Item), static_cast<int32>(Slot), static_cast<int32>(Result), *GetNameSafe(OwnedCharacter));
    ClientEquipmentResult(Result);
}

void AEWPlayerController::ServerUnequipItem_Implementation(EEWEquipmentSlot Slot)
{
    AEWCharacter* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientEquipmentResult(OwnedCharacter && OwnedCharacter->GetController() == this
        ? OwnedCharacter->GetEquipmentComponent()->UnequipItem(Slot) : EEWEquipmentResult::NotOwned);
}

void AEWPlayerController::ClientEquipmentResult_Implementation(EEWEquipmentResult Result)
{
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowEquipmentResult(Result);
}

void AEWPlayerController::ServerInteract_Implementation(AActor* Target)
{
    InteractionComponent->Request(Target);
}

void AEWPlayerController::EWGrantTestWood(int32 Quantity)
{
#if WITH_EDITOR
	if (!HasAuthority() || Quantity <= 0)
	{
		UE_LOG(LogEW, Warning, TEXT("Test Wood grant rejected: authority and a positive quantity are required."));
		return;
	}

	AEWCharacter* EWCharacter = Cast<AEWCharacter>(GetPawn());
	UEWInventoryComponent* Inventory = EWCharacter ? EWCharacter->GetInventoryComponent() : nullptr;
	const FSoftObjectPath ItemPath = UAssetManager::Get().GetPrimaryAssetPath(FPrimaryAssetId(TEXT("EWItem"), TEXT("Test.Wood")));
	UEWItemDefinition* Wood = Cast<UEWItemDefinition>(ItemPath.TryLoad());
	if (!Inventory || !Wood)
	{
		UE_LOG(LogEW, Warning, TEXT("Test Wood grant unavailable: possess an EW character and create the registered DA_TestWood asset."));
		return;
	}

	const int32 Added = Inventory->AddItem(Wood, Quantity);
	UE_LOG(LogEW, Display, TEXT("Test Wood grant: requested=%d added=%d total=%d slots=%d weight=%.1f kg"),
		Quantity, Added, Inventory->GetItemCount(Wood), Inventory->GetUsedSlotCount(), Inventory->GetTotalWeight());
#endif
}

void AEWPlayerController::ToggleInventory()
{
    // With a container open, the inventory key closes it rather than stacking screens.
    if (ContainerWidget && ContainerWidget->IsInViewport()) { SetInventoryOpen(false); return; }
	SetInventoryOpen(!InventoryWidget || !InventoryWidget->IsInViewport());
}

void AEWPlayerController::SetMenuInputBlocked(bool bBlocked)
{
    if (HotbarWidget) HotbarWidget->SetVisibility(bBlocked ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    if (SurvivalWidget) SurvivalWidget->SetVisibility(bBlocked ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    if (bInventoryInputBlocked == bBlocked) return;
    ServerSetInteractionMenuBlocked(bBlocked);
    FlushPressedKeys();
    SetIgnoreMoveInput(bBlocked);
    SetIgnoreLookInput(bBlocked);
    bInventoryInputBlocked = bBlocked;
    if (bBlocked && GetPawn()) GetPawn()->ConsumeMovementInputVector();
}

void AEWPlayerController::SetContainerOpen(AActor* Container)
{
    if (!IsLocalPlayerController()) return;
    if (!IsValid(Container)) { SetInventoryOpen(false); return; }
    if (IsMapOpen() || IsSessionMenuOpen()) return;
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->RemoveFromParent();
    SetMenuInputBlocked(true);
    OpenContainer = Container;
    if (!ContainerWidget) ContainerWidget = CreateWidget<UEWContainerWidget>(this, UEWContainerWidget::StaticClass());
    if (!ContainerWidget) return;
    ContainerWidget->SetContainer(Container);
    if (!ContainerWidget->IsInViewport()) ContainerWidget->AddToPlayerScreen(20);
    FInputModeUIOnly InputMode;
    InputMode.SetWidgetToFocus(ContainerWidget->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(InputMode);
    SetShowMouseCursor(true);
    ContainerWidget->SetUserFocus(this);
}

void AEWPlayerController::ClientOpenContainer_Implementation(AActor* Container)
{
    SetContainerOpen(Container);
}

void AEWPlayerController::ServerTransferContainerItem_Implementation(AActor* Container, bool bToContainer, int32 EntryIndex, int32 Quantity)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || !IsValid(Container) || Container->GetWorld() != GetWorld() || !FEWContainerAccess::CanAccess(Container, Survivor)) return;
    UEWInventoryComponent* Carried = Survivor->GetInventoryComponent();
    UEWInventoryComponent* Hold = FEWContainerAccess::Inventory(Container);
    if (!Carried || !Hold) return;
    if (bToContainer) Carried->TransferEntryTo(Hold, EntryIndex, Quantity);
    else Hold->TransferEntryTo(Carried, EntryIndex, Quantity);
}

void AEWPlayerController::SetInventoryOpen(bool bOpen)
{
    if (bOpen && (IsMapOpen() || IsSessionMenuOpen())) return;
	if (!IsLocalPlayerController())
	{
		return;
	}

    if (ContainerWidget && ContainerWidget->IsInViewport()) ContainerWidget->RemoveFromParent();
    OpenContainer = nullptr;
    SetMenuInputBlocked(bOpen);

	if (bOpen)
	{
		if (!InventoryWidget)
		{
			InventoryWidget = CreateWidget<UEWInventoryWidget>(this, UEWInventoryWidget::StaticClass());
		}
		if (InventoryWidget && !InventoryWidget->IsInViewport())
		{
			InventoryWidget->AddToPlayerScreen(20);
		}

		FInputModeUIOnly InputMode;
        if (InventoryWidget) InputMode.SetWidgetToFocus(InventoryWidget->TakeWidget());
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		SetInputMode(InputMode);
		SetShowMouseCursor(true);
        if (InventoryWidget) InventoryWidget->SetUserFocus(this);
	}
	else
	{
		if (InventoryWidget)
		{
			InventoryWidget->RemoveFromParent();
		}

		SetInputMode(FInputModeGameOnly());
		SetShowMouseCursor(false);
	}
}

bool AEWPlayerController::ShouldUseTouchControls() const
{
	// are we on a mobile platform? Should we force touch?
	return SVirtualJoystick::ShouldDisplayTouchInterface() || bForceTouchControls;
}

void AEWPlayerController::SetMapOpen(bool bOpen)
{
    if (!IsLocalPlayerController() || bMapOpen == bOpen || (bOpen && IsSessionMenuOpen())) return;
    if (bOpen && IsInventoryOpen()) SetInventoryOpen(false);
    FlushPressedKeys();
    bMapOpen = bOpen;
    SetIgnoreLookInput(bOpen);
    if (auto* MapSurvivor = Cast<AEWCharacter>(GetPawn()))
    { MapSurvivor->CancelRestrictedActions(); }
    ServerSetMapOpen(bOpen);
    if (bOpen)
    {
        MapWidget = CreateWidget<UEWMapWidget>(this,UEWMapWidget::StaticClass());
        if (MapWidget) MapWidget->AddToPlayerScreen(30);
    }
    else if (MapWidget) { MapWidget->RemoveFromParent(); MapWidget = nullptr; }
    if (bOpen && MapWidget)
    {
        FInputModeGameAndUI InputMode;
        InputMode.SetWidgetToFocus(MapWidget->TakeWidget());
        InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        SetInputMode(InputMode);
        SetShowMouseCursor(true);
    }
    else
    {
        SetInputMode(FInputModeGameOnly());
        SetShowMouseCursor(false);
    }
}
void AEWPlayerController::ServerSetMapOpen_Implementation(bool bOpen)
{
    bMapOpen = bOpen;
    InteractionComponent->SetMenuBlocked(bOpen || IsInventoryOpen() || IsSessionMenuOpen());
    if (bOpen) if (auto* MapSurvivor = Cast<AEWCharacter>(GetPawn()))
    { MapSurvivor->CancelRestrictedActions(); }
}

void AEWPlayerController::SetSessionMenuOpen(bool bOpen)
{
    if (!IsLocalPlayerController() || bSessionMenuOpen==bOpen) return;
    if (bOpen) { SetMapOpen(false); SetInventoryOpen(false); SetOptionsMenuOpen(false); }
    FlushPressedKeys(); bSessionMenuOpen=bOpen;
    SetIgnoreMoveInput(bOpen); SetIgnoreLookInput(bOpen);
    if (auto* Survivor=Cast<AEWCharacter>(GetPawn())) Survivor->CancelRestrictedActions();
    ServerSetSessionMenuOpen(bOpen);
    if (bOpen)
    {
        SessionWidget=CreateWidget<UEWSessionWidget>(this,UEWSessionWidget::StaticClass());
        if (SessionWidget)
        {
            SessionWidget->AddToPlayerScreen(100);
            FInputModeUIOnly Mode; Mode.SetWidgetToFocus(SessionWidget->TakeWidget()); SetInputMode(Mode);
        }
    }
    else { if (SessionWidget) SessionWidget->RemoveFromParent(); SessionWidget=nullptr; SetInputMode(FInputModeGameOnly()); }
    bShowMouseCursor=bOpen;
}
void AEWPlayerController::SetOptionsMenuOpen(bool bOpen)
{
    if (!IsLocalPlayerController() || bOptionsMenuOpen==bOpen) return;
    if (bOpen) { SetMapOpen(false); SetInventoryOpen(false); SetSessionMenuOpen(false); }
    FlushPressedKeys(); bOptionsMenuOpen=bOpen;
    SetIgnoreMoveInput(bOpen); SetIgnoreLookInput(bOpen);
    if (auto* Survivor=Cast<AEWCharacter>(GetPawn())) Survivor->CancelRestrictedActions();
    ServerSetOptionsMenuOpen(bOpen);
    // Single player pauses behind the menu; a shared world carries on (design: Pause).
    if (GetWorld() && GetWorld()->GetNetMode()==NM_Standalone) SetPause(bOpen);
    if (bOpen)
    {
        OptionsWidget=CreateWidget<UEWOptionsWidget>(this,UEWOptionsWidget::StaticClass());
        if (OptionsWidget)
        {
            OptionsWidget->AddToPlayerScreen(110);
            FInputModeUIOnly Mode; Mode.SetWidgetToFocus(OptionsWidget->TakeWidget()); SetInputMode(Mode);
        }
    }
    else { if (OptionsWidget) OptionsWidget->RemoveFromParent(); OptionsWidget=nullptr; SetInputMode(FInputModeGameOnly()); }
    bShowMouseCursor=bOpen;
}
void AEWPlayerController::ServerSetOptionsMenuOpen_Implementation(bool bOpen)
{
    bOptionsMenuOpen=bOpen;
    InteractionComponent->SetMenuBlocked(bOpen || IsMapOpen() || IsInventoryOpen() || IsSessionMenuOpen());
    if (bOpen) if (auto* Survivor=Cast<AEWCharacter>(GetPawn())) Survivor->CancelRestrictedActions();
}
bool AEWPlayerController::SaveSurvivorGame()
{
    if (!IsLocalPlayerController() || !GetWorld() || GetWorld()->GetNetMode()!=NM_Standalone) return false;
    return UEWSurvivorSave::SaveSurvivor(Cast<AEWCharacter>(GetPawn()));
}
void AEWPlayerController::ReturnToMainMenu()
{
    if (!IsLocalPlayerController()) return;
    SetOptionsMenuOpen(false);
    SetPause(false);
    if (GEngine && GetWorld()) GEngine->CancelPending(GetWorld());
    UGameplayStatics::OpenLevel(this, FName(TEXT("/Game/Elitewake/Maps/Lvl_Title")));
}
void AEWPlayerController::ServerSetSessionMenuOpen_Implementation(bool bOpen)
{
    bSessionMenuOpen=bOpen;
    InteractionComponent->SetMenuBlocked(bOpen || IsMapOpen() || IsInventoryOpen());
    if (bOpen) if (auto* Survivor=Cast<AEWCharacter>(GetPawn())) Survivor->CancelRestrictedActions();
}
