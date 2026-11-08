#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWOptionsWidget.generated.h"
class UButton;
class UTextBlock;
class USlider;
class UVerticalBox;
class UEWVolumeDial;

/** Escape's pause menu (owner, October 30): a column of buttons, RESUME GAME, SAVE GAME (single player), OPTIONS and MAIN MENU.
 *  OPTIONS opens the settings page (brightness; mouse and controller look speed, each horizontal and vertical; master volume, with a
 *  dial beside it; graphics: an overall quality and five groups, Low to Epic, FEWGraphicsSettings, owner November 1; button icons:
 *  Automatic, Xbox or PlayStation, owner November 1) and BACK;
 *  Escape or B there returns to the buttons. */
UCLASS()
class EW_API UEWOptionsWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** The highlighted entry: on the buttons page one of the Item* values, on the settings page 0..12 a setting and 13 BACK
     *  (0 brightness, 1-4 look speeds, 5 volume, 6 graphics quality, 7-11 the graphics groups, 12 button icons). */
    UFUNCTION(BlueprintPure, Category="Options") int32 GetSelected() const { return Selected; }
    /** 0 = the buttons, 1 = OPTIONS (the settings page). */
    UFUNCTION(BlueprintPure, Category="Options") int32 GetTab() const { return Tab; }
    UFUNCTION(BlueprintCallable, Category="Options") void SetTab(int32 NewTab);
    UFUNCTION(BlueprintPure, Category="Options") bool IsSaveShown() const;
    UFUNCTION(BlueprintPure, Category="Options") FText GetStatus() const;
    /** Where the volume dial points, 0 to 1. */
    UFUNCTION(BlueprintPure, Category="Options") float GetDialValue() const;

    static constexpr int32 ItemResume = 10;
    static constexpr int32 ItemSave = 11;
    static constexpr int32 ItemOptions = 12;
    static constexpr int32 ItemMainMenu = 13;
    // Settings rows: brightness 0, look speeds 1-4, master volume 5, sound effects 6, ambience 7, graphics 8-13, icons 14.
    static constexpr int32 SettingBack = 15;
    static constexpr int32 SettingButtonIcons = 14;
    static constexpr int32 SettingGraphics = 8;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void Resume();
    UFUNCTION() void SaveGame();
    UFUNCTION() void OpenOptions() { SetTab(1); }
    UFUNCTION() void BackToButtons() { SetTab(0); Selected = ItemOptions; }
    UFUNCTION() void MainMenu();
    UFUNCTION() void HoverResume() { Selected = ItemResume; }
    UFUNCTION() void HoverSave() { Selected = ItemSave; }
    UFUNCTION() void HoverOptions() { Selected = ItemOptions; }
    UFUNCTION() void HoverMenu() { Selected = ItemMainMenu; }
    UFUNCTION() void HoverBack() { Selected = SettingBack; }
    UFUNCTION() void OnBrightnessChanged(float Value);
    UFUNCTION() void OnMouseHorizontalChanged(float Value) { OnLookChanged(0, Value); }
    UFUNCTION() void OnMouseVerticalChanged(float Value) { OnLookChanged(1, Value); }
    UFUNCTION() void OnControllerHorizontalChanged(float Value) { OnLookChanged(2, Value); }
    UFUNCTION() void OnControllerVerticalChanged(float Value) { OnLookChanged(3, Value); }
    void OnLookChanged(int32 Which, float Value);
    UFUNCTION() void OnVolumeChanged(float Value);
    UFUNCTION() void OnEffectsVolumeChanged(float Value);
    UFUNCTION() void OnAmbienceVolumeChanged(float Value);
    UFUNCTION() void OnQualityChanged(float Value);
    UFUNCTION() void OnTexturesChanged(float Value) { OnGraphicsChanged(0, Value); }
    UFUNCTION() void OnShadowsChanged(float Value) { OnGraphicsChanged(1, Value); }
    UFUNCTION() void OnFoliageChanged(float Value) { OnGraphicsChanged(2, Value); }
    UFUNCTION() void OnReflectionsChanged(float Value) { OnGraphicsChanged(3, Value); }
    UFUNCTION() void OnEffectsChanged(float Value) { OnGraphicsChanged(4, Value); }
    void OnGraphicsChanged(int32 Group, float Value);
    UFUNCTION() void OnButtonIconsChanged(float Value);
    /** Put the graphics sliders where the settings are (after the overall quality changes every group). */
    void SyncGraphicsSliders();
    void AdjustSelectedSetting(float Direction);
    void RefreshSettingLabels();
    /** The buttons page's entries in order (SAVE GAME only in single player). */
    TArray<int32> ButtonItems() const;
    UPROPERTY(Transient) TObjectPtr<UButton> ResumeButton;
    UPROPERTY(Transient) TObjectPtr<UButton> SaveButton;
    UPROPERTY(Transient) TObjectPtr<UButton> OptionsButton;
    UPROPERTY(Transient) TObjectPtr<UButton> MenuButton;
    UPROPERTY(Transient) TObjectPtr<UButton> BackButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Title;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Status;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Hint;
    UPROPERTY(Transient) TObjectPtr<USlider> BrightnessSlider;
    /** Mouse horizontal, mouse vertical, controller horizontal, controller vertical. */
    UPROPERTY(Transient) TArray<TObjectPtr<USlider>> LookSliders;
    UPROPERTY(Transient) TObjectPtr<USlider> VolumeSlider;
    UPROPERTY(Transient) TObjectPtr<UEWVolumeDial> VolumeDial;
    UPROPERTY(Transient) TObjectPtr<USlider> EffectsSlider;
    UPROPERTY(Transient) TObjectPtr<USlider> AmbienceSlider;
    /** The overall quality, then textures, shadows, foliage detail, water and reflections, effects. Four steps each. */
    UPROPERTY(Transient) TObjectPtr<USlider> QualitySlider;
    UPROPERTY(Transient) TArray<TObjectPtr<USlider>> GraphicsSliders;
    /** Automatic, Xbox, PlayStation: three steps. */
    UPROPERTY(Transient) TObjectPtr<USlider> ButtonIconsSlider;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SettingLabels;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SettingValues;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> PausePage;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> OptionsPage;
    int32 Selected = ItemResume;
    /** SyncGraphicsSliders is moving the sliders: their change handlers stand aside. */
    bool bSyncingGraphics = false;
    int32 Tab = 0;
};
