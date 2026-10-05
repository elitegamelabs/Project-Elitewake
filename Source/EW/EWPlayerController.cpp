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
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Engine/AssetManager.h"
#include "Widgets/Input/SVirtualJoystick.h"

void AEWPlayerController::BeginPlay()
{
	Super::BeginPlay();

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

	// Milestone 5 fallback: create an Enhanced Input action in code so the draft works
	// immediately. A designer-authored IA_Inventory asset can be assigned later.
	if (!InventoryAction)
	{
		InventoryAction = NewObject<UInputAction>(this, TEXT("IA_Inventory_Runtime"));
		InventoryAction->ValueType = EInputActionValueType::Boolean;
		RuntimeInventoryMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Inventory_Runtime"));
		RuntimeInventoryMappingContext->MapKey(InventoryAction, EKeys::I);
	}

	if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(InputComponent))
	{
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

		FInputModeGameAndUI InputMode;
		InputMode.SetHideCursorDuringCapture(false);
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		SetInputMode(InputMode);
		SetShowMouseCursor(true);
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
