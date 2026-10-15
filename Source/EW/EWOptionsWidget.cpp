#include "EWOptionsWidget.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "InputCoreTypes.h"

namespace
{
    const FLinearColor Idle(.04f, .16f, .2f, .92f);
    const FLinearColor Lit(.62f, .46f, .16f, 1.f);   // the selected choice, warm brass against the sea blue
}

bool UEWOptionsWidget::IsSaveShown() const
{
    // Multiplayer has no manual save: the server keeps its players' progress (MULTIPLAYER_RULES).
    return GetWorld() && GetWorld()->GetNetMode() == NM_Standalone;
}

FText UEWOptionsWidget::GetStatus() const { return Status ? Status->GetText() : FText::GetEmpty(); }

TSharedRef<SWidget> UEWOptionsWidget::RebuildWidget()
{
    SetIsFocusable(true);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        // A deep sea-dark veil over the whole screen: in single player the world is paused behind it.
        auto* Root = WidgetTree->ConstructWidget<UBorder>(); Root->SetBrushColor(FLinearColor(.01f, .02f, .03f, .82f));
        Root->SetHorizontalAlignment(HAlign_Center); Root->SetVerticalAlignment(VAlign_Center); WidgetTree->RootWidget = Root;
        auto* Width = WidgetTree->ConstructWidget<USizeBox>(); Width->SetWidthOverride(380); Root->SetContent(Width);
        auto* Body = WidgetTree->ConstructWidget<UVerticalBox>(); Width->SetContent(Body);
        auto Text = [&](const FText& Value, int32 Size, const FLinearColor& Colour)
        {
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(Value); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = Size; Font.LetterSpacing = Size >= 30 ? 300 : 120; Label->SetFont(Font);
            Label->SetColorAndOpacity(Colour); Body->AddChildToVerticalBox(Label)->SetPadding(FMargin(0, 0, 0, 14)); return Label;
        };
        Text(NSLOCTEXT("Elitewake", "OptionsTitle", "OPTIONS"), 38, FLinearColor(.93f, .86f, .7f));
        auto Button = [&](const FText& Value)
        {
            auto* Control = WidgetTree->ConstructWidget<UButton>(); Control->SetBackgroundColor(Idle);
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(Value); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = 22; Font.LetterSpacing = 160; Label->SetFont(Font);
            Control->SetContent(Label); Body->AddChildToVerticalBox(Control)->SetPadding(FMargin(0, 6)); return Control;
        };
        SaveButton = Button(NSLOCTEXT("Elitewake", "OptionsSave", "SAVE GAME"));
        SaveButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::SaveGame); SaveButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverSave);
        MenuButton = Button(NSLOCTEXT("Elitewake", "OptionsMainMenu", "MAIN MENU"));
        MenuButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::MainMenu); MenuButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverMenu);
        Status = Text(FText::GetEmpty(), 14, FLinearColor(.75f, .82f, .84f));
        Text(NSLOCTEXT("Elitewake", "OptionsHint", "Escape returns to the game"), 12, FLinearColor(.5f, .58f, .6f));
        if (!IsSaveShown())
        {
            SaveButton->SetVisibility(ESlateVisibility::Collapsed);
            Selected = 1;
            Status->SetText(NSLOCTEXT("Elitewake", "OptionsServerSaves", "The host's world keeps your progress. Leaving for the main menu ends your session; a host's leaving ends it for everyone."));
        }
        Status->SetAutoWrapText(true);
    }
    return Super::RebuildWidget();
}

void UEWOptionsWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    if (SaveButton) SaveButton->SetBackgroundColor(Selected == 0 ? Lit : Idle);
    if (MenuButton) MenuButton->SetBackgroundColor(Selected == 1 ? Lit : Idle);
}

FReply UEWOptionsWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
    {
        if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetOptionsMenuOpen(false);
        return FReply::Handled();
    }
    const bool bUp = Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool bDown = Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    if (bUp || bDown)
    {
        if (IsSaveShown()) Selected = bUp ? 0 : 1;
        return FReply::Handled();
    }
    if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        if (Selected == 0) SaveGame(); else MainMenu();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UEWOptionsWidget::SaveGame()
{
    Selected = 0;
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!PC || !IsSaveShown() || !Status) return;
    Status->SetText(PC->SaveSurvivorGame()
        ? FText::Format(NSLOCTEXT("Elitewake", "OptionsSaved", "Game saved {0}. Single Player resumes from here."), FText::AsTime(FDateTime::Now()))
        : NSLOCTEXT("Elitewake", "OptionsSaveFailed", "The game could not be saved."));
}

void UEWOptionsWidget::MainMenu()
{
    Selected = 1;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->ReturnToMainMenu();
}
