#include "Title/EWLoadingWidget.h"
#include "Title/EWFrontEndPaint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Engine/Texture2D.h"
#include "HAL/PlatformTime.h"

using namespace EWFrontEnd;

TSharedRef<SWidget> UEWLoadingWidget::RebuildWidget()
{
    SetVisibility(ESlateVisibility::HitTestInvisible);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UBorder* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor::Transparent);
        Root->SetVisibility(ESlateVisibility::HitTestInvisible);
        WidgetTree->RootWidget = Root;
    }
    return Super::RebuildWidget();
}

int32 UEWLoadingWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FPainter P{AllottedGeometry, OutDrawElements, Layer};
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const double Now = FPlatformTime::Seconds();
    const float A = FMath::Clamp(Fade, 0.f, 1.f);
    auto With = [A](const FLinearColor& C) { return C.CopyWithNewOpacity(C.A * A); };
    auto SRGB = [](uint8 R, uint8 G, uint8 B, float Alpha = 1.f) { return FLinearColor::FromSRGBColor(FColor(R, G, B)).CopyWithNewOpacity(Alpha); };

    P.Box(1, FSlateRect(FVector2D::ZeroVector, Size), With(Ground));
    if (VoyageArt)
    {
        // The scene covers the screen, drifting slowly larger and back (22 s), framed a little right of centre.
        const float Drift = 1.034f + .03f * (.5f - .5f * FMath::Cos(float(FMath::Fmod(Now, 44.0)) * PI / 22.f));
        const FVector2D Big = Size * Drift;
        FSlateRect R = Cover(Big, FVector2D(VoyageArt->GetSizeX(), VoyageArt->GetSizeY()));
        R = R.OffsetBy(-(Big - Size) * FVector2D(.57f, .52f));
        P.Image(2, VoyageArt, R, FLinearColor(1, 1, 1, A));
    }
    // The wash: dark from the left, and from the bottom.
    P.Gradient(3, FSlateRect(0, 0, Size.X * .34f, Size.Y), {With(SRGB(5, 15, 22, .82f)), With(SRGB(5, 15, 22, .56f))}, true);
    P.Gradient(3, FSlateRect(Size.X * .34f, 0, Size.X * .75f, Size.Y), {With(SRGB(5, 15, 22, .56f)), With(SRGB(5, 15, 22, .04f))}, true);
    P.Gradient(4, FSlateRect(0, 0, Size.X, Size.Y * .64f), {With(SRGB(3, 11, 17, .18f)), With(SRGB(3, 11, 17, .08f))}, false);
    P.Gradient(4, FSlateRect(0, Size.Y * .64f, Size.X, Size.Y), {With(SRGB(3, 11, 17, .08f)), With(SRGB(3, 11, 17, .88f))}, false);

    // The frame, 28 px in, with corner brackets top-left and bottom-right.
    const FSlateRect Frame(28, 28, Size.X - 28, Size.Y - 28);
    P.Outline(5, Frame, 1.f, With(SRGB(245, 223, 186, .24f)));
    const FLinearColor Bracket = With(SRGB(245, 223, 186, .56f));
    P.Box(6, FSlateRect(Frame.Left - 1, Frame.Top - 1, Frame.Left + 28, Frame.Top + 1), Bracket);
    P.Box(6, FSlateRect(Frame.Left - 1, Frame.Top - 1, Frame.Left + 1, Frame.Top + 28), Bracket);
    P.Box(6, FSlateRect(Frame.Right - 28, Frame.Bottom - 1, Frame.Right + 1, Frame.Bottom + 1), Bracket);
    P.Box(6, FSlateRect(Frame.Right - 1, Frame.Bottom - 28, Frame.Right + 1, Frame.Bottom + 1), Bracket);

    // The brand: a gold diamond with a cross through it, and the name.
    const float Left = FMath::Clamp(Size.X * .071f, 48.f, 144.f);
    float Top = FMath::Clamp(Size.Y * .13f, 72.f, 150.f);
    const FVector2D Mark(Left + 16, Top + 16);
    for (int32 Row = -16; Row <= 16; ++Row)
    {
        const float Half = 16.f - FMath::Abs(Row);
        P.Box(7, FSlateRect(Mark.X - Half, Mark.Y + Row, Mark.X - Half + 1.2f, Mark.Y + Row + 1), With(Gold));
        P.Box(7, FSlateRect(Mark.X + Half - 1.2f, Mark.Y + Row, Mark.X + Half, Mark.Y + Row + 1), With(Gold));
    }
    P.Box(7, FSlateRect(Mark.X - .5f, Mark.Y - 25, Mark.X + .5f, Mark.Y + 25), With(Gold));
    P.Box(7, FSlateRect(Mark.X - 25, Mark.Y - .5f, Mark.X + 25, Mark.Y + .5f), With(Gold));
    P.Text(7, TEXT("ELITEWAKE"), Font(FMath::Clamp(int32(Size.X * .017f), 17, 26), false, 300), FVector2D(Left + 52, Mark.Y), With(Cream), FVector2D(0, .5f));
    Top += 32 + FMath::Clamp(Size.Y * .09f, 48.f, 98.f);

    P.Box(7, FSlateRect(Left, Top + 8, Left + 36, Top + 9), With(Gold));
    P.Text(7, TEXT("YOUR VOYAGE BEGINS"), Font(9, true, 520), FVector2D(Left + 52, Top + 8), With(GoldLight), FVector2D(0, .5f));
    Top += 32;
    const FSlateFontInfo Headline = FCoreStyle::GetDefaultFontStyle("Light", FMath::Clamp(int32(Size.X * .043f), 37, 78));
    const FVector2D Line1 = P.Text(7, TEXT("Beyond the"), Headline, FVector2D(Left - 3, Top), With(Cream));
    P.Text(7, TEXT("horizon."), Headline, FVector2D(Left - 3, Top + Line1.Y * .95f), With(GoldLight));
    Top += Line1.Y * 1.95f + 20;
    P.Text(7, TEXT("The open seas await. Find your course, make your name,"), Font(14), FVector2D(Left, Top), With(SRGB(232, 232, 226)));
    P.Text(7, TEXT("and face the peril between you and glory."), Font(14), FVector2D(Left, Top + 29), With(SRGB(232, 232, 226)));

    // The lower band: the bar on the left, the chapter on the right.
    const float Bottom = Size.Y - FMath::Clamp(Size.Y * .08f, 55.f, 105.f);
    const float BarW = FMath::Min(520.f, Size.X * .58f);
    const float BarTop = Bottom - 46;
    P.Text(7, bReady ? TEXT("YOUR WORLD IS READY") : TEXT("PREPARING YOUR WORLD"), Font(9, true, 440), FVector2D(Left, BarTop - 14), With(GoldLight), FVector2D(0, 1));
    P.Text(7, bReady ? TEXT("100%") : TEXT("PLEASE WAIT"), Font(9, false, 60), FVector2D(Left + BarW, BarTop - 14), With(Muted), FVector2D(1, 1));
    const FSlateRect Track(Left, BarTop, Left + BarW, BarTop + 3);
    P.Box(7, Track, With(SRGB(246, 235, 214, .24f)));
    if (bReady) P.Gradient(8, Track, {With(Gold.CopyWithNewOpacity(.4f)), With(GoldLight), With(SRGB(255, 243, 215))}, true);
    else
    {
        // A third of the track passes along it every 2.5 s, eased in and out.
        const float T = float(FMath::Fmod(Now, 2.5) / 2.5);
        const float Ease = T < .5f ? 2 * T * T : 1 - FMath::Square(-2 * T + 2) / 2;
        const float W = BarW * .34f;
        const float X = Left + FMath::Lerp(-1.1f * W, 3.f * W, Ease);
        const FSlateRect Fill(FMath::Max(X, Track.Left), Track.Top, FMath::Min(X + W, Track.Right), Track.Bottom);
        if (Fill.Right > Fill.Left + 1)
        {
            P.Box(8, FSlateRect(Fill.Left, Fill.Top - 3, Fill.Right, Fill.Bottom + 3), With(Gold.CopyWithNewOpacity(.18f)));
            P.Gradient(9, Fill, {With(GoldLight.CopyWithNewOpacity(0.f)), With(GoldLight), With(SRGB(255, 243, 215))}, true);
        }
    }
    P.Text(7, TEXT("Your journey will begin as soon as the world is ready."), Font(10), FVector2D(Left, BarTop + 16), With(SRGB(210, 208, 201)));
    if (Size.X > 760)
    {
        const float Right = Size.X - Left;
        P.Text(7, TEXT("PERIL & GLORY AWAIT"), Font(9, true, 440), FVector2D(Right, BarTop + 6), With(GoldLight), FVector2D(1, 1));
        P.Text(7, TEXT("ON THE OPEN SEAS"), Font(9, false, 260), FVector2D(Right, BarTop + 10), With(SRGB(230, 221, 205)), FVector2D(1, 0));
    }
    return Layer + 12;
}
