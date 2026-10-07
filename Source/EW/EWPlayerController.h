// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWInventoryComponent.h"
#include "EWPlayerController.generated.h"

class UInputMappingContext;
class UInputAction;
class UUserWidget;
class UEWInventoryWidget;
class AEWPickup;
class UEWHotbarWidget;
class UEWSurvivalWidget;
class UEWInteractionComponent;
class UEWInteractionWidget;

/**
 *  Basic PlayerController class for a third person game
 *  Manages input mappings
 */
UCLASS(abstract)
class EW_API AEWPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Inventory|Food")
    void RequestConsumeFood(UEWItemDefinition* Item);
    UFUNCTION(Server, Reliable)
    void ServerConsumeFood(UEWItemDefinition* Item);
    UFUNCTION(Client, Reliable)
    void ClientFoodResult(EEWFoodUseResult Result);
    UFUNCTION(BlueprintCallable, Category="Gathering") void Attack();
    UFUNCTION(Server, Reliable) void ServerAttack(AActor* Target);
    AEWPlayerController();
    UFUNCTION(BlueprintPure, Category="Interaction")
    UEWInteractionComponent* GetInteractionComponent() const { return InteractionComponent; }
    bool IsInventoryOpen() const { return bInventoryInputBlocked; }
    bool UsesControllerPrompts() const { return bControllerPrompts; }
    void RecordInputDevice(const FKey& Key) { if (Key.IsValid()) bControllerPrompts = Key.IsGamepadKey(); }
    bool HasLocalInteractionIntent() const { return bLocalInteractionIntent; }
    UFUNCTION(BlueprintCallable, Category="Interaction") void ReleaseInteraction();
    UFUNCTION(Server, Reliable) void ServerCancelInteraction();
    UFUNCTION(Server, Reliable) void ServerSetInteractionMenuBlocked(bool bBlocked);
    virtual bool InputKey(const FInputKeyEventArgs& Params) override;
    virtual void FlushPressedKeys() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    static int32 HotbarSlotForKey(const FKey& Key, bool bControllerModifier);
    void SetHotbarModifierHeld(bool bHeld) { bHotbarModifierHeld = bHeld; }
    bool IsHotbarModifierHeld() const { return bHotbarModifierHeld; }
    UFUNCTION(BlueprintCallable, Category="Hotbar")
    void RequestHotbarBinding(int32 Slot, UEWItemDefinition* Item);
    UFUNCTION(BlueprintCallable, Category="Hotbar")
    void RequestHotbarActivation(int32 Slot);
    UFUNCTION(Server, Reliable)
    void ServerBindHotbar(int32 Slot, UEWItemDefinition* Item);
    UFUNCTION(Server, Reliable)
    void ServerActivateHotbar(int32 Slot);
    UFUNCTION(Client, Reliable)
    void ClientHotbarResult(EEWHotbarResult Result);
    UFUNCTION(BlueprintCallable, Category="Equipment")
    void RequestEquipItem(UEWItemDefinition* Item, EEWEquipmentSlot Slot);
    UFUNCTION(BlueprintCallable, Category="Equipment")
    void RequestUnequipItem(EEWEquipmentSlot Slot);
    UFUNCTION(Server, Reliable)
    void ServerEquipItem(UEWItemDefinition* Item, EEWEquipmentSlot Slot);
    UFUNCTION(Server, Reliable)
    void ServerUnequipItem(EEWEquipmentSlot Slot);
    UFUNCTION(Client, Reliable)
    void ClientEquipmentResult(EEWEquipmentResult Result);
    /** Local panel lifecycle; no inventory mutation. */
    UFUNCTION(BlueprintCallable, Category="Inventory")
    void SetInventoryOpen(bool bOpen);
    /** Local interaction intent. The owned controller forwards only a target, never item/quantity. */
    UFUNCTION(BlueprintCallable, Category="Interaction")
    void Interact();

    UFUNCTION(Server, Reliable)
    void ServerInteract(AActor* Target);

	/** Explicit editor-only fixture grant. No client RPC or normal-game starting items. */
	UFUNCTION(Exec)
	void EWGrantTestWood(int32 Quantity = 1);
	
protected:
    UPROPERTY(Transient) TObjectPtr<UInputAction> AttackAction;
    UPROPERTY(Transient) TObjectPtr<UInputMappingContext> RuntimeAttackMappingContext;
    double LastHarvestAttackTime = -100;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Interaction")
    TObjectPtr<UEWInteractionComponent> InteractionComponent;
    UPROPERTY(Transient) TObjectPtr<UEWInteractionWidget> InteractionWidget;
    bool bControllerPrompts = false;
    bool bLocalInteractionIntent = false;
    UPROPERTY(Transient)
    TObjectPtr<UEWSurvivalWidget> SurvivalWidget;
    UPROPERTY(Transient)
    TObjectPtr<UEWHotbarWidget> HotbarWidget;
    bool bHotbarModifierHeld = false;
    TSet<FKey> SuppressedHotbarKeys;
    UPROPERTY(EditAnywhere, Category="Input|Interaction")
    TObjectPtr<UInputAction> InteractAction;

    UPROPERTY(Transient)
    TObjectPtr<UInputMappingContext> RuntimeInteractionMappingContext;

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
    bool bInventoryInputBlocked = false;

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

};
