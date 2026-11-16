#include "Title/EWLoadingWidget.h"
#include "Title/EWFrontEndPaint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Engine/Texture2D.h"
#include "Fonts/CompositeFont.h"
#include "HAL/PlatformTime.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/Paths.h"

namespace
{
constexpr int32 WaveFrameCount = 64;
constexpr double WaveCycleSeconds = 3.2;
constexpr double NoteSeconds = 9.0;

struct FLoadingNote
{
    bool bHistory;
    const TCHAR* Lines[2];
};

constexpr FLoadingNote Notes[] = {
    {false, {TEXT("Aim at a freshwater source to drink."), TEXT("Hold an empty waterskin to fill it.")}},
    // Royal Museums Greenwich collections, object ZAA0037 (H4).
    {true, {TEXT("Harrison finished his H4 sea watch"), TEXT("in 1759 to help find longitude at sea.")}},
    {false, {TEXT("Use the capstan to raise the anchor"), TEXT("before you set sail.")}},
    // Royal Museums Greenwich collections, rmgc-object-43324 (sextant).
    {true, {TEXT("Navigators used a sextant to measure"), TEXT("the angle of the Sun above the horizon.")}},
};
}

void UEWLoadingWidget::ConfigureArt(UTexture2D* Art, UMaterialInterface* WaveMaterial)
{
    VoyageArt = Art;
    if (!Art || !WaveMaterial) return;

    // MoviePlayer paints on its loading thread while the game thread is busy. Prepare immutable
    // phase samples here so NativePaint only selects a brush and never mutates a material.
    WaveFrames.Reserve(WaveFrameCount);
    for (int32 Index = 0; Index < WaveFrameCount; ++Index)
    {
        UMaterialInstanceDynamic* Frame = UMaterialInstanceDynamic::Create(WaveMaterial, this);
        Frame->SetScalarParameterValue(TEXT("WavePhase"), float(2.0 * UE_PI * Index / WaveFrameCount));
        WaveFrames.Add(Frame);
    }
}

TSharedRef<SWidget> UEWLoadingWidget::RebuildWidget()
{
    SetVisibility(ESlateVisibility::HitTestInvisible);
    ForceVolatile(true);
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
    using namespace EWFrontEnd;
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FPainter P{AllottedGeometry, OutDrawElements, Layer};
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const double Now = FPlatformTime::Seconds();
    const float Alpha = FMath::Clamp(Fade, 0.f, 1.f);
    auto Tint = [Alpha](const FLinearColor& C) { return C.CopyWithNewOpacity(C.A * Alpha); };
    P.Box(1, FSlateRect(FVector2D::ZeroVector, Size), Tint(Ground));

    const FVector2D Source = VoyageArt ? FVector2D(VoyageArt->GetSizeX(), VoyageArt->GetSizeY()) : FVector2D(16, 9);
    const FVector2D ArtSize = Source * FMath::Min(Size.X / Source.X, Size.Y / Source.Y);
    const FVector2D TopLeft = (Size - ArtSize) * .5;
    const FSlateRect ArtRect(TopLeft, TopLeft + ArtSize);
    if (VoyageArt)
    {
        const int32 Frame = FMath::FloorToInt(FMath::Fmod(Now, WaveCycleSeconds) * WaveFrames.Num() / WaveCycleSeconds);
        UObject* Resource = WaveFrames.IsValidIndex(Frame) ? static_cast<UObject*>(WaveFrames[Frame].Get()) : VoyageArt.Get();
        P.Image(2, Resource, ArtRect, Tint(FLinearColor::White));
    }

    // Keep the text and bar anchored to the approved image at any viewport aspect ratio.
    const float TipLeft = ArtRect.Left + ArtSize.X * .078f;
    const float TipTop = ArtRect.Top + ArtSize.Y * .302f;
    const double NoteCycle = FMath::Fmod(Now, NoteSeconds * UE_ARRAY_COUNT(Notes));
    const FLoadingNote& Note = Notes[FMath::FloorToInt(NoteCycle / NoteSeconds)];
    const double NoteAge = FMath::Fmod(NoteCycle, NoteSeconds);
    const float NoteAlpha = float(FMath::Clamp(FMath::Min(NoteAge, NoteSeconds - NoteAge) / .30, 0.0, 1.0));
    static const TSharedRef<const FCompositeFont> NoteFont = MakeShared<FCompositeFont>(
        FName(TEXT("Regular")), FPaths::ProjectContentDir() / TEXT("Slate/Fonts/IMFeENrm28P.ttf"),
        EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
    const int32 BodySize = FMath::Clamp(FMath::RoundToInt(ArtSize.X * .022f), 14, 54);
    FSlateFontInfo Heading(NoteFont, FMath::Max(11, BodySize * 3 / 5));
    Heading.LetterSpacing = 280;
    const FSlateFontInfo Body(NoteFont, BodySize);
    const FString Category = Note.bHistory ? TEXT("AGE OF SAIL") : TEXT("VOYAGE TIP");
    P.Text(3, Category, Heading, FVector2D(TipLeft, TipTop), GoldLight.CopyWithNewOpacity(Alpha * NoteAlpha));
    const float TextTop = TipTop + ArtSize.Y * .065f;
    for (int32 Row = 0; Row < UE_ARRAY_COUNT(Note.Lines); ++Row)
        P.Text(3, Note.Lines[Row], Body, FVector2D(TipLeft, TextTop + Row * BodySize * 1.23f),
            Cream.CopyWithNewOpacity(Alpha * NoteAlpha));

    const float Left = ArtRect.Left + ArtSize.X * .066f;
    const float Top = ArtRect.Top + ArtSize.Y * .863f;
    const float Width = ArtSize.X * .315f;
    const float Height = FMath::Max(3.f, float(ArtSize.Y * .011));
    const FSlateRect Track(Left, Top, Left + Width, Top + Height);
    P.Box(4, Track, Tint(Ground.CopyWithNewOpacity(.85f)));
    P.Outline(5, Track, 1.f, Tint(Gold.CopyWithNewOpacity(.7f)));
    if (bReady)
        P.Gradient(6, Track, {Tint(Gold), Tint(GoldLight)}, true);
    else
    {
        const float Travel = float(FMath::Fmod(Now, 2.5) / 2.5);
        const float FillWidth = Width * .26f;
        const float Head = FMath::Lerp(Left, Track.Right + FillWidth, Travel);
        const FSlateRect Fill(FMath::Max(Left, Head - FillWidth), Top + 1, FMath::Min(Track.Right, Head), Track.Bottom - 1);
        if (Fill.Right > Fill.Left + 1)
            P.Gradient(6, Fill, {Tint(Gold.CopyWithNewOpacity(0.f)), Tint(Gold), Tint(GoldLight)}, true);
    }
    return Layer + 7;
}
