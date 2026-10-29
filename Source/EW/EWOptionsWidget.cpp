#include "EWOptionsWidget.h"

#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "InputCoreTypes.h"

namespace
{
    const FLinearColor Idle(.04f, .16f, .2f, .92f);
    const FLinearColor Lit(.1f, .62f, .78f, 1.f);
    constexpr float MinBrightness = -.5f;
    constexpr float MaxBrightness = .5f;
    constexpr float MinSensitivity = .1f;
    constexpr float MaxSensitivity = 3.f;

    float Normalize(float Value, float Min, float Max) { return (Value - Min) / (Max - Min); }
    float Denormalize(float Value, float Min, float Max) { return Min + FMath::Clamp(Value, 0.f, 1.f) * (Max - Min); }
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
        auto* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor(.01f, .02f, .03f, .9f));
        Root->SetHorizontalAlignment(HAlign_Center);
        Root->SetVerticalAlignment(VAlign_Center);
        WidgetTree->RootWidget = Root;

        auto* Width = WidgetTree->ConstructWidget<USizeBox>();
        Width->SetWidthOverride(560);
        Root->SetContent(Width);
        auto* Body = WidgetTree->ConstructWidget<UVerticalBox>();
        Width->SetContent(Body);

        auto Text = [&](const FText& Value, int32 Size, const FLinearColor& Colour)
        {
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
            Label->SetText(Value);
            Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = Size; Font.LetterSpacing = Size >= 30 ? 300 : 100;
            Label->SetFont(Font); Label->SetColorAndOpacity(Colour);
            Body->AddChildToVerticalBox(Label)->SetPadding(FMargin(0, 0, 0, 10));
            return Label;
        };
        Text(NSLOCTEXT("Elitewake", "OptionsTitle", "PAUSED"), 34, FLinearColor(.93f, .86f, .7f));
        auto* TabRow = WidgetTree->ConstructWidget<UHorizontalBox>();
        Body->AddChildToVerticalBox(TabRow)->SetPadding(FMargin(0, 0, 0, 14));
        for (int32 Index = 0; Index < 2; ++Index)
        {
            auto* TabButton = WidgetTree->ConstructWidget<UButton>();
            auto* TabLabel = WidgetTree->ConstructWidget<UTextBlock>();
            TabLabel->SetText(Index == 0 ? NSLOCTEXT("Elitewake", "PauseTab", "PAUSE") : NSLOCTEXT("Elitewake", "OptionsTab", "OPTIONS"));
            TabLabel->SetJustification(ETextJustify::Center);
            auto TabFont = TabLabel->GetFont(); TabFont.Size = 16; TabFont.LetterSpacing = 160; TabLabel->SetFont(TabFont);
            TabButton->SetContent(TabLabel);
            if (Index == 0) TabButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::ShowPauseTab);
            else TabButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::ShowOptionsTab);
            auto* TabSlot = TabRow->AddChildToHorizontalBox(TabButton);
            TabSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); TabSlot->SetPadding(FMargin(0, 0, Index == 0 ? 4 : 0, 0));
            TabButtons.Add(TabButton);
        }
        OptionsPage = WidgetTree->ConstructWidget<UVerticalBox>();
        Body->AddChildToVerticalBox(OptionsPage);
        PausePage = WidgetTree->ConstructWidget<UVerticalBox>();
        Body->AddChildToVerticalBox(PausePage);

        auto AddSetting = [&](const FText& Name, float InitialValue) -> USlider*
        {
            auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
            OptionsPage->AddChildToVerticalBox(Row)->SetPadding(FMargin(4, 4));
            auto* NameText = WidgetTree->ConstructWidget<UTextBlock>();
            NameText->SetText(Name);
            auto Font = NameText->GetFont(); Font.Size = 16; NameText->SetFont(Font);
            Row->AddChildToHorizontalBox(NameText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

            auto* Slider = WidgetTree->ConstructWidget<USlider>();
            Slider->SetStepSize(.02f);
            Slider->SetValue(InitialValue);
            Row->AddChildToHorizontalBox(Slider)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

            auto* ValueText = WidgetTree->ConstructWidget<UTextBlock>();
            ValueText->SetJustification(ETextJustify::Right);
            Font.Size = 15; ValueText->SetFont(Font);
            Row->AddChildToHorizontalBox(ValueText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
            SettingLabels.Add(NameText);
            SettingValues.Add(ValueText);
            return Slider;
        };

        auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
        BrightnessSlider = AddSetting(NSLOCTEXT("Elitewake", "BrightnessLabel", "Brightness"),
            Normalize(PC ? PC->GetUserBrightness() : 0.f, MinBrightness, MaxBrightness));
        BrightnessSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnBrightnessChanged);
        MouseSensitivitySlider = AddSetting(NSLOCTEXT("Elitewake", "MouseSensitivityLabel", "Mouse look sensitivity"),
            Normalize(PC ? PC->GetMouseLookSensitivity() : 1.f, MinSensitivity, MaxSensitivity));
        MouseSensitivitySlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnMouseSensitivityChanged);
        ControllerSensitivitySlider = AddSetting(NSLOCTEXT("Elitewake", "ControllerSensitivityLabel", "Controller look sensitivity"),
            Normalize(PC ? PC->GetControllerLookSensitivity() : 1.f, MinSensitivity, MaxSensitivity));
        ControllerSensitivitySlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnControllerSensitivityChanged);
        VolumeSlider = AddSetting(NSLOCTEXT("Elitewake", "VolumeLabel", "Master volume"), PC ? PC->GetMasterVolume() : 1.f);
        VolumeSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnVolumeChanged);

        auto Button = [&](const FText& Value)
        {
            auto* Control = WidgetTree->ConstructWidget<UButton>();
            Control->SetBackgroundColor(Idle);
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
            Label->SetText(Value); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = 19; Font.LetterSpacing = 120; Label->SetFont(Font);
            Control->SetContent(Label);
            PausePage->AddChildToVerticalBox(Control)->SetPadding(FMargin(0, 5));
            return Control;
        };
        SaveButton = Button(NSLOCTEXT("Elitewake", "OptionsSave", "SAVE GAME"));
        SaveButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::SaveGame);
        SaveButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverSave);
        MenuButton = Button(NSLOCTEXT("Elitewake", "OptionsMainMenu", "MAIN MENU"));
        MenuButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::MainMenu);
        MenuButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverMenu);
        Status = Text(FText::GetEmpty(), 13, FLinearColor(.75f, .82f, .84f));
        Text(NSLOCTEXT("Elitewake", "OptionsHint", "Tab / RB / LB switch tabs · Up/Down select · Left/Right adjust · Enter choose"), 11, FLinearColor(.5f, .58f, .6f));

        if (!IsSaveShown())
        {
            SaveButton->SetVisibility(ESlateVisibility::Collapsed);
            Selected = 5;
            Status->SetText(NSLOCTEXT("Elitewake", "OptionsServerSaves", "Your host keeps multiplayer progress. Leaving for the main menu ends this session."));
        }
        Status->SetAutoWrapText(true);
        SetTab(0);
    }
    RefreshSettingLabels();
    return Super::RebuildWidget();
}

