#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Characters/EWAppearance.h"
#include "EWCharacterCreatorWidget.generated.h"

class UButton;
class UTextBlock;
class UHorizontalBox;
DECLARE_DELEGATE(FEWCreatorEvent);
DECLARE_DELEGATE_OneParam(FEWCreatorTurn, float);

/**
 * The character creator, after "Start your journey": a panel on the left to choose the survivor's body, colouring
 * and height, with the survivor standing to the right (drag across it to turn it), then Set Sail or Back.
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
    FEWCreatorTurn OnTurn;

    UFUNCTION(BlueprintPure, Category="Creator")
    FEWAppearance GetAppearance() const { return Appearance; }
    UFUNCTION(BlueprintCallable, Category="Creator")
    void SelectBody(int32 Index);
    UFUNCTION(BlueprintCallable, Category="Creator")
    void SelectTone(int32 Index);
    /** +1 taller, -1 shorter, in steps of 2%. */
    UFUNCTION(BlueprintCallable, Category="Creator")
    void NudgeHeight(int32 Direction);
    UFUNCTION(BlueprintCallable, Category="Creator")
    void SetSail();
    UFUNCTION(BlueprintCallable, Category="Creator")
    void GoBack();
    /** How many body and tone choices are shown. */
    UFUNCTION(BlueprintPure, Category="Creator")
    int32 GetBodyChoiceCount() const { return BodyButtons.Num(); }
    UFUNCTION(BlueprintPure, Category="Creator")
    int32 GetToneChoiceCount() const { return ToneButtons.Num(); }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void HandleBodyClicked();
    UFUNCTION() void HandleToneClicked();
    UFUNCTION() void HandleShorter();
    UFUNCTION() void HandleTaller();
    UFUNCTION() void HandleSetSail();
    UFUNCTION() void HandleBack();
    void Refresh();
    UButton* MakeButton(const FText& Label, int32 FontSize);
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> BodyButtons;
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> ToneButtons;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> HeightText;
    bool bDragging = false;
};
