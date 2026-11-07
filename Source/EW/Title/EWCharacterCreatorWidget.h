#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Characters/EWAppearance.h"
#include "EWCharacterCreatorWidget.generated.h"

DECLARE_DELEGATE(FEWCreatorEvent);
DECLARE_DELEGATE_OneParam(FEWCreatorAmount, float);

/**
 * Create New Survivor (owner, November 7): a box filling the left half of the screen shows the survivor live; on the
 * right, male or female, a preset to start from, and tabs of sliders and choices for every face and body feature, skin,
 * hair, facial hair, makeup and custom tattoos; then Set Sail. Mouse, keyboard and controller alike.
 * The mannequin shows the body, size, shape and skin now; the face, hair, makeup and tattoos are kept in the look for the
 * real character model (Phase 5).
 */
UCLASS()
class EW_API UEWCharacterCreatorWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** Set before the widget is shown. */
    UPROPERTY(Transient)
    TObjectPtr<UEWBodyRoster> Roster;
    FEWAppearance Appearance;
    FEWCreatorEvent OnChanged, OnSetSail, OnBack;
    /** Degrees to turn the survivor; a zoom step (+ closer). */
    FEWCreatorAmount OnTurn, OnZoom;

    UFUNCTION(BlueprintPure, Category="Creator") FEWAppearance GetAppearance() const { return Appearance; }
    /** 0 male, 1 female: starts again from the current preset on that body. */
    UFUNCTION(BlueprintCallable, Category="Creator") void SelectBody(int32 Index);
    UFUNCTION(BlueprintCallable, Category="Creator") void SelectPreset(int32 Index);
    UFUNCTION(BlueprintCallable, Category="Creator") void SetSliderValue(const FString& Id, float Value);
    UFUNCTION(BlueprintPure, Category="Creator") float GetSliderValue(const FString& Id) const;
    UFUNCTION(BlueprintCallable, Category="Creator") void SetChoiceValue(const FString& Id, int32 Value);
    UFUNCTION(BlueprintCallable, Category="Creator") void SetTattoo(int32 TattooIndex, int32 Design, int32 Place, float Size, float Angle, int32 Ink);
    UFUNCTION(BlueprintCallable, Category="Creator") void Randomise();
    UFUNCTION(BlueprintCallable, Category="Creator") void ShowTab(int32 Tab);
    UFUNCTION(BlueprintPure, Category="Creator") int32 GetTab() const { return Tab; }
    UFUNCTION(BlueprintPure, Category="Creator") int32 GetTabCount() const;
    /** Rows that can be chosen on the current tab, and which is chosen. */
    UFUNCTION(BlueprintPure, Category="Creator") int32 GetRowCount() const;
    UFUNCTION(BlueprintPure, Category="Creator") int32 GetSelectedRow() const { return Selected; }
    UFUNCTION(BlueprintPure, Category="Creator") FString GetSelectedRowLabel() const;
    UFUNCTION(BlueprintCallable, Category="Creator") void SetSail();
    UFUNCTION(BlueprintCallable, Category="Creator") void GoBack();
    /** The preview box (left, top, width, height) in the widget. */
    UFUNCTION(BlueprintPure, Category="Creator") FVector4 GetPreviewBox() const;
    /** Every slider and choice on every tab (for checks). */
    UFUNCTION(BlueprintPure, Category="Creator") int32 GetTotalOptionCount() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
    virtual FReply NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event) override;

private:
    enum class ERowKind : uint8 { Header, Slider, Choice };
    enum class ESpecial : uint8 { None, Sex, Preset, TattooSlot, TattooDesign, TattooPlace, TattooSize, TattooAngle, TattooInk };
    struct FRow
    {
        ERowKind Kind = ERowKind::Slider;
        FString Label;
        int32 Slider = INDEX_NONE;
        int32 Choice = INDEX_NONE;
        ESpecial Special = ESpecial::None;
    };
    struct FLayout
    {
        FSlateRect Preview, Panel, List;
        TArray<FSlateRect> Tabs;
        TArray<FSlateRect> Rows;       // every row of the tab, scrolled (may lie outside List)
        FSlateRect Back, Random, Sail;
    };
    void BuildRows();
    FLayout Layout(const FVector2D& Size) const;
    FSlateRect ControlOf(const FSlateRect& Row) const;
    FSlateRect TrackOf(const FSlateRect& Row) const;
    float RowValue(const FRow& Row) const;
    FString RowText(const FRow& Row) const;
    int32 RowOptions(const FRow& Row) const;
    void Step(const FRow& Row, int32 Direction, bool bFine = false);
    void SetRowValue(const FRow& Row, float Value);
    void MoveSelection(int32 Direction);
    void KeepSelectionInView();
    void SyncTattoos();
    void Changed();
    TArray<int32> Selectable() const;

    TArray<FRow> Rows;
    TArray<FEWTattoo> Slots;
    FVector2D LastSize = FVector2D(1920, 1080);
    int32 Tab = 0;
    int32 Selected = 0;          // index into Selectable()
    int32 TattooSlot = 0;
    float Scroll = 0.f;
    float TurnAxis = 0.f;
    int32 DragRow = INDEX_NONE;
    int32 HoverButton = INDEX_NONE;   // 0 back, 1 randomise, 2 set sail
    bool bTurning = false;
    bool bGamepad = false;
    int32 RandomSeed = 1;
};
