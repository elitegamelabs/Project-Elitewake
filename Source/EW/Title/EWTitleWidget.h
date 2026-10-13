#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWTitleWidget.generated.h"

class UTexture2D;
DECLARE_DELEGATE(FEWOnStartJourney);

/**
 * The title screen: the title art fills the screen (cropped, never stretched) and its painted "Start your journey"
 * is the button. It glows under the mouse; a click, Enter or the gamepad's bottom face button starts. The screen
 * fades in from black, and out to black before handing over.
 */
UCLASS()
class EW_API UEWTitleWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient, BlueprintReadOnly, Category="Title")
    TObjectPtr<UTexture2D> Art;
    FEWOnStartJourney OnStartJourney;

    /** Starts the journey as the button does (also for tests). */
    UFUNCTION(BlueprintCallable, Category="Title")
    void StartJourney();
    /** Where the button is on screen now, in this widget's units: top left and size. */
    UFUNCTION(BlueprintPure, Category="Title")
    FVector4 GetStartButtonRect() const;
    UFUNCTION(BlueprintPure, Category="Title")
    bool IsStartHovered() const { return bHovered; }

    /** Where "Start your journey" lies in the art, as fractions of its width and height (from the owner's art). */
    static constexpr float ButtonLeft = .375f;
    static constexpr float ButtonTop = .335f;
    static constexpr float ButtonRight = .625f;
    static constexpr float ButtonBottom = .395f;
protected:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    /** The art's rectangle on screen, covering it. */
    FSlateRect ArtRect(const FVector2D& Size) const;
    FSlateRect ButtonRect(const FVector2D& Size) const;
    FVector2D LastSize = FVector2D(1920, 1080);
    bool bHovered = false;
    bool bLeaving = false;
    float Age = 0.f;
    float Glow = 0.f;
    float LeaveSeconds = 0.f;
};
