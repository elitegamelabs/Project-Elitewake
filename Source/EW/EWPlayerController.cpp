// Copyright Epic Games, Inc. All Rights Reserved.


#include "EWPlayerController.h"
#include "EWItemSpawnerWidget.h"
#include "EWItemDefinition.h"
#include "Engine/AssetManager.h"
#include "EWCrewMaster.h"
#include "Misc/App.h"
#include "WaterBodyActor.h"
#include "EngineUtils.h"
#include "Ships/EWWreckCrate.h"
#include "Wildlife/EWFish.h"
#include "Wildlife/EWAnimal.h"
#include "EWObjectiveComponent.h"
#include "EWSoundscapeComponent.h"
#include "EWPlacementPreviewComponent.h"
#include "World/EWBuildComponent.h"
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
#include "EWDialogueWidget.h"
#include "EWTownsfolk.h"
#include "EWExplorationComponent.h"
#include "EWCraftingRecipe.h"
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
#include "EWArrivalPromptWidget.h"
#include "EWArrivalComponent.h"
#include "World/EWStrongbox.h"
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
    BuildComponent = CreateDefaultSubobject<UEWBuildComponent>(TEXT("Build"));
    ExplorationComponent = CreateDefaultSubobject<UEWExplorationComponent>(TEXT("Exploration"));
    Strongbox = CreateDefaultSubobject<UEWInventoryComponent>(TEXT("Strongbox"));
    Strongbox->MaxSlots = StrongboxSlots;
}

namespace
{
    const TCHAR* LookSensitivityKeys[4] = {TEXT("MouseHorizontalSensitivity"), TEXT("MouseVerticalSensitivity"),
        TEXT("ControllerHorizontalSensitivity"), TEXT("ControllerVerticalSensitivity")};
}

void AEWPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    if (ObjectiveComponent) ObjectiveComponent->ApplyCompletionRecipes();
}

void AEWPlayerController::BeginPlay()
{
	Super::BeginPlay();
    if (GConfig)
    {
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("BrightnessGamma"), UserBrightness, GGameUserSettingsIni);
        // Each look speed falls back on the one setting it replaced (October 30: one mouse and one controller speed before).
        float OldMouse = 1.f, OldController = 1.f;
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("MouseLookSensitivity"), OldMouse, GGameUserSettingsIni);
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("ControllerLookSensitivity"), OldController, GGameUserSettingsIni);
        for (int32 Which = 0; Which < 4; ++Which)
        {
            LookSensitivity[Which] = Which < 2 ? OldMouse : OldController;
            GConfig->GetFloat(TEXT("Elitewake.UserControls"), LookSensitivityKeys[Which], LookSensitivity[Which], GGameUserSettingsIni);
            LookSensitivity[Which] = FMath::Clamp(LookSensitivity[Which], .1f, 3.f);
        }
        GConfig->GetFloat(TEXT("Elitewake.UserControls"), TEXT("MasterVolume"), MasterVolume, GGameUserSettingsIni);
        int32 Icons = 0;
        GConfig->GetInt(TEXT("Elitewake.UserControls"), TEXT("ButtonIcons"), Icons, GGameUserSettingsIni);
        ButtonIconsChoice = static_cast<EEWButtonIconsChoice>(FMath::Clamp(Icons, 0, 2));
        MasterVolume = FMath::Clamp(MasterVolume, 0.f, 1.f);
        if (IsLocalPlayerController()) FApp::SetVolumeMultiplier(MasterVolume);
        UserBrightness = FMath::Clamp(UserBrightness, -.5f, .5f);
    }
    ApplyBrightness();
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
        ArrivalPromptWidget = CreateWidget<UEWArrivalPromptWidget>(this, UEWArrivalPromptWidget::StaticClass());
        if (ArrivalPromptWidget) ArrivalPromptWidget->AddToPlayerScreen(3);
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
    ApplyBrightness();
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), TEXT("BrightnessGamma"), UserBrightness, GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

float AEWPlayerController::GetDisplayGamma() const { return GEngine ? GEngine->DisplayGamma : 2.2f; }

