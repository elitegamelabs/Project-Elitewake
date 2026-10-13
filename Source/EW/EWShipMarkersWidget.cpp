#include "EWShipMarkersWidget.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "EngineUtils.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace
{
const FLinearColor Empty(1.f, .72f, .25f);          // a mount waiting for a fitting
const FLinearColor Fits(.45f, 1.f, .45f);           // a mount a carried fitting fits
const FLinearColor Fitted(.85f, .87f, .9f);         // something already in place
const FLinearColor Working(.55f, .8f, 1.f);         // the anchor, the hold, the ladders

FString SailSizeName(EEWSailSize Size)
{
    return Size == EEWSailSize::Large ? TEXT("Large") : Size == EEWSailSize::Medium ? TEXT("Medium") : TEXT("Small");
}
}

void UEWShipMarkersWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    Markers.Reset();
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Survivor || !GetWorld() || PC->IsInventoryOpen() || PC->IsMapOpen()) return;
    const float Scale = FMath::Max(UWidgetLayoutLibrary::GetViewportScale(this), .01f);
    const FVector Here = Survivor->GetActorLocation();

    // The fittings the survivor carries, to show where each would go.
    TArray<const UEWItemDefinition*> Carried;
    if (const UEWInventoryComponent* Inventory = Survivor->GetInventoryComponent())
        for (const FEWInventoryEntry& Entry : Inventory->GetInventoryEntries())
            if (Entry.ItemDefinition && Entry.Quantity > 0 && Entry.ItemDefinition->FittingMountType != EEWShipMountType::None)
                Carried.Add(Entry.ItemDefinition);

    auto Add = [&](const FVector& Where, const FString& Label, const FLinearColor& Colour, bool bAimed, bool bFits)
    {
        const float Distance = FVector::Dist(Here, Where);
        FVector2D Screen;
        if (Distance > Range || !PC->ProjectWorldLocationToScreen(Where, Screen, true)) return;
        FEWShipMarker Marker;
        Marker.Position = Screen / Scale;
        Marker.Label = Label;
        Marker.Colour = Colour;
        Marker.bAimed = bAimed;
        Marker.bFits = bFits;
        Marker.Strength = FMath::Clamp(1.5f - Distance / Range, .35f, 1.f);
        Markers.Add(Marker);
    };

    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        AEWShip* Ship = *It;
        const UEWShipDefinition* Def = Ship ? Ship->Definition.Get() : nullptr;
        if (!Def || FVector::Dist(Here, Ship->GetActorLocation()) > Range + Def->HullExtent.X) continue;
        const bool bHelmsman = Ship->GetHelmsman() == Survivor;
        // From outside, the deck's places would show through the hull: only the anchor and the near ladders.
        const bool bOutside = !Ship->IsAboard(Survivor) && !bHelmsman;
        const FName Aimed = Ship->FindAimedMount(Survivor);
        // The helmsman needs only the anchor: their sails and wheel are already in hand.
        if (!bOutside && !bHelmsman) for (const FEWShipMount& Mount : Def->Mounts)
        {
            const FVector Where = Ship->GetMountWorldTransform(Mount.MountId).GetLocation();
            const UEWItemDefinition* Installed = Ship->GetFitting(Mount.MountId);
            const bool bThis = Aimed == Mount.MountId;
            if (Mount.Type == EEWShipMountType::Helm)
            {
                if (bHelmsman) continue;
                if (Installed) Add(Where, Def->bPaddled ? TEXT("Paddles") : TEXT("Helm"), Fitted, bThis, false);
                else
                {
                    const bool bFits = Carried.ContainsByPredicate([&](const UEWItemDefinition* I) { return UEWShipDefinition::Accepts(Mount, I); });
                    Add(Where, bFits ? TEXT("Fit the wheel here") : TEXT("Wheel mount"), bFits ? Fits : Empty, bThis, bFits);
                }
            }
            else if (Mount.Type == EEWShipMountType::Sail)
            {
                const FString Size = SailSizeName(Mount.SailSize);
                if (Installed) Add(Where, FString::Printf(TEXT("%s sail"), *Size), Fitted, bThis, false);
                else
                {
                    const bool bFits = Carried.ContainsByPredicate([&](const UEWItemDefinition* I) { return UEWShipDefinition::Accepts(Mount, I); });
                    Add(Where, bFits ? FString::Printf(TEXT("Fit %s sail here"), *Size) : FString::Printf(TEXT("%s sail mount"), *Size),
                        bFits ? Fits : Empty, bThis, bFits);
                }
            }
            else if (Mount.Type == EEWShipMountType::Cannon && !Installed && FVector::Dist(Here, Where) < Range * .5f)
            {
                Add(Where, TEXT("Cannon port"), Empty * FLinearColor(1, 1, 1, .7f), bThis, false);
            }
        }
        Add(Ship->GetAnchorPointWorld() + FVector(0, 0, 40), Ship->IsAnchored() ? TEXT("Anchor (down) - raise") : TEXT("Anchor (up) - drop"),
            Working, Ship->IsAimingAtAnchor(Survivor), false);
        if (!bHelmsman && !bOutside) Add(Ship->GetCargoHatchWorld() + FVector(0, 0, 30), TEXT("Hold"), Working, Ship->IsAimingAtCargoHatch(Survivor), false);
        if (bOutside && !Survivor->IsOnLadder())
        {
            const int32 AimedLadder = Ship->FindAimedBoardingPoint(Survivor);
            const float Side = Ship->GetActorTransform().InverseTransformPosition(Here).Y;
            for (int32 Index = 0; Index < Def->BoardingPoints.Num(); ++Index)
            {
                const FVector Point = Ship->GetBoardingPointWorld(Index);
                const float LadderSide = Ship->GetActorTransform().InverseTransformPosition(Point).Y;
                if (Side * LadderSide < 0.f && FMath::Abs(Side) > 100.f) continue;   // on the far side of the hull
                Add(Point + FVector(0, 0, 140), TEXT("Ladder"), Working, AimedLadder == Index, false);
            }
        }
    }
}