void UEWOptionsWidget::SetTab(int32 NewTab)
{
    Tab = FMath::Clamp(NewTab, 0, 1); TabCursor = Tab;
    Selected = Tab == 1 ? 0 : (IsSaveShown() ? 4 : 5);
    if (PausePage) PausePage->SetVisibility(Tab == 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (OptionsPage) OptionsPage->SetVisibility(Tab == 1 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    for (int32 Index = 0; Index < TabButtons.Num(); ++Index)
        TabButtons[Index]->SetBackgroundColor(Index == Tab ? FLinearColor(.5f, .52f, .55f) : FLinearColor(.055f, .065f, .075f));
}

void UEWOptionsWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    for (int32 Index = 0; Index < TabButtons.Num(); ++Index)
        TabButtons[Index]->SetBackgroundColor(Selected == -1 && Index == TabCursor ? FLinearColor(1.f, .85f, .35f) : Index == Tab ? FLinearColor(.5f, .52f, .55f) : FLinearColor(.055f, .065f, .075f));
    if (SaveButton) SaveButton->SetBackgroundColor(Tab == 0 && Selected == 4 ? Lit : Idle);
    if (MenuButton) MenuButton->SetBackgroundColor(Tab == 0 && Selected == 5 ? Lit : Idle);
    for (int32 Index = 0; Index < SettingLabels.Num(); ++Index)
        SettingLabels[Index]->SetColorAndOpacity(Tab == 1 && Selected == Index ? FLinearColor(.25f,.88f,1.f) : FLinearColor::White);
}

void UEWOptionsWidget::RefreshSettingLabels()
{
    if (SettingValues.Num() < 4) return;
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const float Brightness = PC ? PC->GetUserBrightness() : 0.f;
    const float Mouse = PC ? PC->GetMouseLookSensitivity() : 1.f;
    const float Controller = PC ? PC->GetControllerLookSensitivity() : 1.f;
    SettingValues[0]->SetText(FText::AsNumber(FMath::RoundToInt((Brightness - MinBrightness) / (MaxBrightness - MinBrightness) * 100.f)));
    SettingValues[1]->SetText(FText::AsNumber(FMath::RoundToInt(Mouse * 100.f)));
    SettingValues[2]->SetText(FText::AsNumber(FMath::RoundToInt(Controller * 100.f)));
    SettingValues[3]->SetText(FText::AsNumber(FMath::RoundToInt((PC ? PC->GetMasterVolume() : 1.f) * 100.f)));
}

void UEWOptionsWidget::OnBrightnessChanged(float Value)
{
    Selected = 0;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetUserBrightness(Denormalize(Value, MinBrightness, MaxBrightness));
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnMouseSensitivityChanged(float Value)
{
    Selected = 1;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetMouseLookSensitivity(Denormalize(Value, MinSensitivity, MaxSensitivity));
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnControllerSensitivityChanged(float Value)
{
    Selected = 2;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetControllerLookSensitivity(Denormalize(Value, MinSensitivity, MaxSensitivity));
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnVolumeChanged(float Value)
{
    Selected = 3;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetMasterVolume(Value);
    RefreshSettingLabels();
}

void UEWOptionsWidget::AdjustSelectedSetting(float Direction)
{
    USlider* Slider = Selected == 0 ? BrightnessSlider : Selected == 1 ? MouseSensitivitySlider : Selected == 2 ? ControllerSensitivitySlider : Selected == 3 ? VolumeSlider : nullptr;
    if (Slider) Slider->SetValue(FMath::Clamp(Slider->GetValue() + Direction * .02f, 0.f, 1.f));
}

FReply UEWOptionsWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
    {
        if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetOptionsMenuOpen(false);
        return FReply::Handled();
    }
    if (Key == EKeys::Tab || Key == EKeys::PageDown || Key == EKeys::PageUp || Key == EKeys::Gamepad_RightShoulder || Key == EKeys::Gamepad_LeftShoulder || Key == EKeys::Gamepad_LeftTrigger)
    {
        if (!Event.IsRepeat()) SetTab(1 - Tab);
        return FReply::Handled();
    }
    const bool bTabsLeft = Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left;
    const bool bTabsRight = Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right;
    if (Selected == -1)
    {
        // The tab bar holds the highlight: Left/Right move along it, A opens the tab, Down returns to the page.
        if (bTabsLeft || bTabsRight) TabCursor = FMath::Clamp(TabCursor + (bTabsRight ? 1 : -1), 0, 1);
        else if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom) { if (!Event.IsRepeat()) SetTab(TabCursor); }
        else if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down) Selected = Tab == 1 ? 0 : (IsSaveShown() ? 4 : 5);
        return FReply::Handled();
    }
    const bool bUp = Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool bDown = Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    if (bUp || bDown)
    {
        // The PAUSE tab holds SAVE GAME (4) and MAIN MENU (5); the OPTIONS tab the four sliders (0 to 3).
        const int32 First = Tab == 1 ? 0 : (IsSaveShown() ? 4 : 5);
        const int32 Last = Tab == 1 ? 3 : 5;
        if (bUp && Selected <= First) { Selected = -1; TabCursor = Tab; return FReply::Handled(); }
        Selected = FMath::Clamp(Selected + (bUp ? -1 : 1), First, Last);
        return FReply::Handled();
    }
    if (bTabsLeft || bTabsRight)
    {
        AdjustSelectedSetting(bTabsLeft ? -1.f : 1.f);
        return FReply::Handled();
    }
    if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        if (Selected == 4) SaveGame();
        else if (Selected == 5) MainMenu();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UEWOptionsWidget::SaveGame()
{
    Selected = 4;
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!PC || !IsSaveShown() || !Status) return;
    Status->SetText(PC->SaveSurvivorGame()
        ? FText::Format(NSLOCTEXT("Elitewake", "OptionsSaved", "Game saved {0}. Single Player resumes from here."), FText::AsTime(FDateTime::Now()))
        : NSLOCTEXT("Elitewake", "OptionsSaveFailed", "The game could not be saved."));
}

void UEWOptionsWidget::MainMenu()
{
    Selected = 5;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->ReturnToMainMenu();
}