void AEWPlayerController::ApplyBrightness() const
{
    // Display gamma brightens or darkens the final image of every view (survivor, helm, cannon, title) together:
    // 50 on the slider is the engine's 2.2. Tuning: the ends are one stop of gamma either way.
    if (GEngine && IsLocalPlayerController()) GEngine->DisplayGamma = 2.2f * FMath::Exp2(UserBrightness * 2.f);
}

void AEWPlayerController::SetLookSensitivity(int32 Which, float Value)
{
    if (!IsLocalPlayerController() || Which < 0 || Which > 3) return;
    LookSensitivity[Which] = FMath::Clamp(Value, .1f, 3.f);
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), LookSensitivityKeys[Which], LookSensitivity[Which], GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

EEWGamepadFamily AEWPlayerController::GetGamepadFamily() const
{
    return FEWControllerIcons::Resolve(ButtonIconsChoice,
        ButtonIconsChoice == EEWButtonIconsChoice::Automatic ? FEWControllerIcons::DetectConnected() : EEWGamepadFamily::Unknown);
}

void AEWPlayerController::SetButtonIconsChoice(EEWButtonIconsChoice Choice, bool bRemember)
{
    ButtonIconsChoice = static_cast<EEWButtonIconsChoice>(FMath::Clamp(int32(Choice), 0, 2));
    if (bRemember && GConfig && IsLocalPlayerController())
    {
        GConfig->SetInt(TEXT("Elitewake.UserControls"), TEXT("ButtonIcons"), int32(ButtonIconsChoice), GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

void AEWPlayerController::SetMasterVolume(float Value)
{
    if (!IsLocalPlayerController()) return;
    MasterVolume = FMath::Clamp(Value, 0.f, 1.f);
    FApp::SetVolumeMultiplier(MasterVolume);
    if (GConfig)
    {
        GConfig->SetFloat(TEXT("Elitewake.UserControls"), TEXT("MasterVolume"), MasterVolume, GGameUserSettingsIni);
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
    // At a helm, or at a sail's lines, holding Up/Down (or the D-pad) raises/lowers sail one 25% step at a time.
    if (Survivor->GetHelmShip() || Survivor->GetLinesShip())
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
    // Owner, November 1: slots 1-4 on the d-pad (left, up, right, down); 5-8 on LB with X, Y, B, A.
    static const FKey Numbers[] = {EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight};
    static const FKey ControllerKeys[] = {EKeys::Gamepad_DPad_Left,EKeys::Gamepad_DPad_Up,
        EKeys::Gamepad_DPad_Right,EKeys::Gamepad_DPad_Down,
        EKeys::Gamepad_FaceButton_Left,EKeys::Gamepad_FaceButton_Top,
        EKeys::Gamepad_FaceButton_Right,EKeys::Gamepad_FaceButton_Bottom};
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
        if (Key==Numbers[i] || (i < 4 && Key==ControllerKeys[i]) || (i >= 4 && bControllerModifier && Key==ControllerKeys[i])) return i;
    return INDEX_NONE;
}

bool AEWPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
    // LB is the controller's modifier (hotbar 5-8, LB + d-pad right for Build Mode): know whether it is down whatever else
    // takes the key, so a press or release in a menu never leaves it stuck.
    if (Params.Key==EKeys::Gamepad_LeftShoulder)
    {
        if (Params.Event==IE_Pressed) bHotbarModifierHeld=true;
        if (Params.Event==IE_Released) bHotbarModifierHeld=false;
    }
    if (Params.Key==EKeys::F10)
    {
        if (Params.Event==IE_Pressed) SetSessionMenuOpen(!IsSessionMenuOpen());
        return true;
    }
    if (IsSessionMenuOpen() || IsOptionsMenuOpen()) return true;
#if !UE_BUILD_SHIPPING
    // Testing phase only: F9 opens the item spawner (owner, October 30).
    if (Params.Key == EKeys::F9)
    {
        if (Params.Event == IE_Pressed) SetItemSpawnerOpen(!IsItemSpawnerOpen());
        return true;
    }
#endif
    if (IsItemSpawnerOpen()) return true;
    // Build Mode takes B / LB + d-pad right to enter; while it is on, its own keys too (UEWBuildComponent::ResolveKey).
    if (IsLocalPlayerController() && !bMapOpen && (!InventoryWidget || !InventoryWidget->IsInViewport()) && BuildComponent
        && BuildComponent->HandleKey(Params, bHotbarModifierHeld)) return true;
    // At a cannon, Right Mouse (or LB) marks the ship it is laid on for the hired gunners, or clears the mark (owner, October 18).
    if (Params.Event == IE_Pressed && (Params.Key == EKeys::RightMouseButton || Params.Key == EKeys::Gamepad_LeftShoulder) && !bMapOpen)
        if (auto* Gunner = Cast<AEWCharacter>(GetPawn()); Gunner && Gunner->GetGunShip()) { Gunner->ServerMarkTarget(); return true; }
#if !UE_BUILD_SHIPPING
    // Testing phase only: Shift + 1 to 5 teleports to a region (owner, October 24), Shift + 6 to the nearest Port (owner, October 30).
    // Compiled out of shipping builds.
    if (Params.Event==IE_Pressed && (IsInputKeyDown(EKeys::LeftShift) || IsInputKeyDown(EKeys::RightShift)))
    {
        static const FKey RegionKeys[] = {EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five};
        for (int32 i=0; i<5; ++i) if (Params.Key==RegionKeys[i]) { ServerDebugTeleportToRegion(i); return true; }
        if (Params.Key==EKeys::Six) { ServerDebugTeleportToPort(); return true; }
    }
#endif
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
    // M opens and closes the map; on a controller the Back / View button does, and B closes it.
    if (Params.Key == EKeys::M || Params.Key == EKeys::Gamepad_Special_Left || (bMapOpen && Params.Key == EKeys::Gamepad_FaceButton_Right))
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
    if (BuildComponent) BuildComponent->ForgetHeldKeys();
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
void AEWPlayerController::FinishCraft()
{
    UEWCraftingRecipe* Recipe = CraftingRecipe;
    CraftingRecipe = nullptr;
    GetWorldTimerManager().ClearTimer(CraftTimer);
    auto* Crafter = Cast<AEWCharacter>(GetPawn());
    // A survivor who died, or whose menu or map was taken away, gets nothing and loses nothing.
    if (!Recipe || !Crafter || Crafter->IsDead()) { ClientCraftResult(EEWCraftResult::Busy); return; }
    const EEWCraftResult Result = Crafter->GetInventoryComponent()->CraftItem(Recipe);
    if (Result == EEWCraftResult::Success && Crafter->GetProgressionComponent()) Crafter->GetProgressionComponent()->Award(EEWExperienceSource::Craft);
    ClientCraftResult(Result);
}

void AEWPlayerController::ClientCraftStarted_Implementation(UEWCraftingRecipe* Recipe, float Seconds)
{
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowCraftStarted(Recipe, Seconds);
}

void AEWPlayerController::ServerUnlockSkill_Implementation(FName Id)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (Survivor && Survivor->GetProgressionComponent() && !Survivor->IsDead()) Survivor->GetProgressionComponent()->UnlockSkill(Id);
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

void AEWPlayerController::ServerDebugTeleportToRegion_Implementation(int32 RegionIndex)
{
#if !UE_BUILD_SHIPPING
    // Island centres from Scripts/Setup/world_layout.py (cm): Starter (Plains), Jungle1, Desert1, Swamp1, Winter1.
    static const FVector2D Centres[] = {FVector2D(-800.f, -100.f), FVector2D(-380000.f, 20000.f), FVector2D(280000.f, -30000.f), FVector2D(-30000.f, -270000.f), FVector2D(-60000.f, 280000.f)};
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || Survivor->IsDead() || RegionIndex < 0 || RegionIndex >= 5 || !GetWorld()) return;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWDebugTeleport), false, Survivor);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    // Dry ground nearest the island's centre: the centre itself, then rings round it (a swamp's middle can lie under water).
    static const float Radii[] = {0.f, 4000.f, 9000.f, 16000.f, 25000.f, 36000.f, 50000.f};
    const FVector2D Centre = Centres[RegionIndex];
    FVector Spot(Centre.X, Centre.Y, 500.f);
    bool bFound = false;
    for (const float Radius : Radii)
    {
        for (int32 Step = 0; Step < (Radius <= 0.f ? 1 : 12) && !bFound; ++Step)
        {
            const float Angle = Step * (PI / 6.f);
            const FVector From(Centre.X + FMath::Cos(Angle) * Radius, Centre.Y + FMath::Sin(Angle) * Radius, 100000.f);
            FHitResult Hit;
            if (GetWorld()->LineTraceSingleByObjectType(Hit, From, From - FVector(0.f, 0.f, 300000.f), FCollisionObjectQueryParams(ECC_WorldStatic), Query) && Hit.ImpactPoint.Z > -40.f)
            {
                Spot = FVector(From.X, From.Y, Hit.ImpactPoint.Z + 120.f);
                bFound = true;
            }
        }
        if (bFound) break;
    }
    Survivor->TeleportTo(Spot, Survivor->GetActorRotation(), false, true);
#endif
}

void AEWPlayerController::SetItemSpawnerOpen(bool bOpen)
{
#if !UE_BUILD_SHIPPING
    if (!IsLocalPlayerController() || IsItemSpawnerOpen() == bOpen) return;
    if (bOpen) { SetMapOpen(false); SetInventoryOpen(false); SetOptionsMenuOpen(false); SetSessionMenuOpen(false); }
    FlushPressedKeys();
    SetIgnoreMoveInput(bOpen); SetIgnoreLookInput(bOpen);
    if (bOpen)
    {
        ItemSpawnerWidget = CreateWidget<UEWItemSpawnerWidget>(this, UEWItemSpawnerWidget::StaticClass());
        if (ItemSpawnerWidget)
        {
            ItemSpawnerWidget->AddToPlayerScreen(105);
            FInputModeUIOnly Mode; Mode.SetWidgetToFocus(ItemSpawnerWidget->TakeWidget()); SetInputMode(Mode);
        }
    }
    else { if (ItemSpawnerWidget) ItemSpawnerWidget->RemoveFromParent(); ItemSpawnerWidget = nullptr; SetInputMode(FInputModeGameOnly()); }
    bShowMouseCursor = bOpen;
#endif
}

void AEWPlayerController::ServerDebugGiveItem_Implementation(UEWItemDefinition* Item)
{
#if !UE_BUILD_SHIPPING
    // Only an item of the game's item list, to a living survivor; one at a time.
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Item || !Survivor || Survivor->IsDead() || !Survivor->GetInventoryComponent()) return;
    if (!UAssetManager::Get().GetPrimaryAssetPath(Item->GetPrimaryAssetId()).IsValid()) return;
    Survivor->GetInventoryComponent()->AddItem(Item, 1);
#endif
}

