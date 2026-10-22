#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWMapWidget.generated.h"

class ASceneCapture2D;
class UTextureRenderTarget2D;
class UTexture2D;
class UMaterialInstanceDynamic;
class UEWExplorationComponent;
class UImage;
class UBorder;
class UTextBlock;
class UCanvasPanelSlot;
class UCanvasPanel;
class USizeBox;

/**
 * Navigable square map of the world (owner, October 22). The picture is a top-down capture of the world; over it lies grey mist with drifting cloud wherever the
 * survivor has not been, cleared in a circle round them as they explore and staying clear. A scale bar and the compass heading give the basic navigation.
 * On the map, up is +X and right is +Y (the top-down camera's own orientation).
 */
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
    UFUNCTION(BlueprintPure, Category="Map") FText GetScaleText() const;
    UFUNCTION(BlueprintCallable, Category="Map") void AdjustZoom(float Direction);
    UFUNCTION(BlueprintCallable, Category="Map") void SetPanInput(FVector2D Input) { ControllerPanInput = Input; }
    UFUNCTION(BlueprintCallable, Category="Map") void SetPanAxis(bool bHorizontal, float Value) { if (bHorizontal) ControllerPanInput.X = Value; else ControllerPanInput.Y = Value; }
    UFUNCTION(BlueprintCallable, Category="Map") void SetZoomInput(float Input) { ControllerZoomInput = Input; }
    /** The colour of the captured map at a point of it (0..1 across and down), for tests: a map that is all one colour is a broken map. */
    UFUNCTION(BlueprintCallable, Category="Map") FLinearColor ProbeMapPixel(FVector2D Uv) const;
    /** True once the mist is drawn over the map. */
    UFUNCTION(BlueprintPure, Category="Map") bool HasFog() const { return FogTexture != nullptr && FogImage != nullptr; }
    /** The mist's opacity over a place in the world, 0 clear to 1 thick, as last drawn; 1 where there is no mist image yet. */
    UFUNCTION(BlueprintPure, Category="Map") float GetFogAlphaAtWorld(FVector Location) const;
    /** Moves the map's view to a world place (tests, and recentring on the survivor). */
    UFUNCTION(BlueprintCallable, Category="Map") void CenterOn(FVector Location) { MapCenter.X = Location.X; MapCenter.Y = Location.Y; }
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
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> MapMaterial;
    UPROPERTY(Transient) TObjectPtr<UTexture2D> FogTexture;
    UPROPERTY(Transient) TObjectPtr<UImage> MapImage;
    UPROPERTY(Transient) TObjectPtr<UImage> FogImage;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RegionTitle;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> MapHint;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PlayerMarker;
    UPROPERTY(Transient) TObjectPtr<UCanvasPanelSlot> PlayerMarkerSlot;
    UPROPERTY(Transient) TObjectPtr<UCanvasPanel> MapCanvas;
    UPROPERTY(Transient) TObjectPtr<UBorder> ScaleBar;
    UPROPERTY(Transient) TObjectPtr<UCanvasPanelSlot> ScaleBarSlot;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ScaleLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> NorthLabel;
    FVector MapCenter = FVector::ZeroVector;
    float CurrentViewWidth = 12000.f;
    float TargetViewWidth = 12000.f;
    float OverviewViewWidth = 12000.f;
    FVector2D ControllerPanInput = FVector2D::ZeroVector;
    float ControllerZoomInput = 0.f;
    float CaptureRemaining = 0.f;
    float FogClock = 0.f;
    int32 FogRevisionDrawn = -1;
    TArray<FColor> FogPixels;
    static constexpr int32 FogSize = 256;
    bool bHasInitializedView = false;
    bool bMousePanning = false;
    FVector2D LastMousePosition = FVector2D::ZeroVector;

    void PanByScreenDelta(const FVector2D& Delta);
    bool IsPointerOverMap(const FVector2D& ScreenPosition) const;
    void PositionPlayerMarker(const APawn* Pawn);
    void InitializeWorldOverview();
    void UpdateFog(float DeltaSeconds);
    void UpdateScaleBar();
    UEWExplorationComponent* GetExploration() const;
};
