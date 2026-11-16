#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWLoadingWidget.generated.h"

class UTexture2D;
class UMaterialInterface;
class UMaterialInstanceDynamic;

/** The voyage art, rotating notes and progress are painted from a clock that runs during map loading. */
UCLASS()
class EW_API UEWLoadingWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void ConfigureArt(UTexture2D* Art, UMaterialInterface* WaveMaterial);
    /** The bar fills once the world is ready. */
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
    UPROPERTY(Transient) TObjectPtr<UTexture2D> VoyageArt;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> WaveFrames;
    bool bReady = false;
    float Fade = 1.f;
};
