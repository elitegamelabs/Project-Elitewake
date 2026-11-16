#include "Title/EWTitleWidget.h"
#include "Title/EWFrontEndPaint.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"

TSharedRef<SWidget> UEWTitleWidget::RebuildWidget()
{
    // Focusability is captured when Slate constructs the widget, before NativeConstruct.
    SetIsFocusable(true);
    SetVisibility(ESlateVisibility::Visible);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UBorder* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor::Transparent);
        Root->SetVisibility(ESlateVisibility::HitTestInvisible);
        WidgetTree->RootWidget = Root;
    }
    return Super::RebuildWidget();
}

void UEWTitleWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if (WaterMaterial && Art && WaterMaskArt)
    {
        WaterMaterialInstance = UMaterialInstanceDynamic::Create(WaterMaterial, this);
        WaterMaterialInstance->SetTextureParameterValue(TEXT("TitleImage"), Art);
        WaterMaterialInstance->SetTextureParameterValue(TEXT("WaterMask"), WaterMaskArt);
    }
}

namespace
{
FVector2D ImageSize(const UTexture2D* Texture)
{
    return Texture ? FVector2D(Texture->GetSizeX(), Texture->GetSizeY()) : FVector2D(1672, 941);
}

FSlateRect FitImage(const FVector2D& Size, const UTexture2D* Texture)
{
    const FVector2D Source = ImageSize(Texture);
    const FVector2D Shown = Source * FMath::Min(Size.X / Source.X, Size.Y / Source.Y);
    const FVector2D Corner = (Size - Shown) * .5f;
    return FSlateRect(Corner, Corner + Shown);
}
}

FSlateRect UEWTitleWidget::CardRect(const FVector2D& Size, ECard Card) const
{
    const FSlateRect ArtRect = FitImage(Size, MainMenuArt);
    const FVector2D Shown = ArtRect.GetSize();
    // The bounds follow the gold frames in the supplied menu art.
    const bool bSingle = Card == ECard::SinglePlayer;
    return FSlateRect(ArtRect.Left + Shown.X * (bSingle ? 125. : 850.) / 1672., ArtRect.Top + Shown.Y * 247. / 941.,
        ArtRect.Left + Shown.X * (bSingle ? 821. : 1546.) / 1672., ArtRect.Top + Shown.Y * 743. / 941.);
}

FVector4 UEWTitleWidget::GetSinglePlayerButtonRect() const
{
    const FSlateRect R = CardRect(LastSize, ECard::SinglePlayer);
    return FVector4(R.Left, R.Top, R.GetSize().X, R.GetSize().Y);
}

void UEWTitleWidget::ContinueToMenu()
{
    if (Screen != EEWTitleScreen::Splash) return;
    Screen = EEWTitleScreen::MainMenu;
    HighlightCard(ECard::None, false);
    OnContinue.ExecuteIfBound();
}

void UEWTitleWidget::StartJourney()
{
    if (Screen == EEWTitleScreen::Splash) ContinueToMenu();
    else StartSinglePlayer();
}

void UEWTitleWidget::StartSinglePlayer()
{
    if (Screen != EEWTitleScreen::MainMenu) return;
    OnSinglePlayer.ExecuteIfBound();
}

void UEWTitleWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    LastSize = Geometry.GetLocalSize();
    if (Screen == EEWTitleScreen::Splash && WaterMaterialInstance)
    {
        // Feed Slate's material an explicit clock in both Editor Play and standalone.
        TitleMotionTime += DeltaTime;
        WaterMaterialInstance->SetScalarParameterValue(TEXT("TitleMotionTime"), TitleMotionTime);
    }
    if (HighlightedCard != ECard::None)
    {
        const float PreviousGlow = Glow;
        Glow = FMath::FInterpTo(Glow, 1.f, DeltaTime, 9.f);
        if (!FMath::IsNearlyEqual(Glow, PreviousGlow)) InvalidateLayoutAndVolatility();
    }
}

void UEWTitleWidget::HighlightCard(ECard Card, bool bFromMouse)
{
    bMouseHighlight = bFromMouse;
    if (HighlightedCard != Card)
    {
        HighlightedCard = Card;
        Glow = 0.f;
        InvalidateLayoutAndVolatility();
    }
}

FReply UEWTitleWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Screen == EEWTitleScreen::MainMenu)
    {
        const FVector2D Point = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
        const FVector2D Size = Geometry.GetLocalSize();
        HighlightCard(CardRect(Size, ECard::SinglePlayer).ContainsPoint(Point) ? ECard::SinglePlayer :
            CardRect(Size, ECard::Multiplayer).ContainsPoint(Point) ? ECard::Multiplayer : ECard::None, true);
    }
    return FReply::Handled();
}

