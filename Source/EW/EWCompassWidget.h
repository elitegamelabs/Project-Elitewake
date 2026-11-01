#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWCompassWidget.generated.h"

/**
 * A compass strip across the top of the screen. The bearings scroll past a fixed centre mark as the view turns:
 * north is the world's +X (as on the map), east +Y. The wind is marked where it blows from.
 * At the helm of a ship with sails it also shows the sails' trim: where they are swung, where they would draw
 * best, and how well they draw. In Saltreach it marks where the shown town step is done. Local and read-only.
 */
UCLASS()
class EW_API UEWCompassWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** The bearing the view faces, 0-360 clockwise from north. */
    UFUNCTION(BlueprintPure, Category="Compass")
    float GetHeading() const { return Heading; }
    /** The bearing the wind blows from, 0-360. */
    UFUNCTION(BlueprintPure, Category="Compass")
    float GetWindFrom() const { return WindFrom; }
    /** True while the trim readout shows, at the helm of a ship with sails. */
    UFUNCTION(BlueprintPure, Category="Compass")
    bool IsShowingTrim() const { return bShowTrim; }
    /** The trim advice shown, for example "Trim to starboard". */
    UFUNCTION(BlueprintPure, Category="Compass")
    FString GetTrimAdvice() const { return TrimAdvice; }
    /** True while the strip marks where Saltreach's shown town step is done (UEWArrivalComponent::GetTownTarget). */
    UFUNCTION(BlueprintPure, Category="Compass")
    bool IsShowingPlace() const { return bShowPlace; }
    /** That place's bearing, 0-360, and how far it is, metres. */
    UFUNCTION(BlueprintPure, Category="Compass")
    float GetPlaceBearing() const { return PlaceBearing; }
    UFUNCTION(BlueprintPure, Category="Compass")
    int32 GetPlaceMetres() const { return PlaceMetres; }

    /** Degrees of bearing the strip spans, and its size on screen (tuning). */
    static constexpr float SpanDegrees = 180.f;
    static constexpr float StripWidth = 620.f;
    static constexpr float StripHeight = 34.f;
protected:
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
private:
    float Heading = 0.f;
    float WindFrom = 0.f;
    bool bShown = false;
    bool bShowTrim = false;
    float SailAngle = 0.f;
    float BestSailAngle = 0.f;
    float TrimQuality = 0.f;
    float MaxSailAngle = 85.f;
    FString TrimAdvice;
    bool bShowPlace = false;
    float PlaceBearing = 0.f;
    int32 PlaceMetres = 0;
};
