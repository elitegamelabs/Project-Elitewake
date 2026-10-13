#include "Title/EWTitleWidget.h"
#include "Engine/Texture2D.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace
{
const float FadeInSeconds = 1.5f;
const float FadeOutSeconds = .6f;
}

void UEWTitleWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);
    SetKeyboardFocus();
}

FSlateRect UEWTitleWidget::ArtRect(const FVector2D& Size) const
{
    const FVector2D ArtSize = Art ? FVector2D(Art->GetSizeX(), Art->GetSizeY()) : FVector2D(16, 9);
    const float Scale = FMath::Max(Size.X / ArtSize.X, Size.Y / ArtSize.Y);
    const FVector2D Shown = ArtSize * Scale;
    const FVector2D Corner = (Size - Shown) * .5f;
    return FSlateRect(Corner, Corner + Shown);
}

FSlateRect UEWTitleWidget::ButtonRect(const FVector2D& Size) const
{
    const FSlateRect A = ArtRect(Size);
    const FVector2D S = A.GetSize();
    return FSlateRect(A.Left + S.X * ButtonLeft, A.Top + S.Y * ButtonTop, A.Left + S.X * ButtonRight, A.Top + S.Y * ButtonBottom);
}

FVector4 UEWTitleWidget::GetStartButtonRect() const
{
    const FSlateRect R = ButtonRect(LastSize);
    return FVector4(R.Left, R.Top, R.GetSize().X, R.GetSize().Y);
}

void UEWTitleWidget::StartJourney()
{
    if (bLeaving) return;
    bLeaving = true;
    LeaveSeconds = 0.f;
}

void UEWTitleWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    LastSize = Geometry.GetLocalSize();
    Age += DeltaTime;
    Glow = FMath::FInterpTo(Glow, bHovered && !bLeaving ? 1.f : 0.f, DeltaTime, 8.f);
    if (bLeaving)
    {
        LeaveSeconds += DeltaTime;
        if (LeaveSeconds >= FadeOutSeconds)
        {
            bLeaving = false;   // hand over once
            LeaveSeconds = -1.f;
            OnStartJourney.ExecuteIfBound();
        }
    }
}

FReply UEWTitleWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    bHovered = ButtonRect(Geometry.GetLocalSize()).ContainsPoint(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition()));
    return FReply::Handled();
}

FReply UEWTitleWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton
        && ButtonRect(Geometry.GetLocalSize()).ContainsPoint(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition())))
    {
        StartJourney();
        return FReply::Handled();
    }
    return FReply::Unhandled();
}

FReply UEWTitleWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        StartJourney();
        return FReply::Handled();
    }
    return FReply::Unhandled();
}

int32 UEWTitleWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");
    auto Box = [&](int32 L, const FSlateRect& R, const FSlateBrush* Brush, const FLinearColor& Colour)
    {
        FSlateDrawElement::MakeBox(OutDrawElements, Layer + L,
            AllottedGeometry.ToPaintGeometry(FVector2f(R.GetSize()), FSlateLayoutTransform(FVector2f(R.GetTopLeft()))),
            Brush, ESlateDrawEffect::None, Colour);
    };
    Box(1, FSlateRect(FVector2D::ZeroVector, Size), White, FLinearColor::Black);
    if (Art)
    {
        FSlateBrush ArtBrush;
        ArtBrush.SetResourceObject(Art);
        ArtBrush.ImageSize = FVector2D(Art->GetSizeX(), Art->GetSizeY());
        Box(2, ArtRect(Size), &ArtBrush, FLinearColor::White);
    }
    // The button: a warm haze behind the words and a fine rule beneath them while the mouse is on them.
    if (Glow > .01f)
    {
        const FSlateRect R = ButtonRect(Size);
        const float Pulse = .85f + .15f * FMath::Sin(Age * 3.f);
        const FVector2D Pad(R.GetSize().X * .06f, R.GetSize().Y * .25f);
        Box(3, FSlateRect(R.GetTopLeft() - Pad, R.GetBottomRight() + Pad), White, FLinearColor(1.f, .78f, .45f, .10f * Glow * Pulse));
        Box(4, FSlateRect(R.Left + R.GetSize().X * .1f, R.Bottom, R.Right - R.GetSize().X * .1f, R.Bottom + 2.f), White,
            FLinearColor(1.f, .86f, .6f, .85f * Glow));
    }
    // Fade in from black at the start, out to black when leaving.
    float Black = FMath::Clamp(1.f - Age / FadeInSeconds, 0.f, 1.f);
    if (bLeaving || LeaveSeconds < 0.f) Black = FMath::Max(Black, LeaveSeconds < 0.f ? 1.f : LeaveSeconds / FadeOutSeconds);
    if (Black > 0.f) Box(5, FSlateRect(FVector2D::ZeroVector, Size), White, FLinearColor(0, 0, 0, Black));
    return Layer + 6;
}