void AEWPlayerController::ServerDebugTeleportToPort_Implementation()
{
#if !UE_BUILD_SHIPPING
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || Survivor->IsDead() || !GetWorld()) return;
    // The nearest Port's general merchant (not a crew master): stand on the plaza in front of them, facing them.
    const AEWMerchant* Nearest = nullptr;
    for (TActorIterator<AEWMerchant> It(GetWorld()); It; ++It)
    {
        if (It->IsA<AEWCrewMaster>()) continue;
        if (!Nearest || FVector::DistSquared(It->GetActorLocation(), Survivor->GetActorLocation())
            < FVector::DistSquared(Nearest->GetActorLocation(), Survivor->GetActorLocation())) Nearest = *It;
    }
    if (!Nearest) return;
    const FVector Spot = Nearest->GetActorLocation() + Nearest->GetActorForwardVector() * 220.f + FVector(0.f, 0.f, 110.f);
    const FRotator Facing(0.f, (-Nearest->GetActorForwardVector()).Rotation().Yaw, 0.f);
    Survivor->TeleportTo(Spot, Facing, false, true);
    SetControlRotation(Facing);
    ClientSetRotation(Facing);
#endif
}

void AEWPlayerController::ServerCraft_Implementation(UEWCraftingRecipe* Recipe)
{
    auto* OwnedCrafter = Cast<AEWCharacter>(GetPawn());
    if (IsMapOpen() || IsSessionMenuOpen() || !OwnedCrafter || OwnedCrafter->GetController() != this || OwnedCrafter->GetSurvivalComponent()->GetHealth() <= 0.f)
    { ClientCraftResult(EEWCraftResult::Busy); return; }
    if (CraftingRecipe) { ClientCraftResult(EEWCraftResult::Busy); return; }
    // Checked now so a craft that cannot succeed never starts, and again when it finishes: the materials are used up only on completion.
    const EEWCraftResult Ready = OwnedCrafter->GetInventoryComponent()->GetCraftReadiness(Recipe);
    if (Ready != EEWCraftResult::Success) { ClientCraftResult(Ready); return; }
    CraftingRecipe = Recipe;
    const float Seconds = Recipe->CraftSeconds;
    ClientCraftStarted(Recipe, Seconds);
    if (Seconds <= .02f) FinishCraft();
    else GetWorldTimerManager().SetTimer(CraftTimer, this, &AEWPlayerController::FinishCraft, Seconds, false);
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
    if (ArrivalPromptWidget) ArrivalPromptWidget->RemoveFromParent();
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

void AEWPlayerController::OpenDialogue(AEWTownsfolk* Speaker)
{
    if (!IsLocalPlayerController() || !IsValid(Speaker) || IsMapOpen() || IsSessionMenuOpen()) return;
    if (IsInventoryOpen()) SetInventoryOpen(false);
    SetMenuInputBlocked(true);
    DialogueSpeaker = Speaker;
    if (!DialogueWidget) DialogueWidget = CreateWidget<UEWDialogueWidget>(this, UEWDialogueWidget::StaticClass());
    if (!DialogueWidget) return;
    if (!DialogueWidget->IsInViewport()) DialogueWidget->AddToPlayerScreen(25);
    DialogueWidget->SetSpeaker(Speaker);
    FInputModeUIOnly InputMode;
    InputMode.SetWidgetToFocus(DialogueWidget->TakeWidget());
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(InputMode);
    SetShowMouseCursor(true);
    DialogueWidget->SetUserFocus(this);
}

void AEWPlayerController::CloseDialogue()
{
    if (!IsLocalPlayerController()) return;
    const bool bWasOpen = IsDialogueOpen();
    DialogueSpeaker = nullptr;
    if (DialogueWidget && DialogueWidget->IsInViewport()) DialogueWidget->RemoveFromParent();
    if (!bWasOpen) return;
    SetMenuInputBlocked(false);
    SetInputMode(FInputModeGameOnly());
    SetShowMouseCursor(false);
}

bool AEWPlayerController::IsDialogueOpen() const
{
    return DialogueWidget && DialogueWidget->IsInViewport();
}

void AEWPlayerController::ClientOpenDialogue_Implementation(AEWTownsfolk* Speaker)
{
    OpenDialogue(Speaker);
}

void AEWPlayerController::ServerChooseDialogue_Implementation(AEWTownsfolk* Speaker, FName Key)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || !IsValid(Speaker) || Speaker->GetWorld() != GetWorld()) return;
    const FText Reply = Speaker->ChooseDialogue(Survivor, Key);
    LastDialogueReply = Reply;
    ClientDialogueReply(Speaker, Reply);
}