void UEWTitleWidget::NativeOnMouseLeave(const FPointerEvent& Event)
{
    Super::NativeOnMouseLeave(Event);
    if (bMouseHighlight) HighlightCard(ECard::None, true);
}

FReply UEWTitleWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Screen == EEWTitleScreen::Splash)
    {
        ContinueToMenu();
        return FReply::Handled();
    }
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton && Event.GetEffectingButton() != EKeys::RightMouseButton)
        return FReply::Unhandled();
    if (CardRect(Geometry.GetLocalSize(), ECard::SinglePlayer).ContainsPoint(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition())))
    {
        StartSinglePlayer();
        return FReply::Handled();
    }
    // Multiplayer is intentionally a non-interactive preview.
    return FReply::Handled();
}

FReply UEWTitleWidget::NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Screen == EEWTitleScreen::Splash && !FMath::IsNearlyZero(Event.GetWheelDelta()))
    {
        ContinueToMenu();
        return FReply::Handled();
    }
    return Super::NativeOnMouseWheel(Geometry, Event);
}

FReply UEWTitleWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Screen == EEWTitleScreen::Splash)
    {
        ContinueToMenu();
        if (Key.IsGamepadKey()) HighlightCard(ECard::SinglePlayer, false);
        return FReply::Handled();
    }
    if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left)
        HighlightCard(ECard::SinglePlayer, false);
    else if (Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right)
        HighlightCard(ECard::Multiplayer, false);
    else if (!Event.IsRepeat() && Key == EKeys::Gamepad_FaceButton_Bottom && HighlightedCard == ECard::SinglePlayer)
        StartSinglePlayer();
    return FReply::Handled();
}

FReply UEWTitleWidget::NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event)
{
    if (Event.GetKey() != EKeys::Gamepad_LeftX) return Super::NativeOnAnalogValueChanged(Geometry, Event);
    const float Value = Event.GetAnalogValue();
    if (FMath::Abs(Value) < .3f) StickDirection = 0;
    else if (FMath::Abs(Value) > .55f)
    {
        const int32 Direction = Value < 0.f ? -1 : 1;
        if (Direction != StickDirection && Screen == EEWTitleScreen::MainMenu)
            HighlightCard(Direction < 0 ? ECard::SinglePlayer : ECard::Multiplayer, false);
        StickDirection = Direction;
    }
    return FReply::Handled();
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
    auto Brush = [&](int32 L, UObject* Image, const FVector2D& ImageSize, const FSlateRect& Rect, const FLinearColor& Tint = FLinearColor::White)
    {
        if (!Image) return;
        FSlateBrush SlateBrush;
        SlateBrush.SetResourceObject(Image);
        SlateBrush.ImageSize = ImageSize;
        Box(L, Rect, &SlateBrush, Tint);
    };

    Box(1, FSlateRect(FVector2D::ZeroVector, Size), White, FLinearColor::Black);
    if (Screen == EEWTitleScreen::Splash)
    {
        const FVector2D BackgroundSize = ImageSize(Art);
        const FSlateRect Background = EWFrontEnd::Cover(Size, BackgroundSize);
        Brush(2, WaterMaterialInstance ? static_cast<UObject*>(WaterMaterialInstance.Get()) : static_cast<UObject*>(Art.Get()), BackgroundSize, Background);
    }
    else
    {
        const FSlateRect ArtRect = FitImage(Size, MainMenuArt);
        Brush(2, MainMenuArt, ImageSize(MainMenuArt), ArtRect);
        if (HighlightedCard != ECard::None && Glow > .01f)
        {
            const FSlateRect R = CardRect(Size, HighlightedCard);
            const float Scale = FMath::Max(.4f, ArtRect.GetSize().Y / 941.f);
            const EWFrontEnd::FPainter Painter{AllottedGeometry, OutDrawElements, Layer};
            auto Outline = [&](float Pad, float Width, float Alpha)
            {
                const float Margin = Pad * Scale;
                Painter.Outline(3, FSlateRect(R.Left - Margin, R.Top - Margin, R.Right + Margin, R.Bottom + Margin),
                    Width * Scale, FLinearColor(1.f, .59f, .23f, Alpha * Glow));
            };
            Outline(7.f, 9.f, .08f);
            Outline(4.f, 6.f, .16f);
            Outline(1.f, 2.f, .65f);
        }
    }

    return Layer + 7;
}
