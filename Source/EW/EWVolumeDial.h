#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWVolumeDial.generated.h"

/** A round volume knob for the options page (owner, October 30: "a dial next to it to adjust the overall game volume"). Painted in
 *  code: a 270-degree track, the filled part up to the value, a pointer and the percentage. Drag up or down (or round the ring),
 *  scroll the wheel, or click a point on the ring. Value 0 to 1. */
UCLASS()
class EW_API UEWVolumeDial : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Options") float GetValue() const { return Value; }
    /** Sets the knob without telling anyone (to follow the slider). */
    UFUNCTION(BlueprintCallable, Category="Options") void SetValue(float NewValue) { Value = FMath::Clamp(NewValue, 0.f, 1.f); }
    /** Called when the player turns the knob. */
    TFunction<void(float)> OnTurned;
protected:
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& CullingRect, FSlateWindowElementList& Elements,
        int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event) override;
    virtual FReply NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event) override;
private:
    void Turn(float NewValue);
    /** The value at a point of the ring (straight down is the gap between the ends). */
    static float ValueAt(const FVector2D& Local, const FVector2D& Size);
    float Value = 1.f;
    bool bDragging = false;
};