void AEWPlayerController::ClientDialogueReply_Implementation(AEWTownsfolk* Speaker, const FText& Reply)
{
    LastDialogueReply = Reply;
    if (DialogueWidget && DialogueWidget->IsInViewport() && DialogueSpeaker == Speaker) DialogueWidget->ShowReply(Reply);
}

void AEWPlayerController::ServerTransferContainerItem_Implementation(AActor* Container, bool bToContainer, int32 EntryIndex, int32 Quantity)
{
    auto* Survivor = Cast<AEWCharacter>(GetPawn());
    if (!Survivor || !IsValid(Container) || Container->GetWorld() != GetWorld() || !FEWContainerAccess::CanAccess(Container, Survivor)) return;
    UEWInventoryComponent* Carried = Survivor->GetInventoryComponent();
    UEWInventoryComponent* Hold = FEWContainerAccess::Inventory(Container, Survivor);
    if (!Carried || !Hold) return;
    if (bToContainer)
    {
        // Putting something in the strongbox is the town's storage step (Phase 1 slice 5).
        if (Carried->TransferEntryTo(Hold, EntryIndex, Quantity) > 0)
            if (auto* Arrival = Survivor->GetArrivalComponent())
            {
                if (Cast<AEWStrongbox>(Container)) Arrival->NoteTownStep(EEWTownStep::Store);
                // Loading her own boat's hold is the voyage's provisions step (slice 6) once it holds enough.
                if (const auto* Ship = Cast<AEWShip>(Container)) Arrival->NoteHoldLoaded(Ship);
            }
    }
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
