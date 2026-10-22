// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWInventoryComponent.h"
#include "EWProgressionComponent.h"
#include "Characters/EWAppearance.h"
#include "EWWorkFeedback.h"
#include "EWPlayerController.generated.h"

class UInputMappingContext;
class UInputAction;
class UUserWidget;
class UEWInventoryWidget;
class AEWPickup;
class UEWHotbarWidget;
class UEWSurvivalWidget;
class UEWDeathWidget;
class UEWInteractionComponent;
class UEWInteractionWidget;
class UEWShipMarkersWidget;
class UEWCompassWidget;
class UEWObjectiveComponent;
class UEWObjectiveWidget;
class UEWMapWidget;
class UEWSessionWidget;
class UEWOptionsWidget;
class UEWHitMarkerWidget;
class UEWCompanyComponent;
class UEWContainerWidget;
class UEWSoundscapeComponent;
class UEWPlacementPreviewComponent;

/**
 *  Basic PlayerController class for a third person game
 *  Manages input mappings
 */
UCLASS(abstract)
class EW_API AEWPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
    /** Owner: asks the server to dress this player's survivor in a look (from the character creator). */
    UFUNCTION(BlueprintCallable, Category="Appearance")
    void RequestAppearance(const FEWAppearance& Appearance);
    UFUNCTION(Server, Reliable)
    void ServerSetAppearance(const FEWAppearance& Appearance);
    /** Sends the look chosen at the title, once this controller has its survivor. */
    virtual void AcknowledgePossession(APawn* P) override;
    UFUNCTION(BlueprintPure, Category="Company") UEWCompanyComponent* GetCompanyComponent() const { return CompanyComponent; }
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Company") TObjectPtr<UEWCompanyComponent> CompanyComponent;
    UFUNCTION(BlueprintCallable, Category="Multiplayer") void SetSessionMenuOpen(bool bOpen);
    UFUNCTION(BlueprintPure, Category="Multiplayer") bool IsSessionMenuOpen() const { return bSessionMenuOpen; }
    UFUNCTION(Server, Reliable) void ServerSetSessionMenuOpen(bool bOpen);
    UPROPERTY(Transient) TObjectPtr<UEWSessionWidget> SessionWidget;
    bool bSessionMenuOpen = false;
    /** Escape's OPTIONS menu. In single player it pauses the world. */
    UFUNCTION(BlueprintCallable, Category="Options") void SetOptionsMenuOpen(bool bOpen);
    UFUNCTION(BlueprintPure, Category="Options") float GetUserBrightness() const { return UserBrightness; }
    UFUNCTION(BlueprintCallable, Category="Options") void SetUserBrightness(float Value);
    UFUNCTION(BlueprintPure, Category="Options") float GetMouseLookSensitivity() const { return MouseLookSensitivity; }
    UFUNCTION(BlueprintCallable, Category="Options") void SetMouseLookSensitivity(float Value);
    UFUNCTION(BlueprintPure, Category="Options") float GetControllerLookSensitivity() const { return ControllerLookSensitivity; }
    UFUNCTION(BlueprintCallable, Category="Options") void SetControllerLookSensitivity(float Value);
    float GetActiveLookSensitivity() const { return bControllerPrompts ? ControllerLookSensitivity : MouseLookSensitivity; }
    UFUNCTION(BlueprintPure, Category="Options") bool IsOptionsMenuOpen() const { return bOptionsMenuOpen; }
    UFUNCTION(BlueprintPure, Category="Options") UEWOptionsWidget* GetOptionsWidget() const { return OptionsWidget; }
    UFUNCTION(Server, Reliable) void ServerSetOptionsMenuOpen(bool bOpen);
    /** SAVE GAME: single player only (multiplayer has no manual save); writes this survivor to the save slot. */
    UFUNCTION(BlueprintCallable, Category="Options") bool SaveSurvivorGame();
    /** MAIN MENU: leaves this world (and any session) for the ELITEWAKE title screen. */
    UFUNCTION(BlueprintCallable, Category="Options") void ReturnToMainMenu();
    UPROPERTY(Transient) TObjectPtr<UEWOptionsWidget> OptionsWidget;
    /** The striker's hit marker and what blows and gathers gave. */
    void ShowWorkHit(bool bGave, const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal);
    void ShowGains(const TArray<FEWGatherGain>& Gains);
    UFUNCTION(BlueprintPure, Category="Gathering") UEWHitMarkerWidget* GetHitMarkerWidget() const { return HitMarkerWidget; }
    UPROPERTY(Transient) TObjectPtr<UEWHitMarkerWidget> HitMarkerWidget;
    bool bOptionsMenuOpen = false;
    UFUNCTION(BlueprintPure, Category="Objectives")
    UEWObjectiveComponent* GetObjectiveComponent() const { return ObjectiveComponent; }
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Objectives")
    TObjectPtr<UEWObjectiveComponent> ObjectiveComponent;
    /** The surf, wind and seabirds this player hears. */
    UFUNCTION(BlueprintPure, Category="Sound") UEWSoundscapeComponent* GetSoundscapeComponent() const { return SoundscapeComponent; }
    /** Where a carried placeable would go: blue if it can be placed there, red if not (owner, October 17). */
    UFUNCTION(BlueprintPure, Category="Placement") UEWPlacementPreviewComponent* GetPlacementPreview() const { return PlacementPreview; }
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Sound")
    TObjectPtr<UEWSoundscapeComponent> SoundscapeComponent;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Placement")
    TObjectPtr<UEWPlacementPreviewComponent> PlacementPreview;
    UPROPERTY(Transient)
    TObjectPtr<UEWObjectiveWidget> ObjectiveWidget;
    UFUNCTION(BlueprintCallable, Category="Inventory|Crafting")
    void RequestCraft(UEWCraftingRecipe* Recipe);
    UFUNCTION(Server, Reliable) void ServerCraft(UEWCraftingRecipe* Recipe);
    /** The dead survivor chooses to respawn (owner, October 22): the server drops their bag where they fell and brings them back at a safe place away from it. */
    void RequestRespawn() { ServerRequestRespawn(); }
    UFUNCTION(Server, Reliable) void ServerRequestRespawn();
    /** Spends one of the survivor's unspent stat points on a stat (one point per level; owner, October 22). */
    void RequestSpendStatPoint(EEWStat Stat) { if (IsLocalPlayerController()) ServerSpendStatPoint(Stat); }
    UFUNCTION(Server, Reliable) void ServerSpendStatPoint(EEWStat Stat);
    /** Lights a star of the constellation tree with skill points (owner, October 22). */
    void RequestUnlockSkill(FName Id) { if (IsLocalPlayerController()) ServerUnlockSkill(Id); }
    UFUNCTION(Server, Reliable) void ServerUnlockSkill(FName Id);
    UFUNCTION(BlueprintPure, Category="Death") UEWDeathWidget* GetDeathWidget() const { return DeathWidget; }
    UFUNCTION(Client, Reliable) void ClientCraftResult(EEWCraftResult Result);
    /** The server accepted the recipe: the work takes this long. */
    UFUNCTION(Client, Reliable) void ClientCraftStarted(UEWCraftingRecipe* Recipe, float Seconds);
    /** Server: true while a craft is under way (one at a time). */
    UFUNCTION(BlueprintPure, Category="Crafting") bool IsCraftingNow() const { return CraftingRecipe != nullptr; }
    UFUNCTION(BlueprintCallable, Category="Inventory|Food")
    void RequestConsumeFood(UEWItemDefinition* Item);
    UFUNCTION(Server, Reliable)
    void ServerConsumeFood(UEWItemDefinition* Item);
    UFUNCTION(Client, Reliable)
    void ClientFoodResult(EEWFoodUseResult Result);
    UFUNCTION(BlueprintCallable, Category="Gathering") void Attack();
    UFUNCTION(Server, Reliable) void ServerAttack(AActor* Target, int32 Variant);
    AEWPlayerController();
    virtual void OnPossess(APawn* InPawn) override;
    UFUNCTION(BlueprintPure, Category="Interaction")
    UEWInteractionComponent* GetInteractionComponent() const { return InteractionComponent; }
    UFUNCTION(BlueprintCallable, Category="Map") void SetMapOpen(bool bOpen);
    UFUNCTION(BlueprintPure, Category="Map") bool IsMapOpen() const { return bMapOpen; }
    UFUNCTION(Server, Reliable) void ServerSetMapOpen(bool bOpen);
    UPROPERTY(Transient) TObjectPtr<UEWMapWidget> MapWidget;
    bool bMapOpen = false;
    /** True while a menu screen (inventory or a container) blocks gameplay input. */
    UFUNCTION(BlueprintPure, Category="Inventory")
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
    /** Local panel lifecycle; no inventory mutation. Closing also closes an open container screen. */
    UFUNCTION(BlueprintCallable, Category="Inventory")
    void SetInventoryOpen(bool bOpen);
    /** Local container screen (a ship's hold) beside the survivor's inventory. Null closes it. */
    UFUNCTION(BlueprintCallable, Category="Inventory|Container")
    void SetContainerOpen(AActor* Container);
    UFUNCTION(BlueprintPure, Category="Inventory|Container")
    AActor* GetOpenContainer() const { return OpenContainer; }
    /** Sent by the server once it has agreed this player may use the container. */
    UFUNCTION(Client, Reliable)
    void ClientOpenContainer(AActor* Container);
    /** Owned request to move one stack between the survivor's inventory and a container. The server checks
     *  the survivor can reach the container and moves only what fits. */
    UFUNCTION(Server, Reliable)
    void ServerTransferContainerItem(AActor* Container, bool bToContainer, int32 EntryIndex, int32 Quantity);
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
    UPROPERTY(Transient) TObjectPtr<UInputAction> ClimbUpAction;
    UPROPERTY(Transient) TObjectPtr<UInputAction> ClimbDownAction;
    /** At the helm only: Left/Right Arrow or LB/RB swing the sails (owner, October 16). */
    UPROPERTY(Transient) TObjectPtr<UInputAction> SailLeftAction;
    UPROPERTY(Transient) TObjectPtr<UInputAction> SailRightAction;
    void SailLeft() { SetSailInput(-1.f); }
    void SailRight() { SetSailInput(1.f); }
    void SailStop() { SetSailInput(0.f); }
    void SetSailInput(float Direction);
    void ClimbUp() { SetClimbInput(1.f); }
    void ClimbDown() { SetClimbInput(-1.f); }
    void ClimbStop() { SetClimbInput(0.f); }
    void SetClimbInput(float Direction);
    UPROPERTY(Transient) TObjectPtr<UInputMappingContext> RuntimeAttackMappingContext;
    double LastHarvestAttackTime = -100;
    /** The owner's own swing pacing, so it never shows a swing the server would refuse. */
    double LastLocalAttackTime = -100;
    int32 AttackVariant = 0;
    /** One swing a second: the draft tool pace, now for every swing (tuning). */
    static constexpr double AttackInterval = 1.0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Interaction")
    TObjectPtr<UEWInteractionComponent> InteractionComponent;
    UPROPERTY(Transient) TObjectPtr<UEWInteractionWidget> InteractionWidget;
    UPROPERTY(Transient) TObjectPtr<UEWShipMarkersWidget> ShipMarkersWidget;
    UPROPERTY(Transient) TObjectPtr<UEWCompassWidget> CompassWidget;
    bool bControllerPrompts = false;
    float UserBrightness = 0.f;
    float MouseLookSensitivity = 1.f;
    float ControllerLookSensitivity = 1.f;
    bool bLocalInteractionIntent = false;
    UPROPERTY(Transient)
    TObjectPtr<UEWSurvivalWidget> SurvivalWidget;
    UPROPERTY(Transient)
    TObjectPtr<UEWCraftingRecipe> CraftingRecipe;
    FTimerHandle CraftTimer;
    void FinishCraft();
    UPROPERTY(Transient)
    TObjectPtr<UEWDeathWidget> DeathWidget;
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
    UPROPERTY(Transient)
    TObjectPtr<UEWContainerWidget> ContainerWidget;
    UPROPERTY(Transient)
    TObjectPtr<AActor> OpenContainer;
    /** Shared by the inventory and container screens: blocks gameplay input and tells the server a menu is up. */
    void SetMenuInputBlocked(bool bBlocked);

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
