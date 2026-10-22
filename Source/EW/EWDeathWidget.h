#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWDeathWidget.generated.h"
class UBorder;
class UButton;
class UCanvasPanel;
class UTextBlock;
class UVerticalBox;
class UOverlay;

/**
 * What a survivor sees when they are hurt or die (owner, October 22). Hurt: a small red number jumps off the character and fades. Dead: the screen fades to black,
 * frost creeps in from its edges, and a Respawn button waits (mouse click, Enter or Space, or the controller's A button). Respawning asks the server to bring them
 * back at a safe place away from where they fell. The widget lives on the player's screen for the whole session and does nothing while they are well.
 */
UCLASS()
class EW_API UEWDeathWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** Seconds from the moment of death until the screen is black and Respawn can be chosen. */
    static constexpr float FadeSeconds = 2.2f;
    /** Seconds the red damage number takes to rise, bounce and fade. */
    static constexpr float DamageFlashSeconds = .75f;

    UFUNCTION(BlueprintPure, Category="Death") bool IsDeathScreenShown() const { return bShown; }
    /** 0 clear, 1 fully black. */
    UFUNCTION(BlueprintPure, Category="Death") float GetFadeAlpha() const;
    UFUNCTION(BlueprintPure, Category="Death") bool IsRespawnAvailable() const { return bShown && DeadClock >= FadeSeconds; }
    UFUNCTION(BlueprintPure, Category="Death") bool IsDamageFlashShown() const { return FlashClock >= 0.f && FlashClock < DamageFlashSeconds; }
    /** How many red damage numbers have been shown this session. */
    UFUNCTION(BlueprintPure, Category="Death") int32 GetDamageFlashCount() const { return FlashesShown; }
    /** Asks the server to respawn; only once the screen has faded. */
    UFUNCTION(BlueprintCallable, Category="Death") bool Respawn();
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void OnRespawnClicked() { Respawn(); }
    void ShowDeathScreen(bool bShow);
    UPROPERTY(Transient) TObjectPtr<UCanvasPanel> Layer;
    UPROPERTY(Transient) TObjectPtr<UBorder> Black;
    UPROPERTY(Transient) TObjectPtr<UOverlay> FrostOverlay;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> Message;
    UPROPERTY(Transient) TObjectPtr<UButton> RespawnButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RespawnLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DamageText;
    bool bShown = false;
    float DeadClock = 0.f;
    float ClearClock = 1.f;       // 0..1 while the black clears after coming back to life
    float FlashClock = -1.f;
    int32 SeenDamageCount = -1;
    int32 FlashesShown = 0;
};
