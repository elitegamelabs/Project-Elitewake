#pragma once

#include "CoreMinimal.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"

/**
 * The single-player front end's look (owner, November 7; from the loading screen ChatGPT designed): a deep sea-blue
 * ground, cream type, gold accents and gold corner brackets. Painted directly, so the port choice, the creator and the
 * loading screen share it and work the same with mouse, keyboard and controller.
 */
namespace EWFrontEnd
{
inline const FLinearColor Ground = FLinearColor::FromSRGBColor(FColor(7, 19, 26));
inline const FLinearColor Panel = FLinearColor::FromSRGBColor(FColor(10, 27, 37)).CopyWithNewOpacity(.94f);
inline const FLinearColor Cream = FLinearColor::FromSRGBColor(FColor(238, 231, 215));
inline const FLinearColor Gold = FLinearColor::FromSRGBColor(FColor(218, 183, 128));
inline const FLinearColor GoldLight = FLinearColor::FromSRGBColor(FColor(241, 216, 168));
inline const FLinearColor Muted = FLinearColor::FromSRGBColor(FColor(190, 190, 181));
inline const FLinearColor Line = FLinearColor::FromSRGBColor(FColor(218, 183, 128)).CopyWithNewOpacity(.35f);
inline const FLinearColor Highlight = FLinearColor::FromSRGBColor(FColor(218, 183, 128)).CopyWithNewOpacity(.16f);

inline FSlateFontInfo Font(int32 Size, bool bBold = false, int32 Spacing = 0)
{
    FSlateFontInfo Info = FCoreStyle::GetDefaultFontStyle(bBold ? "Bold" : "Regular", Size);
    Info.LetterSpacing = Spacing;
    return Info;
}

inline FVector2D Measure(const FString& Text, const FSlateFontInfo& Info)
{
    return FSlateApplication::IsInitialized()
        ? FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, Info) : FVector2D(Text.Len() * Info.Size * .6f, Info.Size * 1.3f);
}

/** Draws into one widget's paint call. */
struct FPainter
{
    const FGeometry& Geometry;
    FSlateWindowElementList& Out;
    int32 Layer;

    FPaintGeometry At(const FSlateRect& R) const
    {
        return Geometry.ToPaintGeometry(FVector2f(R.GetSize()), FSlateLayoutTransform(FVector2f(R.GetTopLeft())));
    }
    void Box(int32 L, const FSlateRect& R, const FLinearColor& Colour) const
    {
        FSlateDrawElement::MakeBox(Out, Layer + L, At(R), FCoreStyle::Get().GetBrush("WhiteBrush"), ESlateDrawEffect::None, Colour);
    }
    void Outline(int32 L, const FSlateRect& R, float Width, const FLinearColor& Colour) const
    {
        Box(L, FSlateRect(R.Left, R.Top, R.Right, R.Top + Width), Colour);
        Box(L, FSlateRect(R.Left, R.Bottom - Width, R.Right, R.Bottom), Colour);
        Box(L, FSlateRect(R.Left, R.Top + Width, R.Left + Width, R.Bottom - Width), Colour);
        Box(L, FSlateRect(R.Right - Width, R.Top + Width, R.Right, R.Bottom - Width), Colour);
    }
    /** Gold corner brackets, as on the loading screen's frame. */
    void Corners(int32 L, const FSlateRect& R, float Arm, float Width, const FLinearColor& Colour) const
    {
        Box(L, FSlateRect(R.Left, R.Top, R.Left + Arm, R.Top + Width), Colour);
        Box(L, FSlateRect(R.Left, R.Top, R.Left + Width, R.Top + Arm), Colour);
        Box(L, FSlateRect(R.Right - Arm, R.Top, R.Right, R.Top + Width), Colour);
        Box(L, FSlateRect(R.Right - Width, R.Top, R.Right, R.Top + Arm), Colour);
        Box(L, FSlateRect(R.Left, R.Bottom - Width, R.Left + Arm, R.Bottom), Colour);
        Box(L, FSlateRect(R.Left, R.Bottom - Arm, R.Left + Width, R.Bottom), Colour);
        Box(L, FSlateRect(R.Right - Arm, R.Bottom - Width, R.Right, R.Bottom), Colour);
        Box(L, FSlateRect(R.Right - Width, R.Bottom - Arm, R.Right, R.Bottom), Colour);
    }
    /** Text with its top-left at Where, or aligned by Align (0 left/top, .5 centre, 1 right/bottom). Returns its size. */
    FVector2D Text(int32 L, const FString& String, const FSlateFontInfo& Info, const FVector2D& Where, const FLinearColor& Colour,
        const FVector2D& Align = FVector2D::ZeroVector) const
    {
        const FVector2D Size = Measure(String, Info);
        const FVector2D Corner = Where - Size * Align;
        FSlateDrawElement::MakeText(Out, Layer + L, Geometry.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(FVector2f(Corner))),
            String, Info, ESlateDrawEffect::None, Colour);
        return Size;
    }
    void Image(int32 L, UObject* Resource, const FSlateRect& R, const FLinearColor& Tint = FLinearColor::White,
        const FBox2f& UV = FBox2f(FVector2f(0, 0), FVector2f(1, 1))) const
    {
        if (!Resource) return;
        FSlateBrush Brush;
        Brush.SetResourceObject(Resource);
        Brush.ImageSize = FVector2D(R.GetSize());
        Brush.SetUVRegion(UV);
        FSlateDrawElement::MakeBox(Out, Layer + L, At(R), &Brush, ESlateDrawEffect::None, Tint);
    }
    /** A gradient across R, colours spread evenly (horizontal: left to right). */
    void Gradient(int32 L, const FSlateRect& R, const TArray<FLinearColor>& Colours, bool bHorizontal) const
    {
        TArray<FSlateGradientStop> Stops;
        for (int32 I = 0; I < Colours.Num(); ++I)
            Stops.Add(FSlateGradientStop(FVector2D(bHorizontal ? R.GetSize().X * I / (Colours.Num() - 1) : 0.f,
                bHorizontal ? 0.f : R.GetSize().Y * I / (Colours.Num() - 1)), Colours[I]));
        FSlateDrawElement::MakeGradient(Out, Layer + L, At(R), Stops, bHorizontal ? Orient_Vertical : Orient_Horizontal);
    }
    /** A labelled button: framed, filled when focused. */
    void Button(int32 L, const FSlateRect& R, const FString& Label, bool bFocused, bool bPrimary, int32 FontSize = 16, bool bEnabled = true) const
    {
        const float Glow = bFocused ? 1.f : 0.f;
        Box(L, R, bPrimary ? Gold.CopyWithNewOpacity(bFocused ? .95f : .75f) : Highlight * (bFocused ? 2.2f : 1.f));
        Outline(L + 1, R, bFocused ? 2.f : 1.f, bFocused ? GoldLight : Line);
        const FLinearColor Ink = !bEnabled ? Muted.CopyWithNewOpacity(.5f) : bPrimary ? Ground : (Glow > 0 ? GoldLight : Cream);
        Text(L + 2, Label, Font(FontSize, true, 180), R.GetCenter(), Ink, FVector2D(.5f, .5f));
    }
};

inline FSlateRect Cover(const FVector2D& Size, const FVector2D& Source)
{
    const float Scale = FMath::Max(Size.X / FMath::Max(1.0, Source.X), Size.Y / FMath::Max(1.0, Source.Y));
    const FVector2D Shown = Source * Scale;
    const FVector2D Corner = (Size - Shown) * .5f;
    return FSlateRect(Corner, Corner + Shown);
}
}
