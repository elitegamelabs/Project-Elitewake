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
class URichTextBlock;

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
    TArray<TObjectPtr<UTextBlock>> KeyHints;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> Cells;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> Status;
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> ModifierHint;
    /** Each slot's gamepad button as the pad's own icon (owner, November 1); the text KeyHints stand in when there is none. */
    UPROPERTY(Transient) TArray<TObjectPtr<UImage>> KeyIcons;
    /** LB or L1, the modifier for slots 5 to 8, as an icon. */
    UPROPERTY(Transient) TObjectPtr<UImage> ModifierIcon;
    /** How to open Build Mode (owner, November 1): "hold LB + D-pad Right", "hold L1 + D-pad Right", or the B key. */
    UPROPERTY(Transient) TObjectPtr<URichTextBlock> BuildHint;
    FText BuildHintPlain;
    int32 ShownFamily = 0;
public:
    /** The build hint as plain words (empty when hidden), for Play checks. */
    UFUNCTION(BlueprintPure, Category="Hotbar") FText GetBuildHint() const { return BuildHintPlain; }
    /** The family the hotbar's button icons are drawn for (0 none, 1 Xbox, 2 PlayStation). */
    UFUNCTION(BlueprintPure, Category="Hotbar") int32 GetShownIconFamily() const { return ShownFamily; }
    /** The words for the build hint, with [Gamepad_...] button tokens. */
    static FString BuildHintText(bool bController);
private:
    TWeakObjectPtr<UEWHotbarComponent> PreviousHotbar;
    FString LastDisplay;
    float MessageRemaining = 0.f;
};
