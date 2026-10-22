#include "EWDeathWidget.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "InputCoreTypes.h"

TSharedRef<SWidget> UEWDeathWidget::RebuildWidget()
{
    SetIsFocusable(true);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        Layer = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Layer;
        auto Fill = [this](UWidget* Child)
        {
            auto* Slot = Layer->AddChildToCanvas(Child);
            Slot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f)); Slot->SetOffsets(FMargin(0.f));
            return Slot;
        };
        // The black the screen fades to.
        Black = WidgetTree->ConstructWidget<UBorder>(); Black->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.f)); Black->SetVisibility(ESlateVisibility::HitTestInvisible);
        Fill(Black);
        // Frost closing in from the edges: five stepped bands on each side, thicker towards the middle, so the rim is the iciest.
        FrostOverlay = WidgetTree->ConstructWidget<UOverlay>(); FrostOverlay->SetVisibility(ESlateVisibility::HitTestInvisible);
        Fill(FrostOverlay);
        static const float Bands[5] = { 34.f, 78.f, 130.f, 190.f, 260.f };
        for (int32 Side = 0; Side < 4; ++Side)
            for (float Band : Bands)
            {
                auto* Size = WidgetTree->ConstructWidget<USizeBox>();
                const bool bHorizontalStrip = Side < 2;           // top and bottom strips are wide, left and right are tall
                if (bHorizontalStrip) Size->SetHeightOverride(Band); else Size->SetWidthOverride(Band);
                auto* Ice = WidgetTree->ConstructWidget<UBorder>(); Ice->SetBrushColor(FLinearColor(.72f, .9f, 1.f, .1f)); Size->SetContent(Ice);
                auto* Strip = FrostOverlay->AddChildToOverlay(Size);
                Strip->SetHorizontalAlignment(bHorizontalStrip ? HAlign_Fill : (Side == 2 ? HAlign_Left : HAlign_Right));
                Strip->SetVerticalAlignment(bHorizontalStrip ? (Side == 0 ? VAlign_Top : VAlign_Bottom) : VAlign_Fill);
            }
        FrostOverlay->SetRenderOpacity(0.f);
        // The message and the Respawn button, centred.
        Message = WidgetTree->ConstructWidget<UVerticalBox>();
        auto* Centre = Layer->AddChildToCanvas(Message);
        Centre->SetAnchors(FAnchors(.5f, .5f)); Centre->SetAlignment(FVector2D(.5f, .5f)); Centre->SetAutoSize(true); Centre->SetPosition(FVector2D::ZeroVector);
        auto Text = [this](const FText& Value, int32 Size, const FLinearColor& Colour)
        {
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(Value); Label->SetColorAndOpacity(FSlateColor(Colour)); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = Size; Label->SetFont(Font);
            auto* Slot = Message->AddChildToVerticalBox(Label); Slot->SetPadding(FMargin(0.f, 0.f, 0.f, 12.f)); Slot->SetHorizontalAlignment(HAlign_Center); return Label;
        };
        Text(NSLOCTEXT("Elitewake", "YouDied", "YOU HAVE DIED"), 44, FLinearColor(.88f, .95f, 1.f));
        Text(NSLOCTEXT("Elitewake", "DeathBagNote", "What you carried waits in a bag where you fell for 30 minutes."), 18, FLinearColor(.72f, .8f, .86f));
        RespawnButton = WidgetTree->ConstructWidget<UButton>(); RespawnButton->SetBackgroundColor(FLinearColor(.08f, .26f, .34f, .95f));
        RespawnLabel = WidgetTree->ConstructWidget<UTextBlock>(); RespawnLabel->SetText(NSLOCTEXT("Elitewake", "Respawn", "Respawn  (Enter / A)"));
        { auto Font = RespawnLabel->GetFont(); Font.Size = 24; RespawnLabel->SetFont(Font); }
        RespawnButton->SetContent(RespawnLabel);
        RespawnButton->OnClicked.AddDynamic(this, &UEWDeathWidget::OnRespawnClicked);
        Message->AddChildToVerticalBox(RespawnButton)->SetPadding(FMargin(24.f, 6.f));
        Message->SetVisibility(ESlateVisibility::Collapsed);
        // The red number that jumps off the character when they are hurt.
        DamageText = WidgetTree->ConstructWidget<UTextBlock>(); DamageText->SetColorAndOpacity(FSlateColor(FLinearColor(1.f, .12f, .1f)));
        { auto Font = DamageText->GetFont(); Font.Size = 26; DamageText->SetFont(Font); }
        DamageText->SetShadowOffset(FVector2D(1.5f, 1.5f)); DamageText->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, .8f));
        DamageText->SetVisibility(ESlateVisibility::Collapsed);
        auto* DamageSlot = Layer->AddChildToCanvas(DamageText); DamageSlot->SetAutoSize(true); DamageSlot->SetAlignment(FVector2D(.5f, .5f));
    }
    SetVisibility(ESlateVisibility::HitTestInvisible);
    return Super::RebuildWidget();
}

