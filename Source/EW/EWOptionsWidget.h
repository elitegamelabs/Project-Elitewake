#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWOptionsWidget.generated.h"
class UButton;
class UTextBlock;
class USlider;
class UVerticalBox;

/** Escape's pause menu, in two tabs (owner, October 25): PAUSE (SAVE GAME in single player, MAIN MENU) and OPTIONS (brightness and the look sensitivities). Tab, RB/LB, PageUp/PageDown or a click switch tabs. */
UCLASS()
class EW_API UEWOptionsWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Options") int32 GetSelected() const { return Selected; }
    /** 0 = PAUSE, 1 = OPTIONS. */
    UFUNCTION(BlueprintPure, Category="Options") int32 GetTab() const { return Tab; }
    UFUNCTION(BlueprintCallable, Category="Options") void SetTab(int32 NewTab);
    UFUNCTION(BlueprintPure, Category="Options") bool IsSaveShown() const;
    UFUNCTION(BlueprintPure, Category="Options") FText GetStatus() const;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void SaveGame();
    UFUNCTION() void MainMenu();
    UFUNCTION() void ShowPauseTab() { SetTab(0); }
    UFUNCTION() void ShowOptionsTab() { SetTab(1); }
    UFUNCTION() void HoverSave() { Selected = 3; }
    UFUNCTION() void HoverMenu() { Selected = 4; }
    UFUNCTION() void OnBrightnessChanged(float Value);
    UFUNCTION() void OnMouseSensitivityChanged(float Value);
    UFUNCTION() void OnControllerSensitivityChanged(float Value);
    void AdjustSelectedSetting(float Direction);
    void RefreshSettingLabels();
    UPROPERTY(Transient) TObjectPtr<UButton> SaveButton;
    UPROPERTY(Transient) TObjectPtr<UButton> MenuButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Status;
    UPROPERTY(Transient) TObjectPtr<USlider> BrightnessSlider;
    UPROPERTY(Transient) TObjectPtr<USlider> MouseSensitivitySlider;
    UPROPERTY(Transient) TObjectPtr<USlider> ControllerSensitivitySlider;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SettingLabels;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SettingValues;
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> TabButtons;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> PausePage;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> OptionsPage;
    int32 Selected = 3;
    int32 Tab = 0;
};
