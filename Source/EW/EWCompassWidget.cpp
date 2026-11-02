#include "EWCompassWidget.h"
#include "EWArrivalComponent.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "Ships/EWShip.h"
#include "Ships/EWWindSubsystem.h"
#include "World/EWNorth.h"
#include "Camera/PlayerCameraManager.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace
{
const FLinearColor CompassInk(.93f, .9f, .82f);           // bearings
const FLinearColor CompassNorth(1.f, .55f, .35f);         // N stands out
const FLinearColor CompassWind(.55f, .8f, 1.f);        // the wind, as the ship markers' working blue
const FLinearColor CompassGood(.45f, 1.f, .45f);
const FLinearColor CompassPlace(1.f, .78f, .3f);         // the town step's place: a square, gold, with its distance
// The same compass strip location with a darker, more opaque plate for sea/sky contrast.
const FLinearColor CompassBacking(.008f, .014f, .022f, .82f);

float Bearing(float Yaw) { return EWNorth::BearingOfYaw(Yaw); }

FString PointName(int32 Degrees)
{
    static const TCHAR* Names[] = {TEXT("N"), TEXT("NE"), TEXT("E"), TEXT("SE"), TEXT("S"), TEXT("SW"), TEXT("W"), TEXT("NW")};
    return Names[(Degrees / 45) % 8];
}
}

void UEWCompassWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    bShown = Survivor && !PC->IsInventoryOpen() && !PC->IsMapOpen();
    bShowTrim = false;
    if (!bShown) return;
    Heading = Bearing(PC->PlayerCameraManager ? PC->PlayerCameraManager->GetCameraRotation().Yaw : PC->GetControlRotation().Yaw);
    const UEWWindSubsystem* Wind = GetWorld() ? GetWorld()->GetSubsystem<UEWWindSubsystem>() : nullptr;
    WindFrom = Bearing((Wind ? Wind->GetWindYaw() : 0.f) + 180.f);
    // In Saltreach, where the shown town step is done (slice 5).
    FVector Place;
    const UEWArrivalComponent* Arrival = Survivor->GetArrivalComponent();
    bShowPlace = Arrival && Arrival->GetTownTarget(Place);
    if (bShowPlace)
    {
        const FVector To = Place - Survivor->GetActorLocation();
        PlaceBearing = EWNorth::BearingOf(To);
        PlaceMetres = FMath::RoundToInt(To.Size2D() / 100.f);
    }

    const AEWShip* Ship = Survivor->GetHelmShip();
    if (!Ship || !Ship->HasTrimmableSails()) return;
    bShowTrim = true;
    SailAngle = Ship->GetSailAngle();
    BestSailAngle = Ship->GetBestSailAngle();
    TrimQuality = Ship->GetTrimQuality();
    MaxSailAngle = AEWShip::MaxSailAngle;
    // Running before the wind the sails draw on either side; aim for the nearer.
    float Target = BestSailAngle;
    if (FMath::Abs(BestSailAngle) > MaxSailAngle - 10.f && FMath::Abs(SailAngle + BestSailAngle) < FMath::Abs(SailAngle - BestSailAngle))
        Target = -BestSailAngle;
    if (TrimQuality >= .9f) TrimAdvice = TEXT("Sails drawing well");
    else if (Target > SailAngle) TrimAdvice = TEXT("Trim to starboard: Shift + D");
    else TrimAdvice = TEXT("Trim to port: Shift + A");
}