float UEWDeathWidget::GetFadeAlpha() const
{
    if (bShown) return FMath::Clamp(DeadClock / FadeSeconds, 0.f, 1.f);
    return FMath::Clamp(1.f - ClearClock, 0.f, 1.f);
}

void UEWDeathWidget::ShowDeathScreen(bool bShow)
{
    if (bShown == bShow) return;
    bShown = bShow;
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (bShow)
    {
        DeadClock = 0.f; ClearClock = 1.f;
        if (PC)
        {
            // Whatever menu was open closes; movement and looking stop; the cursor and the controller reach the Respawn button.
            PC->SetInventoryOpen(false); PC->SetMapOpen(false); PC->SetSessionMenuOpen(false); PC->SetOptionsMenuOpen(false);
            PC->SetIgnoreMoveInput(true); PC->SetIgnoreLookInput(true);
            PC->bShowMouseCursor = true;
            FInputModeUIOnly Mode; Mode.SetWidgetToFocus(TakeWidget()); PC->SetInputMode(Mode);
        }
        SetVisibility(ESlateVisibility::Visible);
        if (Message) Message->SetVisibility(ESlateVisibility::Visible);
        if (RespawnButton) RespawnButton->SetIsEnabled(false);
    }
    else
    {
        ClearClock = 0.f;
        if (PC)
        {
            PC->SetIgnoreMoveInput(false); PC->SetIgnoreLookInput(false);
            PC->bShowMouseCursor = false;
            PC->SetInputMode(FInputModeGameOnly());
        }
        if (Message) Message->SetVisibility(ESlateVisibility::Collapsed);
        SetVisibility(ESlateVisibility::HitTestInvisible);
    }
}

bool UEWDeathWidget::Respawn()
{
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!PC || !IsRespawnAvailable()) return false;
    PC->RequestRespawn();
    return true;
}

void UEWDeathWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    UEWSurvivalComponent* Stats = Survivor ? Survivor->GetSurvivalComponent() : nullptr;
    if (!Stats) return;
    ShowDeathScreen(Stats->IsDead());
    if (bShown)
    {
        DeadClock += Delta;
        if (RespawnButton) RespawnButton->SetIsEnabled(IsRespawnAvailable());
    }
    else if (ClearClock < 1.f) ClearClock = FMath::Min(1.f, ClearClock + Delta / 1.2f);
    const float Fade = GetFadeAlpha();
    if (Black) Black->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, Fade));
    // Frost comes in as the black falls, and goes with it.
    if (FrostOverlay) FrostOverlay->SetRenderOpacity(FMath::Clamp(Fade * 1.4f, 0.f, 1.f));
    if (Message) Message->SetRenderOpacity(FMath::Clamp((DeadClock - FadeSeconds * .55f) / (FadeSeconds * .45f), 0.f, 1.f));

    // The red number: one per hit, rising off the survivor's head in a bounce and fading.
    const int32 Count = Stats->GetDamageEventCount();
    if (SeenDamageCount < 0) SeenDamageCount = Count;
    else if (Count != SeenDamageCount)
    {
        SeenDamageCount = Count;
        if (!Stats->IsDead() && DamageText)
        {
            DamageText->SetText(FText::FromString(FString::Printf(TEXT("-%d"), FMath::Max(1, FMath::RoundToInt(Stats->GetLastDamageAmount())))));
            FlashClock = 0.f; ++FlashesShown;
        }
    }
    if (FlashClock >= 0.f && DamageText)
    {
        FlashClock += Delta;
        if (FlashClock >= DamageFlashSeconds || bShown) { FlashClock = -1.f; DamageText->SetVisibility(ESlateVisibility::Collapsed); }
        else
        {
            const float T = FlashClock / DamageFlashSeconds;
            FVector2D Screen;
            if (PC->ProjectWorldLocationToScreen(Survivor->GetActorLocation() + FVector(0.f, 0.f, 110.f), Screen, true))
            {
                const float Scale = FMath::Max(.1f, UWidgetLayoutLibrary::GetViewportScale(this));
                // Up and out in an arc with a bounce: |sin| gives two hops over the flash, each lower than the last.
                const float Hop = FMath::Abs(FMath::Sin(T * PI * 2.f)) * (1.f - T) * 34.f;
                const FVector2D At = Screen / Scale + FVector2D(T * 36.f, -T * 28.f - Hop);
                if (auto* Place = Cast<UCanvasPanelSlot>(DamageText->Slot)) Place->SetPosition(At);
                DamageText->SetRenderOpacity(T < .6f ? 1.f : (1.f - T) / .4f);
                DamageText->SetRenderScale(FVector2D::UnitVector * (1.f + .35f * FMath::Sin(T * PI)));
                DamageText->SetVisibility(ESlateVisibility::HitTestInvisible);
            }
        }
    }
}

FReply UEWDeathWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (!bShown) return Super::NativeOnKeyDown(Geometry, Event);
    const FKey Key = Event.GetKey();
    if ((Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) Respawn();
    return FReply::Handled();      // nothing else works while dead
}
