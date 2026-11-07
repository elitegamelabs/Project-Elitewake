#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWShipMarkersWidget.generated.h"

/** One labelled point on a nearby ship, as drawn this frame. */
USTRUCT(BlueprintType)
struct FEWShipMarker
{
    GENERATED_BODY()
    /** Where it sits on the screen, in this widget's units. */
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") FVector2D Position = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") FString Label;
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") FLinearColor Colour = FLinearColor::White;
    /** The one the survivor is aiming at, drawn larger. */
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") bool bAimed = false;
    /** A mount that a fitting the survivor carries would fit. */
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") bool bFits = false;
    /** 1 close by, fading toward 0 at the edge of the range. */
    UPROPERTY(BlueprintReadOnly, Category="Ship Markers") float Strength = 1.f;
};

/** Labels on the ships near the local survivor, so places to act are easy to find: each mount (empty ones and the
 *  size of sail they take, green where a carried fitting fits), the anchor capstan, the hold's hatch and, from
 *  outside, the boarding ladders. The one under the survivor's aim is drawn larger. Local and read-only. */
UCLASS()
class EW_API UEWShipMarkersWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Ship Markers")
    TArray<FEWShipMarker> GetMarkers() const { return Markers; }
    /** How far from the survivor places are labelled, in cm (tuning). */
    static constexpr float Range = 1400.f;
protected:
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
private:
    TArray<FEWShipMarker> Markers;
};