int32 UEWShipMarkersWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");
    const TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
    // The aimed and nearest labels keep their place; any other that would cover one is lifted above it.
    TArray<int32> Order;
    for (int32 Index = 0; Index < Markers.Num(); ++Index) Order.Add(Index);
    Order.Sort([this](int32 A, int32 B)
    {
        return Markers[A].bAimed != Markers[B].bAimed ? Markers[A].bAimed : Markers[A].Strength > Markers[B].Strength;
    });
    TArray<FSlateRect> Taken;
    for (const int32 Index : Order)
    {
        const FEWShipMarker& Marker = Markers[Index];
        const float Alpha = Marker.Strength;
        const float Dot = Marker.bAimed ? 14.f : 9.f;
        // A dot on the place itself, with a dark rim.
        FSlateDrawElement::MakeBox(OutDrawElements, Layer + 1,
            AllottedGeometry.ToPaintGeometry(FVector2f(Dot + 4, Dot + 4), FSlateLayoutTransform(FVector2f(Marker.Position) - FVector2f(Dot / 2 + 2))),
            White, ESlateDrawEffect::None, FLinearColor(0, 0, 0, .6f * Alpha));
        FSlateDrawElement::MakeBox(OutDrawElements, Layer + 2,
            AllottedGeometry.ToPaintGeometry(FVector2f(Dot, Dot), FSlateLayoutTransform(FVector2f(Marker.Position) - FVector2f(Dot / 2))),
            White, ESlateDrawEffect::None, Marker.Colour.CopyWithNewOpacity(Alpha));
        // Its label on a dark tab just above.
        const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", Marker.bAimed ? 15 : 11);
        const FVector2D Size = Measure->Measure(Marker.Label, Font);
        const FVector2f Tab(Size.X + 12.f, Size.Y + 4.f);
        FVector2f TabAt = FVector2f(Marker.Position) - FVector2f(Tab.X / 2, Tab.Y + Dot);
        for (int32 Tries = 0; Tries < 6; ++Tries)
        {
            const FSlateRect Here(TabAt.X, TabAt.Y, TabAt.X + Tab.X, TabAt.Y + Tab.Y);
            const FSlateRect* Covered = Taken.FindByPredicate([&](const FSlateRect& R) { return FSlateRect::DoRectanglesIntersect(R, Here); });
            if (!Covered) break;
            TabAt.Y = Covered->Top - Tab.Y - 2.f;
        }
        Taken.Add(FSlateRect(TabAt.X, TabAt.Y, TabAt.X + Tab.X, TabAt.Y + Tab.Y));
        if (TabAt.Y + Tab.Y < Marker.Position.Y - Dot - 2.f)
        {
            // A lifted label keeps a thin line down to its place.
            TArray<FVector2f> Line{FVector2f(Marker.Position) - FVector2f(0, Dot / 2), FVector2f(Marker.Position.X, TabAt.Y + Tab.Y)};
            FSlateDrawElement::MakeLines(OutDrawElements, Layer + 1, AllottedGeometry.ToPaintGeometry(), Line, ESlateDrawEffect::None,
                Marker.Colour.CopyWithNewOpacity(.6f * Alpha), true, 1.f);
        }
        FSlateDrawElement::MakeBox(OutDrawElements, Layer + 1, AllottedGeometry.ToPaintGeometry(Tab, FSlateLayoutTransform(TabAt)),
            White, ESlateDrawEffect::None, FLinearColor(.02f, .03f, .04f, (Marker.bAimed ? .85f : .6f) * Alpha));
        FSlateDrawElement::MakeText(OutDrawElements, Layer + 2,
            AllottedGeometry.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(TabAt + FVector2f(6, 2))),
            Marker.Label, Font, ESlateDrawEffect::None, Marker.Colour.CopyWithNewOpacity(Alpha));
    }
    return Layer + 3;
}
