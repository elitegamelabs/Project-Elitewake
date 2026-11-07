#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWTitleWidget.generated.h"

class UTexture2D;
class UMaterialInterface;
class UMaterialInstanceDynamic;
DECLARE_DELEGATE(FEWOnTitleContinue);
DECLARE_DELEGATE(FEWOnSinglePlayer);

UENUM(BlueprintType)
enum class EEWTitleScreen : uint8
{
    Splash,
    MainMenu
};

/** Full-screen title splash and the two-option front menu. */
UCLASS()
class EW_API UEWTitleWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title") TObjectPtr<UTexture2D> Art;
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title") TObjectPtr<UTexture2D> PromptArt;
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title") TObjectPtr<UTexture2D> MainMenuArt;
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title") TObjectPtr<UTexture2D> WaterMaskArt;
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title") TObjectPtr<UMaterialInterface> WaterMaterial;

    FEWOnTitleContinue OnContinue;
    FEWOnSinglePlayer OnSinglePlayer;

    /** Legacy callable retained for existing test tooling; advances the splash or starts Single Player. */
    UFUNCTION(BlueprintCallable, Category="Title") void StartJourney();
    UFUNCTION(BlueprintCallable, Category="Title") void ContinueToMenu();
    UFUNCTION(BlueprintCallable, Category="Title") void StartSinglePlayer();
    UFUNCTION(BlueprintPure, Category="Title") EEWTitleScreen GetScreen() const { return Screen; }
    UFUNCTION(BlueprintPure, Category="Title") bool IsSplashScreen() const { return Screen == EEWTitleScreen::Splash; }
    UFUNCTION(BlueprintPure, Category="Title") bool IsMainMenuScreen() const { return Screen == EEWTitleScreen::MainMenu; }
    UFUNCTION(BlueprintPure, Category="Title") bool IsMultiplayerAvailable() const { return false; }
    UFUNCTION(BlueprintPure, Category="Title") FVector4 GetSinglePlayerButtonRect() const;

    static constexpr float SingleLeft = .064f;
    static constexpr float SingleTop = .266f;
    static constexpr float SingleRight = .493f;
    static constexpr float SingleBottom = .85f;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;

private:
    FSlateRect CoverRect(const FVector2D& Size, const UTexture2D* Texture) const;
    FSlateRect SinglePlayerRect(const FVector2D& Size) const;
    FSlateRect MultiplayerRect(const FVector2D& Size) const;
    FVector2D LastSize = FVector2D(1920, 1080);
    EEWTitleScreen Screen = EEWTitleScreen::Splash;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> WaterMaterialInstance;
    bool bHovered = false;
    bool bMultiplayerHovered = false;
    float Age = 0.f;
    float Glow = 0.f;
    float MultiplayerGlow = 0.f;
};