int32 UEWCompassWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    if (!bShown) return Layer;
    const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");
    const TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
    const float Centre = AllottedGeometry.GetLocalSize().X * .5f;
    const float Top = 14.f;
    const float Width = FMath::Min(StripWidth, AllottedGeometry.GetLocalSize().X - 32.f);
    const float PerDegree = Width / SpanDegrees;
    const float Half = SpanDegrees * .5f;

    auto Box = [&](int32 L, FVector2f At, FVector2f Size, const FLinearColor& Colour)
    {
        FSlateDrawElement::MakeBox(OutDrawElements, Layer + L, AllottedGeometry.ToPaintGeometry(Size, FSlateLayoutTransform(At)),
            White, ESlateDrawEffect::None, Colour);
    };
    auto Text = [&](const FString& String, const FSlateFontInfo& Font, FVector2f CentreTop, const FLinearColor& Colour)
    {
        const FVector2D Size = Measure->Measure(String, Font);
        FSlateDrawElement::MakeText(OutDrawElements, Layer + 3,
            AllottedGeometry.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(CentreTop - FVector2f(Size.X * .5f, 0))),
            String, Font, ESlateDrawEffect::None, Colour);
        return FVector2f(Size);
    };
    // Bearings fade toward the strip's ends.
    auto Fade = [&](float Offset) { return FMath::Clamp(1.f - FMath::Square(Offset / Half), 0.f, 1.f); };

    Box(1, FVector2f(Centre - Width * .5f, Top), FVector2f(Width, StripHeight), CompassBacking);
    const int32 First = FMath::CeilToInt((Heading - Half) / 5.f) * 5;
    for (int32 Degrees = First; Degrees <= Heading + Half; Degrees += 5)
    {
        const float Offset = Degrees - Heading;
        const float Alpha = Fade(Offset);
        if (Alpha <= .02f) continue;
        const float X = Centre + Offset * PerDegree;
        const int32 Point = ((Degrees % 360) + 360) % 360;
        if (Point % 45 == 0)
        {
            const bool bCardinal = Point % 90 == 0;
            const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", bCardinal ? 15 : 11);
            const FLinearColor Colour = (Point == 0 ? CompassNorth : CompassInk).CopyWithNewOpacity(Alpha);
            Text(PointName(Point), Font, FVector2f(X, Top + (bCardinal ? 6.f : 9.f)), Colour);
        }
        else if (Point % 15 == 0)
        {
            Box(2, FVector2f(X - .5f, Top + StripHeight - 10.f), FVector2f(1.f, 10.f), CompassInk.CopyWithNewOpacity(.8f * Alpha));
            Text(FString::FromInt(Point), FCoreStyle::GetDefaultFontStyle("Regular", 8), FVector2f(X, Top + 4.f), CompassInk.CopyWithNewOpacity(.7f * Alpha));
        }
        else Box(2, FVector2f(X - .5f, Top + StripHeight - 6.f), FVector2f(1.f, 6.f), CompassInk.CopyWithNewOpacity(.6f * Alpha));
    }
    // The fixed centre mark and the bearing faced.
    Box(2, FVector2f(Centre - 1.f, Top - 4.f), FVector2f(2.f, StripHeight + 8.f), CompassInk.CopyWithNewOpacity(.9f));
    const FString Faced = FString::Printf(TEXT("%03d"), FMath::RoundToInt(Heading) % 360);
    Text(Faced, FCoreStyle::GetDefaultFontStyle("Bold", 10), FVector2f(Centre, Top + StripHeight + 4.f), CompassInk);

    // The wind, where it blows from; off the strip it waits at the nearer end, pointing the way.
    {
        const float Offset = FRotator::NormalizeAxis(WindFrom - Heading);
        const bool bOnStrip = FMath::Abs(Offset) <= Half - 6.f;
        const float X = Centre + FMath::Clamp(Offset, -(Half - 6.f), Half - 6.f) * PerDegree;
        const FString Label = bOnStrip ? TEXT("WIND") : Offset < 0.f ? TEXT("< WIND") : TEXT("WIND >");
        Box(2, FVector2f(X - 1.5f, Top), FVector2f(3.f, StripHeight), CompassWind.CopyWithNewOpacity(bOnStrip ? .9f : .5f));
        Text(Label, FCoreStyle::GetDefaultFontStyle("Bold", 9), FVector2f(X, Top + StripHeight + (FMath::Abs(X - Centre) < 30.f ? 18.f : 4.f)), CompassWind);
    }

    // The town step's place: a gold square on the strip's lower edge with its distance beneath; off the strip it waits at the nearer end.
    if (bShowPlace)
    {
        const float Offset = FRotator::NormalizeAxis(PlaceBearing - Heading);
        const bool bOnStrip = FMath::Abs(Offset) <= Half - 6.f;
        const float X = Centre + FMath::Clamp(Offset, -(Half - 6.f), Half - 6.f) * PerDegree;
        Box(2, FVector2f(X - 7.f, Top + StripHeight - 16.f), FVector2f(14.f, 14.f), CompassBacking);
        Box(3, FVector2f(X - 5.f, Top + StripHeight - 14.f), FVector2f(10.f, 10.f), CompassPlace.CopyWithNewOpacity(bOnStrip ? 1.f : .6f));
        const FString Label = bOnStrip ? FString::Printf(TEXT("%d m"), PlaceMetres)
            : Offset < 0.f ? FString::Printf(TEXT("< %d m"), PlaceMetres) : FString::Printf(TEXT("%d m >"), PlaceMetres);
        Text(Label, FCoreStyle::GetDefaultFontStyle("Bold", 10), FVector2f(X, Top + StripHeight + 32.f), CompassPlace);
    }

    if (!bShowTrim) return Layer + 4;
    // The sails' trim: a bar from port to starboard, the best angle shaded, and where the sails are.
    const float BarWidth = 300.f, BarTop = Top + StripHeight + 40.f;
    const float BarLeft = Centre - BarWidth * .5f;
    auto AngleX = [&](float Angle) { return Centre + Angle / MaxSailAngle * BarWidth * .5f; };
    Box(1, FVector2f(BarLeft - 8.f, BarTop - 22.f), FVector2f(BarWidth + 16.f, 64.f), CompassBacking);
    Text(TEXT("SAILS"), FCoreStyle::GetDefaultFontStyle("Bold", 9), FVector2f(Centre, BarTop - 19.f), CompassInk);
    Text(TEXT("Port"), FCoreStyle::GetDefaultFontStyle("Regular", 8), FVector2f(BarLeft + 14.f, BarTop - 17.f), CompassInk.CopyWithNewOpacity(.7f));
    Text(TEXT("Starboard"), FCoreStyle::GetDefaultFontStyle("Regular", 8), FVector2f(BarLeft + BarWidth - 26.f, BarTop - 17.f), CompassInk.CopyWithNewOpacity(.7f));
    Box(2, FVector2f(BarLeft, BarTop), FVector2f(BarWidth, 10.f), CompassInk.CopyWithNewOpacity(.18f));
    auto Shade = [&](float Best)
    {
        const float From = AngleX(FMath::Clamp(Best - 18.f, -MaxSailAngle, MaxSailAngle));
        const float To = AngleX(FMath::Clamp(Best + 18.f, -MaxSailAngle, MaxSailAngle));
        Box(2, FVector2f(From, BarTop), FVector2f(FMath::Max(To - From, 2.f), 10.f), CompassGood.CopyWithNewOpacity(.45f));
    };
    Shade(BestSailAngle);
    if (FMath::Abs(BestSailAngle) > MaxSailAngle - 10.f) Shade(-BestSailAngle);
    Box(2, FVector2f(Centre - .5f, BarTop - 3.f), FVector2f(1.f, 16.f), CompassInk.CopyWithNewOpacity(.5f));
    const FLinearColor Marker = FMath::Lerp(FLinearColor(1.f, .45f, .3f), CompassGood, TrimQuality);
    Box(3, FVector2f(AngleX(SailAngle) - 2.5f, BarTop - 4.f), FVector2f(5.f, 18.f), Marker);
    Text(FString::Printf(TEXT("%s  -  %d%%"), *TrimAdvice, FMath::RoundToInt(TrimQuality * 100.f)),
        FCoreStyle::GetDefaultFontStyle("Bold", 10), FVector2f(Centre, BarTop + 16.f), TrimQuality >= .9f ? CompassGood : CompassInk);
    return Layer + 4;
}
