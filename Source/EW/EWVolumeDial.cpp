#include "EWVolumeDial.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace
{
    // The track runs 270 degrees clockwise from lower left (0) over the top to lower right (1); straight down is the gap.
    constexpr float StartDegrees = 135.f;
    constexpr float SweepDegrees = 270.f;

    FVector2D OnRing(const FVector2D& Centre, float Radius, float Fraction)
    {
        const float Radians = FMath::DegreesToRadians(StartDegrees + SweepDegrees * Fraction);
        return Centre + Radius * FVector2D(FMath::Cos(Radians), FMath::Sin(Radians));
    }

    void Arc(FSlateWindowElementList& Elements, int32 Layer, const FGeometry& Geometry, const FVector2D& Centre, float Radius, float From, float To,
        const FLinearColor& Colour, float Thickness)
    {
        if (To <= From) return;
        TArray<FVector2D> Points;
        const int32 Steps = FMath::Max(2, FMath::CeilToInt((To - From) * 48.f));
        for (int32 Step = 0; Step <= Steps; ++Step) Points.Add(OnRing(Centre, Radius, FMath::Lerp(From, To, float(Step) / Steps)));
        FSlateDrawElement::MakeLines(Elements, Layer, Geometry.ToPaintGeometry(), Points, ESlateDrawEffect::None, Colour, true, Thickness);
    }
}

int32 UEWVolumeDial::NativePaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& CullingRect, FSlateWindowElementList& Elements,
    int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
    const FVector2D Size = Geometry.GetLocalSize();
    const FVector2D Centre = Size * .5f;
    const float Radius = FMath::Max(4.f, FMath::Min(Size.X, Size.Y) * .5f - 5.f);
    // Face, track, the filled part and the pointer.
    Arc(Elements, LayerId, Geometry, Centre, Radius * .5f, 0.f, 1.f / .75f, FLinearColor(.03f, .1f, .13f, 1.f), Radius);
    Arc(Elements, LayerId + 1, Geometry, Centre, Radius, 0.f, 1.f, FLinearColor(.12f, .2f, .24f, 1.f), 5.f);
    Arc(Elements, LayerId + 2, Geometry, Centre, Radius, 0.f, Value, bDragging ? FLinearColor(.45f, .95f, 1.f) : FLinearColor(.25f, .88f, 1.f), 5.f);
    const TArray<FVector2D> Pointer = {Centre, OnRing(Centre, Radius * .78f, Value)};
    FSlateDrawElement::MakeLines(Elements, LayerId + 3, Geometry.ToPaintGeometry(), Pointer, ESlateDrawEffect::None, FLinearColor(.93f, .86f, .7f), true, 3.f);
    // The percentage under the pointer's hub.
    const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", FMath::Max(7, FMath::RoundToInt(Radius * .32f)));
    const FString Label = FString::FromInt(FMath::RoundToInt(Value * 100.f));
    const FVector2D TextSize = FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Label, Font);
    FSlateDrawElement::MakeText(Elements, LayerId + 4,
        Geometry.ToPaintGeometry(TextSize, FSlateLayoutTransform(FVector2D(Centre.X - TextSize.X * .5f, Centre.Y + Radius * .38f))),
        Label, Font, ESlateDrawEffect::None, FLinearColor::White);
    return LayerId + 4;
}

float UEWVolumeDial::ValueAt(const FVector2D& Local, const FVector2D& Size)
{
    const FVector2D From = Local - Size * .5f;
    float Degrees = FMath::RadiansToDegrees(FMath::Atan2(From.Y, From.X)) - StartDegrees;
    while (Degrees < 0.f) Degrees += 360.f;
    // In the gap at the bottom, the nearer end.
    if (Degrees > SweepDegrees) return Degrees < SweepDegrees + 45.f ? 1.f : 0.f;
    return Degrees / SweepDegrees;
}

void UEWVolumeDial::Turn(float NewValue)
{
    NewValue = FMath::Clamp(NewValue, 0.f, 1.f);
    if (FMath::IsNearlyEqual(NewValue, Value)) return;
    Value = NewValue;
    if (OnTurned) OnTurned(Value);
}

FReply UEWVolumeDial::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();
    bDragging = true;
    Turn(ValueAt(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition()), Geometry.GetLocalSize()));
    return FReply::Handled().CaptureMouse(TakeWidget());
}

FReply UEWVolumeDial::NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (!bDragging) return FReply::Unhandled();
    bDragging = false;
    return FReply::Handled().ReleaseMouseCapture();
}

FReply UEWVolumeDial::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (!bDragging) return FReply::Unhandled();
    Turn(ValueAt(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition()), Geometry.GetLocalSize()));
    return FReply::Handled();
}

FReply UEWVolumeDial::NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event)
{
    Turn(Value + (Event.GetWheelDelta() > 0.f ? .02f : -.02f));
    return FReply::Handled();
}
