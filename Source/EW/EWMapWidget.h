#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWMapWidget.generated.h"

class ASceneCapture2D;
class UTextureRenderTarget2D;
class UImage;
class UTextBlock;
class UCanvasPanelSlot;
class UCanvasPanel;

/** Navigable world overview and local map, using the placed region actors as island data. */
UCLASS()
class EW_API UEWMapWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Map") bool HasMapCapture() const;
    UFUNCTION(BlueprintPure, Category="Map") FVector GetMapCenter() const { return MapCenter; }
    UFUNCTION(BlueprintPure, Category="Map") float GetViewWidth() const { return CurrentViewWidth; }
    UFUNCTION(BlueprintPure, Category="Map") FText GetRegionTitle() const;
    UFUNCTION(BlueprintPure, Category="Map") FText GetHeadingText() const;
    UFUNCTION(BlueprintPure, Category="Map") FText GetMapHintText() const;
    UFUNCTION(BlueprintCallable, Category="Map") void AdjustZoom(float Direction);
    UFUNCTION(BlueprintCallable, Category="Map") void SetPanInput(FVector2D Input) { ControllerPanInput = Input; }
    UFUNCTION(BlueprintCallable, Category="Map") void SetPanAxis(bool bHorizontal, float Value) { if (bHorizontal) ControllerPanInput.X = Value; else ControllerPanInput.Y = Value; }
    UFUNCTION(BlueprintCallable, Category="Map") void SetZoomInput(float Input) { ControllerZoomInput = Input; }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event) override;
private:
    UPROPERTY(Transient) TObjectPtr<ASceneCapture2D> Capture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> RenderTarget;
    UPROPERTY(Transient) TObjectPtr<UImage> MapImage;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RegionTitle;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> MapHint;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PlayerMarker;
    UPROPERTY(Transient) TObjectPtr<UCanvasPanelSlot> PlayerMarkerSlot;
    UPROPERTY(Transient) TObjectPtr<UCanvasPanel> MapCanvas;
    FVector MapCenter = FVector::ZeroVector;
    float CurrentViewWidth = 12000.f;
    float TargetViewWidth = 12000.f;
    float OverviewViewWidth = 12000.f;
    FVector2D ControllerPanInput = FVector2D::ZeroVector;
    float ControllerZoomInput = 0.f;
    float CaptureRemaining = 0.f;
    bool bHasInitializedView = false;
    bool bMousePanning = false;
    FVector2D LastMousePosition = FVector2D::ZeroVector;

    void PanByScreenDelta(const FVector2D& Delta);
    bool IsPointerOverMap(const FVector2D& ScreenPosition) const;
    void PositionPlayerMarker(const APawn* Pawn);
    void InitializeWorldOverview();
};
