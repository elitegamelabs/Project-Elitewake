#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWLoadingWidget.generated.h"

class UTexture2D;

/**
 * The loading screen after Set Sail, as ChatGPT designed it for the owner (November 7; C:/ELITEWAKE/ElitewakeLoadingScreen):
 * the voyage picture under a dark wash, a framed brand, "Beyond the horizon.", and a gold indeterminate bar that never claims
 * completion until the world is ready. Painted from the clock alone, so it keeps moving while the map loads.
 */
UCLASS()
class EW_API UEWLoadingWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient) TObjectPtr<UTexture2D> VoyageArt;
    /** The world is ready: the bar fills and the label says so. */
    UFUNCTION(BlueprintCallable, Category="Loading") void SetReady() { bReady = true; }
    UFUNCTION(BlueprintPure, Category="Loading") bool IsReady() const { return bReady; }
    /** 1 shown, 0 gone (a fade). */
    void SetFade(float Value) { Fade = Value; }
    void Restart() { bReady = false; Fade = 1.f; }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
private:
    bool bReady = false;
    float Fade = 1.f;
};
