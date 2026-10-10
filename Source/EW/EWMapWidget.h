#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWMapWidget.generated.h"

class ASceneCapture2D;
class UTextureRenderTarget2D;
class UImage;
class UTextBlock;

/** Local surrounding-area preview. Full-world discovery/cartography is separate work. */
UCLASS()
class EW_API UEWMapWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Map") bool HasMapCapture() const;
    UFUNCTION(BlueprintPure, Category="Map") FVector GetMapCenter() const { return MapCenter; }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
    /** Prototype local view size in cm; final navigation scale remains designer-owned. */
    UPROPERTY(EditDefaultsOnly, Category="Map", meta=(ClampMin="1000")) float ViewWidth = 12000.f;
private:
    UPROPERTY(Transient) TObjectPtr<ASceneCapture2D> Capture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> RenderTarget;
    UPROPERTY(Transient) TObjectPtr<UImage> MapImage;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PlayerMarker;
    FVector MapCenter = FVector::ZeroVector;
    float CaptureRemaining = 0.f;
};
