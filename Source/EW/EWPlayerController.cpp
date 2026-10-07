// Copyright Epic Games, Inc. All Rights Reserved.


#include "EWPlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedInputComponent.h"
#include "Engine/LocalPlayer.h"
#include "InputAction.h"
#include "InputCoreTypes.h"
#include "InputMappingContext.h"
#include "Blueprint/UserWidget.h"
#include "EW.h"
#include "EWInventoryWidget.h"
#include "EWHotbarWidget.h"
#include "EWSurvivalWidget.h"
#include "InputKeyEventArgs.h"
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
    InteractionComponent = CreateDefaultSubobject<UEWInteractionComponent>(TEXT("Interaction"));
}

void AEWPlayerController::BeginPlay()
{
	Super::BeginPlay();
    if (IsLocalPlayerController())
    {
        HotbarWidget = CreateWidget<UEWHotbarWidget>(this, UEWHotbarWidget::StaticClass());
        if (HotbarWidget) HotbarWidget->AddToPlayerScreen(1);
        SurvivalWidget = CreateWidget<UEWSurvivalWidget>(this, UEWSurvivalWidget::StaticClass());
        if (SurvivalWidget) SurvivalWidget->AddToPlayerScreen(2);
        InteractionWidget = CreateWidget<UEWInteractionWidget>(this, UEWInteractionWidget::StaticClass());
        if (InteractionWidget) InteractionWidget->AddToPlayerScreen(3);
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

void AEWPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

    AttackAction = NewObject<UInputAction>(this, TEXT("IA_Attack_Runtime"));
    AttackAction->ValueType = EInputActionValueType::Boolean;
    RuntimeAttackMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Attack_Runtime"));
    RuntimeAttackMappingContext->MapKey(AttackAction, EKeys::LeftMouseButton);
    RuntimeAttackMappingContext->MapKey(AttackAction, EKeys::Gamepad_RightTrigger);

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

void AEWPlayerController::Attack()
{
    if (!IsLocalPlayerController() || IsInventoryOpen()) return;
    ServerAttack(FEWInteractionTargeting::FindTarget(Cast<AEWCharacter>(GetPawn())));
}

void AEWPlayerController::ServerAttack_Implementation(AActor* Target)
{
    const double Now = GetWorld()->GetTimeSeconds();
    // Per-controller admission, across targets. One-second interval is draft tool tuning.
    if (Now - LastHarvestAttackTime < 1.) return;
    LastHarvestAttackTime = Now;
    if (InteractionComponent->IsMenuBlocked() || InteractionComponent->GetHoldState().Target) return;
    if (auto* Tree = Cast<AEWHarvestTree>(Target)) Tree->TryHarvest(Cast<AEWCharacter>(GetPawn()));
    else if (auto* Node = Cast<AEWMineable>(Target)) Node->TryMine(Cast<AEWCharacter>(GetPawn()));
}

void AEWPlayerController::Interact()
{
    if (!IsLocalPlayerController() || (InventoryWidget && InventoryWidget->IsInViewport())) return;
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
    InteractionComponent->SetMenuBlocked(bBlocked);
}

int32 AEWPlayerController::HotbarSlotForKey(const FKey& Key, bool bControllerModifier)
{
    static const FKey Numbers[] = {EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight};
    static const FKey ControllerKeys[] = {EKeys::Gamepad_FaceButton_Bottom,EKeys::Gamepad_FaceButton_Right,
        EKeys::Gamepad_FaceButton_Left,EKeys::Gamepad_FaceButton_Top,
        EKeys::Gamepad_DPad_Up,EKeys::Gamepad_DPad_Right,EKeys::Gamepad_DPad_Down,EKeys::Gamepad_DPad_Left};
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
        if (Key==Numbers[i] || (bControllerModifier && Key==ControllerKeys[i])) return i;
    return INDEX_NONE;
}

bool AEWPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
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
        if (Slot!=INDEX_NONE && Params.Event==IE_Pressed)
        {
            // Consume the complete chord, including releases after LB is released, before Enhanced Input.
            SuppressedHotbarKeys.Add(Params.Key);
            RequestHotbarActivation(Slot);
            return true;
        }
        if (Slot!=INDEX_NONE && Params.Event==IE_Repeat) return true;
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
    if (IsLocalPlayerController()) ServerBindHotbar(Slot,Item);
}
void AEWPlayerController::RequestHotbarActivation(int32 Slot)
{
    if (IsLocalPlayerController() && (!InventoryWidget || !InventoryWidget->IsInViewport())) ServerActivateHotbar(Slot);
}
void AEWPlayerController::ServerBindHotbar_Implementation(int32 Slot, UEWItemDefinition* Item)
{
    auto* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientHotbarResult(OwnedCharacter && OwnedCharacter->GetController()==this
        ? OwnedCharacter->GetHotbarComponent()->BindItem(Slot,Item) : EEWHotbarResult::NotOwned);
}
void AEWPlayerController::ServerActivateHotbar_Implementation(int32 Slot)
{
    auto* OwnedCharacter = Cast<AEWCharacter>(GetPawn());
    ClientHotbarResult(OwnedCharacter && OwnedCharacter->GetController()==this
        ? OwnedCharacter->GetHotbarComponent()->ActivateSlot(Slot) : EEWHotbarResult::NotOwned);
}
void AEWPlayerController::ClientHotbarResult_Implementation(EEWHotbarResult Result)
{
    if (HotbarWidget) HotbarWidget->ShowResult(Result);
    if (InventoryWidget && InventoryWidget->IsInViewport()) InventoryWidget->ShowHotbarResult(Result);
}
void AEWPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bHotbarModifierHeld=false; SuppressedHotbarKeys.Reset();
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
	SetInventoryOpen(!InventoryWidget || !InventoryWidget->IsInViewport());
}

void AEWPlayerController::SetInventoryOpen(bool bOpen)
{
	if (!IsLocalPlayerController())
	{
		return;
	}

    if (bInventoryInputBlocked != bOpen)
    {
        ServerSetInteractionMenuBlocked(bOpen);
        FlushPressedKeys();
        SetIgnoreMoveInput(bOpen);
        SetIgnoreLookInput(bOpen);
        bInventoryInputBlocked = bOpen;
        if (bOpen && GetPawn()) GetPawn()->ConsumeMovementInputVector();
    }

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
