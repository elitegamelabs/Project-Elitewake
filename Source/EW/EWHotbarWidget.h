#pragma once

#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "EWHotbarComponent.h"
#include "EWHotbarWidget.generated.h"

class UTextBlock;
class UBorder;
class UProgressBar;
class UImage;
class UTexture2D;
class UHorizontalBox;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FEWOnHotbarSlotPressed, int32, Slot);

/** Numbered mouse assignment button without stealing inventory navigation focus. */
UCLASS()
class UEWHotbarSlotButton : public UButton
{
    GENERATED_BODY()
public:
    UEWHotbarSlotButton() { InitIsFocusable(false); }
    void InitializeSlot(int32 NewSlotIndex);
    UPROPERTY()
    FEWOnHotbarSlotPressed OnSlotPressed;
private:
    int32 SlotIndex = INDEX_NONE;
    UFUNCTION()
    void EmitSlot();
};

/** Local bottom-center eight-slot HUD. Never intercepts aiming/movement input. */
UCLASS()
class EW_API UEWHotbarWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void ShowResult(EEWHotbarResult Result);
    static FText ResultText(EEWHotbarResult Result);
    virtual void NativeConstruct() override;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;

private:
    UPROPERTY(Transient) TObjectPtr<UHorizontalBox> SlotPanel;
    UPROPERTY(Transient) TArray<TObjectPtr<UProgressBar>> FreshnessBars;
    UPROPERTY(Transient) TArray<TObjectPtr<UImage>> Icons;
    UPROPERTY(Transient) TArray<TObjectPtr<UTexture2D>> FallbackIcons;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> Quantities;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SelectionMarkers;
    void BuildWidgetTree();
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> Labels;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> Cells;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> Status;
    TWeakObjectPtr<UEWHotbarComponent> PreviousHotbar;
    FString LastDisplay;
    float MessageRemaining = 0.f;
};
