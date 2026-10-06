// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class UEWInventoryComponent;
class UBorder;
class UScrollBox;
class UButton;

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
    virtual FReply NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

	UFUNCTION()
	void RefreshInventory();

private:
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
	void BuildWidgetTree();
	UEWInventoryComponent* ResolveInventory() const;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> SummaryText;

	UPROPERTY(Transient)
	TObjectPtr<UVerticalBox> ItemsBox;

	UPROPERTY(Transient)
	TObjectPtr<UEWInventoryComponent> BoundInventory;
};
