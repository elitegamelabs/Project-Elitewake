#include "Title/EWTitleWidget.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

void UEWTitleWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);
    SetKeyboardFocus();
    if (WaterMaterial && Art && WaterMaskArt)
    {
        WaterMaterialInstance = UMaterialInstanceDynamic::Create(WaterMaterial, this);
        WaterMaterialInstance->SetTextureParameterValue(TEXT("TitleImage"), Art);
        WaterMaterialInstance->SetTextureParameterValue(TEXT("WaterMask"), WaterMaskArt);
    }
}

FSlateRect UEWTitleWidget::CoverRect(const FVector2D& Size, const UTexture2D* Texture) const
{
    const FVector2D Source = Texture ? FVector2D(Texture->GetSizeX(), Texture->GetSizeY()) : FVector2D(16, 9);
    const float Scale = FMath::Max(Size.X / Source.X, Size.Y / Source.Y);
    const FVector2D Shown = Source * Scale;
    const FVector2D Corner = (Size - Shown) * .5f;
    return FSlateRect(Corner, Corner + Shown);
}

FSlateRect UEWTitleWidget::SinglePlayerRect(const FVector2D& Size) const
{
    const FSlateRect A = CoverRect(Size, MainMenuArt);
    const FVector2D Shown = A.GetSize();
    return FSlateRect(A.Left + Shown.X * SingleLeft, A.Top + Shown.Y * SingleTop,
        A.Left + Shown.X * SingleRight, A.Top + Shown.Y * SingleBottom);
}

FVector4 UEWTitleWidget::GetSinglePlayerButtonRect() const
{
    const FSlateRect R = SinglePlayerRect(LastSize);
    return FVector4(R.Left, R.Top, R.GetSize().X, R.GetSize().Y);
}

void UEWTitleWidget::ContinueToMenu()
{
    if (Screen != EEWTitleScreen::Splash) return;
    Screen = EEWTitleScreen::MainMenu;
    Age = 0.f;
    Glow = 0.f;
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
    Age += DeltaTime;
    Glow = FMath::FInterpTo(Glow, bHovered ? 1.f : 0.f, DeltaTime, 8.f);
}

FReply UEWTitleWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Screen == EEWTitleScreen::Splash)
    {
        bHovered = false;
    }
    else
    {
        bHovered = SinglePlayerRect(Geometry.GetLocalSize()).ContainsPoint(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition()));
    }
    return FReply::Handled();
}

FReply UEWTitleWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();
    if (Screen == EEWTitleScreen::Splash)
    {
        ContinueToMenu();
        return FReply::Handled();
    }
    if (SinglePlayerRect(Geometry.GetLocalSize()).ContainsPoint(Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition())))
    {
        StartSinglePlayer();
        return FReply::Handled();
    }
    // Multiplayer is intentionally a non-interactive preview.
    return FReply::Handled();
}

FReply UEWTitleWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (Screen == EEWTitleScreen::Splash)
    {
        ContinueToMenu();
        return FReply::Handled();
    }
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        StartSinglePlayer();
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
        const FSlateRect Background = CoverRect(Size, Art);
        const FVector2D BackgroundSize = Art ? FVector2D(Art->GetSizeX(), Art->GetSizeY()) : Size;
        Brush(2, WaterMaterialInstance ? static_cast<UObject*>(WaterMaterialInstance.Get()) : static_cast<UObject*>(Art.Get()), BackgroundSize, Background);

        // Keep the key prompt separate from the supplied title art so only the water is animated.
        const float PromptW = Size.X * .40f;
        const float PromptH = PromptArt ? PromptW * PromptArt->GetSizeY() / PromptArt->GetSizeX() : Size.Y * .09f;
        const FVector2D PromptTop((Size.X - PromptW) * .5f, Size.Y * .865f);
        const float Pulse = .78f + .22f * FMath::Sin(Age * 2.6f);
        Brush(4, PromptArt, FVector2D(PromptArt ? PromptArt->GetSizeX() : 1, PromptArt ? PromptArt->GetSizeY() : 1),
            FSlateRect(PromptTop, PromptTop + FVector2D(PromptW, PromptH)), FLinearColor(1.f, 1.f, 1.f, Pulse));
    }
    else
    {
        Brush(2, MainMenuArt, MainMenuArt ? FVector2D(MainMenuArt->GetSizeX(), MainMenuArt->GetSizeY()) : Size,
            CoverRect(Size, MainMenuArt));
        if (Glow > .01f)
        {
            const FSlateRect R = SinglePlayerRect(Size);
            const FVector2D Pad(4.f, 4.f);
            Box(3, FSlateRect(R.GetTopLeft() - Pad, R.GetBottomRight() + Pad), White,
                FLinearColor(1.f, .78f, .45f, .08f * Glow));
        }
    }

    return Layer + 7;
}
