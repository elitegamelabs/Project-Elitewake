// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWInventoryWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class UWrapBox;
class UEWInventoryComponent;
class UBorder;
class UScrollBox;
class UButton;
class UEWHotbarSlotButton;
class UHorizontalBox;
class UImage;
class UTexture2D;
class UProgressBar;
class UEWCompanyWidget;
class UEWJournalWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FEWRecipePressed, int32, Index);
UCLASS()
class UEWRecipeButton : public UButton
{
    GENERATED_BODY()
public:
    UEWRecipeButton() { InitIsFocusable(false); }
    int32 RecipeIndex = 0;
    FEWRecipePressed OnRecipePressed;
    void Initialize(int32 Index) { RecipeIndex = Index; OnClicked.AddDynamic(this, &UEWRecipeButton::Pressed); }
private:
    UFUNCTION() void Pressed() { OnRecipePressed.Broadcast(RecipeIndex); }
};

/** Keep mouse actions from taking navigation focus away from the inventory panel. */
UCLASS()
class UEWInventoryActionButton : public UButton
{
    GENERATED_BODY()
public:
    UEWInventoryActionButton() { InitIsFocusable(false); }
};

/** Functional first-pass inventory screen. Final art and equipment presentation will replace this layout. */
UCLASS()
class EW_API UEWInventoryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
    UPROPERTY(Transient) TObjectPtr<UEWCompanyWidget> CompanyPanel;
    UPROPERTY(Transient) TObjectPtr<UEWJournalWidget> JournalPanel;
    /** The Journal section's panel, for tests and tools. */
    UFUNCTION(BlueprintPure, Category="Menu") UEWJournalWidget* GetJournalPanel() const { return JournalPanel; }
    /** Opens a menu section by its tab: 0 inventory, 1 crafting, ... 6 journal. */
    UFUNCTION(BlueprintCallable, Category="Menu") void OpenSection(int32 Index) { SelectSection(Index); }
    UPROPERTY(Transient) TObjectPtr<UWidget> SurvivorPanel;
    UFUNCTION(BlueprintPure, Category="Inventory|Presentation")
    FText GetDisplayedDetails() const;
    UFUNCTION(BlueprintPure, Category="Inventory|Food")
    bool IsFoodActionVisible() const;
    UFUNCTION(BlueprintPure, Category="Inventory|Food")
    float GetDisplayedFoodFreshness() const;
    void ShowFoodResult(EEWFoodUseResult Result);
    void ShowCraftResult(EEWCraftResult Result);
    UFUNCTION(BlueprintPure, Category="Inventory|Crafting") bool IsCraftActionEnabled() const;
    UFUNCTION(BlueprintPure, Category="Inventory|Presentation") UTexture2D* GetDisplayedInventoryIcon(UEWItemDefinition* Item) const;
    UFUNCTION(BlueprintPure, Category="Inventory|Presentation") UTexture2D* GetDisplayedMaterialIcon(UEWItemDefinition* Item) const;
    void ShowHotbarResult(EEWHotbarResult Result);
    void ShowEquipmentResult(EEWEquipmentResult Result);
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
    UFUNCTION(BlueprintPure, Category="Inventory")
    int32 GetSelectedIndex() const { return SelectedIndex; }
    UFUNCTION(BlueprintPure, Category="Inventory")
    bool IsShowingDetails() const { return bShowingDetails; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
    virtual FReply NativeOnKeyUp(const FGeometry& Geometry, const FKeyEvent& Event) override;
    virtual FReply NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnPreviewMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

	UFUNCTION()
	void RefreshInventory();

private:
    /** One square slot of the grid: the item's picture filling it, its count in the corner, its name along the
     *  bottom and, for food that ages, a thin freshness bar. With no item, an empty slot. */
    UBorder* MakeSlotTile(UEWItemDefinition* Item, const FString& Corner, float Freshness, UImage*& Image, UProgressBar*& FreshBar);
    void AddToGrid(UWrapBox* Grid, UBorder* Tile);
    void BuildStatRows(UVerticalBox* Into);
    UFUNCTION() void ShowInventoryTab();
    UFUNCTION() void ShowCraftingTab();
    UPROPERTY(Transient) TObjectPtr<UButton> InventoryTab;
    UPROPERTY(Transient) TObjectPtr<UButton> CraftingTab;
    UPROPERTY(Transient) TObjectPtr<UImage> ItemPreview;
    UFUNCTION() void SelectSection(int32 Index);
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> SectionButtons;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> BrowserPanel;
    UPROPERTY(Transient) TObjectPtr<UBorder> DetailsPanel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> SectionMessage;
    int32 SelectedSection = 0;

    UHorizontalBox* MakeItemRow(UEWItemDefinition* Item, UWidget* Label, UImage*& Image);
    UPROPERTY(Transient) TMap<UEWItemDefinition*, TObjectPtr<UImage>> InventoryImages;
    UPROPERTY(Transient) TMap<UEWItemDefinition*, TObjectPtr<UImage>> MaterialImages;
    UFUNCTION() void ToggleCrafting();
    UFUNCTION() void SelectRecipe(int32 Index);
    UFUNCTION() void PerformCraft();
    void RefreshCrafting();
    bool bCraftingOpen = false;
    int32 SelectedRecipeIndex = 0;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> CraftingBox;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CraftingDetails;
    UPROPERTY(Transient) TObjectPtr<UButton> CraftButton;
    UPROPERTY(Transient) TArray<TObjectPtr<UEWCraftingRecipe>> DisplayedRecipes;
    UFUNCTION()
    void PerformFoodAction();
    UPROPERTY(Transient) TObjectPtr<UButton> FoodActionButton;
    UFUNCTION()
    void AssignHotbarSlot(int32 SlotIndex);
    UFUNCTION()
    void RefreshHotbarAssignments();
    UPROPERTY(Transient)
    TObjectPtr<UEWHotbarComponent> BoundHotbar;
    UPROPERTY(Transient)
    TObjectPtr<UVerticalBox> HotbarAssignments;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UEWHotbarSlotButton>> HotbarButtons;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> HotbarButtonLabels;
    UFUNCTION()
    void PerformEquipmentAction();
    UEWItemDefinition* SelectedItem() const;
    EEWEquipmentSlot SelectedEquipmentSlot() const;
    UEWEquipmentComponent* ResolveEquipment() const;
    int32 SelectionCount() const { return DisplayedEntries.Num() + DisplayedEquipment.Num(); }
    UPROPERTY(Transient)
    TArray<FEWEquipmentEntry> DisplayedEquipment;
    UPROPERTY(Transient)
    TObjectPtr<UEWEquipmentComponent> BoundEquipment;
    UPROPERTY(Transient)
    TObjectPtr<UButton> EquipmentActionButton;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> EquipmentActionText;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> EquipmentResultText;
    void Select(int32 Index);
    void UpdateSelection();
    void ConfirmSelection();
    int32 RowAt(const FVector2D& Position) const;
    void RefreshSummary();
    int32 SelectedIndex = INDEX_NONE;
    bool bShowingDetails = false;
    int32 AnalogDirection = 0;
    float AnalogRepeatRemaining = 0.f;
    int32 RevealSelectionAfterFrames = 0;
    UPROPERTY(Transient)
    TArray<FEWInventoryEntry> DisplayedEntries;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> Rows;
    UPROPERTY(Transient)
    TObjectPtr<UScrollBox> ItemsScroll;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailsText;
    UTexture2D* ResolveIcon(UEWItemDefinition* Item);
    UPROPERTY(Transient) TMap<int32,TObjectPtr<UTexture2D>> FallbackIcons;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> RecipeDetailsBox;
    UPROPERTY(Transient) TObjectPtr<UScrollBox> CraftScroll;
	void BuildWidgetTree();
	UEWInventoryComponent* ResolveInventory() const;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> SummaryText;

	UPROPERTY(Transient)
	TObjectPtr<UWrapBox> ItemsBox;
    /** Equipped items, in their own row under the slots. */
    UPROPERTY(Transient) TObjectPtr<UWrapBox> EquippedBox;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> EquippedHeading;
    /** Each selectable tile's freshness bar, or null, parallel to Rows. */
    UPROPERTY(Transient) TArray<TObjectPtr<UProgressBar>> RowFreshness;
    /** The survivor's needs, each with its icon, value and bar. */
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> StatValues;
    UPROPERTY(Transient) TArray<TObjectPtr<UProgressBar>> StatBars;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ClimateValue;
    UPROPERTY(Transient) TObjectPtr<UProgressBar> HumidityBar;

	UPROPERTY(Transient)
	TObjectPtr<UEWInventoryComponent> BoundInventory;
};
