#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWPortSelectWidget.generated.h"

class UTexture2D;
DECLARE_DELEGATE(FEWPortSelectEvent);

/**
 * After Single Player (owner, November 7): a wide box showing the whole world with every island (the only screen that
 * shows them all), each Freeport selectable on the map or in the list beside it; centred below, Resume Game (when a survivor
 * was played before) and Create New Survivor. Mouse, keyboard and controller.
 */
UCLASS()
class EW_API UEWPortSelectWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** The world, drawn by Scripts/Art/draw_port_select_map.py. */
    UPROPERTY(Transient) TObjectPtr<UTexture2D> MapArt;
    /** Set before showing: a survivor was played before, and when it was saved. */
    bool bCanResume = false;
    FText ResumeNote;
    FEWPortSelectEvent OnResume, OnCreateNew, OnBack;

    UFUNCTION(BlueprintCallable, Category="Front end") void SelectPort(int32 Index);
    UFUNCTION(BlueprintPure, Category="Front end") int32 GetSelectedPort() const { return Port; }
    UFUNCTION(BlueprintPure, Category="Front end") FName GetSelectedPortId() const;
    UFUNCTION(BlueprintPure, Category="Front end") bool IsResumeShown() const { return bCanResume; }
    UFUNCTION(BlueprintCallable, Category="Front end") void Resume();
    /** Asks first when it would replace a survivor played before. */
    UFUNCTION(BlueprintCallable, Category="Front end") void CreateNew();
    UFUNCTION(BlueprintCallable, Category="Front end") void AnswerReplace(bool bYes);
    UFUNCTION(BlueprintPure, Category="Front end") bool IsAskingToReplace() const { return bAsking; }
    UFUNCTION(BlueprintCallable, Category="Front end") void GoBack();
    /** A port marker's centre in the widget (for checks), or (-1,-1). */
    UFUNCTION(BlueprintPure, Category="Front end") FVector2D GetPortMarker(int32 Index) const;

    /** The world rectangle the map picture shows, cm (draw_port_select_map.py). */
    static constexpr float ArtHalfX = 4000000.f;
    static constexpr float ArtHalfY = 1800000.f;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;

private:
    struct FLayout
    {
        FSlateRect Box, Map, List;
        TArray<FSlateRect> Entries;
        TArray<FVector2D> Markers;
        TArray<FSlateRect> Buttons;     // Resume (if shown), Create New
        FSlateRect Back;
        FSlateRect AskYes, AskNo, AskPanel;
        float HalfW = 0.f, HalfH = 0.f;
    };
    FLayout Layout(const FVector2D& Size) const;
    int32 ButtonCount() const { return bCanResume ? 2 : 1; }
    void Activate(int32 Button);
    FVector2D LastSize = FVector2D(1920, 1080);
    int32 Port = 0;
    int32 HoverPort = INDEX_NONE;
    int32 Focus = 0;          // the focused button
    int32 AskFocus = 1;       // in the question: 0 yes, 1 no
    bool bAsking = false;
    bool bGamepad = false;
    float Age = 0.f;
};
