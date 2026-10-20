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
        Text(NSLOCTEXT("Elitewake", "OptionsTitle", "OPTIONS"), 34, FLinearColor(.93f, .86f, .7f));

        auto AddSetting = [&](const FText& Name, float InitialValue) -> USlider*
        {
            auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
            Body->AddChildToVerticalBox(Row)->SetPadding(FMargin(4, 4));
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

        auto Button = [&](const FText& Value)
        {
            auto* Control = WidgetTree->ConstructWidget<UButton>();
            Control->SetBackgroundColor(Idle);
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
            Label->SetText(Value); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = 19; Font.LetterSpacing = 120; Label->SetFont(Font);
            Control->SetContent(Label);
            Body->AddChildToVerticalBox(Control)->SetPadding(FMargin(0, 5));
            return Control;
        };
        SaveButton = Button(NSLOCTEXT("Elitewake", "OptionsSave", "SAVE GAME"));
        SaveButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::SaveGame);
        SaveButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverSave);
        MenuButton = Button(NSLOCTEXT("Elitewake", "OptionsMainMenu", "MAIN MENU"));
        MenuButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::MainMenu);
        MenuButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverMenu);
        Status = Text(FText::GetEmpty(), 13, FLinearColor(.75f, .82f, .84f));
        Text(NSLOCTEXT("Elitewake", "OptionsHint", "Use Up/Down to select · Left/Right to adjust · Enter to choose"), 11, FLinearColor(.5f, .58f, .6f));

        if (!IsSaveShown())
        {
            SaveButton->SetVisibility(ESlateVisibility::Collapsed);
            Selected = 0;
            Status->SetText(NSLOCTEXT("Elitewake", "OptionsServerSaves", "Your host keeps multiplayer progress. Leaving for the main menu ends this session."));
        }
        Status->SetAutoWrapText(true);
    }
    RefreshSettingLabels();
    return Super::RebuildWidget();
}

void UEWOptionsWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    if (SaveButton) SaveButton->SetBackgroundColor(Selected == 3 ? Lit : Idle);
    if (MenuButton) MenuButton->SetBackgroundColor(Selected == 4 ? Lit : Idle);
    for (int32 Index = 0; Index < SettingLabels.Num(); ++Index)
        SettingLabels[Index]->SetColorAndOpacity(Selected == Index ? FLinearColor(.25f,.88f,1.f) : FLinearColor::White);
}

void UEWOptionsWidget::RefreshSettingLabels()
{
    if (SettingValues.Num() < 3) return;
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const float Brightness = PC ? PC->GetUserBrightness() : 0.f;
    const float Mouse = PC ? PC->GetMouseLookSensitivity() : 1.f;
    const float Controller = PC ? PC->GetControllerLookSensitivity() : 1.f;
    SettingValues[0]->SetText(FText::AsNumber(FMath::RoundToInt((Brightness - MinBrightness) / (MaxBrightness - MinBrightness) * 100.f)));
    SettingValues[1]->SetText(FText::AsNumber(FMath::RoundToInt(Mouse * 100.f)));
    SettingValues[2]->SetText(FText::AsNumber(FMath::RoundToInt(Controller * 100.f)));
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

void UEWOptionsWidget::AdjustSelectedSetting(float Direction)
{
    USlider* Slider = Selected == 0 ? BrightnessSlider : Selected == 1 ? MouseSensitivitySlider : Selected == 2 ? ControllerSensitivitySlider : nullptr;
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
    const bool bUp = Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool bDown = Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    if (bUp || bDown)
    {
        const int32 MaxSelection = IsSaveShown() ? 4 : 4;
        int32 Next = FMath::Clamp(Selected + (bUp ? -1 : 1), 0, MaxSelection);
        if (!IsSaveShown() && Next == 3) Next = bUp ? 2 : 4;
        Selected = Next;
        return FReply::Handled();
    }
    if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right)
    {
        AdjustSelectedSetting((Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left) ? -1.f : 1.f);
        return FReply::Handled();
    }
    if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        if (Selected == 3) SaveGame();
        else if (Selected == 4) MainMenu();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UEWOptionsWidget::SaveGame()
{
    Selected = 3;
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!PC || !IsSaveShown() || !Status) return;
    Status->SetText(PC->SaveSurvivorGame()
        ? FText::Format(NSLOCTEXT("Elitewake", "OptionsSaved", "Game saved {0}. Single Player resumes from here."), FText::AsTime(FDateTime::Now()))
        : NSLOCTEXT("Elitewake", "OptionsSaveFailed", "The game could not be saved."));
}

void UEWOptionsWidget::MainMenu()
{
    Selected = 4;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->ReturnToMainMenu();
}
