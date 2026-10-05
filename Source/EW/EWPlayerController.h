// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "EWPlayerController.generated.h"

class UInputMappingContext;
class UInputAction;
class UUserWidget;
class UEWInventoryWidget;

/**
 *  Basic PlayerController class for a third person game
 *  Manages input mappings
 */
UCLASS(abstract)
class AEWPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	/** Explicit editor-only fixture grant. No client RPC or normal-game starting items. */
	UFUNCTION(Exec)
	void EWGrantTestWood(int32 Quantity = 1);
	
protected:

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category ="Input|Input Mappings")
	TArray<UInputMappingContext*> DefaultMappingContexts;

	/** Input Mapping Contexts */
	UPROPERTY(EditAnywhere, Category="Input|Input Mappings")
	TArray<UInputMappingContext*> MobileExcludedMappingContexts;

	/** Mobile controls widget to spawn */
	UPROPERTY(EditAnywhere, Category="Input|Touch Controls")
	TSubclassOf<UUserWidget> MobileControlsWidgetClass;

	/** Pointer to the mobile controls widget */
	UPROPERTY()
	TObjectPtr<UUserWidget> MobileControlsWidget;

	/** Toggle action for the native inventory draft. */
	UPROPERTY(EditAnywhere, Category="Input|Inventory")
	TObjectPtr<UInputAction> InventoryAction;

	/** Runtime fallback mapping used until the project has a designer-authored inventory input asset. */
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> RuntimeInventoryMappingContext;

	UPROPERTY(Transient)
	TObjectPtr<UEWInventoryWidget> InventoryWidget;

	/** If true, the player will use UMG touch controls even if not playing on mobile platforms */
	UPROPERTY(EditAnywhere, Config, Category = "Input|Touch Controls")
	bool bForceTouchControls = false;

	/** Gameplay initialization */
	virtual void BeginPlay() override;

	/** Input mapping context setup */
	virtual void SetupInputComponent() override;

	/** Returns true if the player should use UMG touch controls */
	bool ShouldUseTouchControls() const;

	/** Opens or closes the inventory and changes local mouse/input focus. */
	void ToggleInventory();
	void SetInventoryOpen(bool bOpen);

};
