#include "EWOptionsWidget.h"

#include "EWPlayerController.h"
#include "EWGameInstance.h"
#include "EWVolumeDial.h"
#include "EWGraphicsSettings.h"
#include "EWControllerIcons.h"
#include "EWControlsList.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
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
    constexpr int32 SettingCount = 15;
    constexpr float IconsStep = .5f;     // Automatic, Xbox, PlayStation
    constexpr float QualityStep = 1.f / (FEWGraphicsSettings::Levels - 1);

    float Normalize(float Value, float Min, float Max) { return (Value - Min) / (Max - Min); }
    float Denormalize(float Value, float Min, float Max) { return Min + FMath::Clamp(Value, 0.f, 1.f) * (Max - Min); }
}

bool UEWOptionsWidget::IsSaveShown() const
{
    // Multiplayer has no manual save: the server keeps its players' progress (MULTIPLAYER_RULES).
    return GetWorld() && GetWorld()->GetNetMode() == NM_Standalone;
}

float UEWOptionsWidget::GetDialValue() const { return VolumeDial ? VolumeDial->GetValue() : -1.f; }

FText UEWOptionsWidget::GetStatus() const { return Status ? Status->GetText() : FText::GetEmpty(); }

TArray<int32> UEWOptionsWidget::ButtonItems() const
{
    TArray<int32> Items = {ItemResume};
    if (IsSaveShown()) Items.Add(ItemSave);
    Items.Append({ItemOptions, ItemMainMenu});
    return Items;
}

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
        PanelWidth = Width;
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
        Title = Text(NSLOCTEXT("Elitewake", "OptionsTitle", "PAUSED"), 34, FLinearColor(.93f, .86f, .7f));
        PausePage = WidgetTree->ConstructWidget<UVerticalBox>();
        Body->AddChildToVerticalBox(PausePage);
        OptionsPage = WidgetTree->ConstructWidget<UVerticalBox>();
        Body->AddChildToVerticalBox(OptionsPage);
        ControlsPage = WidgetTree->ConstructWidget<UVerticalBox>();
        Body->AddChildToVerticalBox(ControlsPage);

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
        auto Button = [&](UVerticalBox* Page, const FText& Value)
        {
            auto* Control = WidgetTree->ConstructWidget<UButton>();
            Control->SetBackgroundColor(Idle);
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
            Label->SetText(Value); Label->SetJustification(ETextJustify::Center);
            auto Font = Label->GetFont(); Font.Size = 19; Font.LetterSpacing = 120; Label->SetFont(Font);
            Control->SetContent(Label);
            Page->AddChildToVerticalBox(Control)->SetPadding(FMargin(0, 5));
            return Control;
        };

        // The buttons page.
        ResumeButton = Button(PausePage, NSLOCTEXT("Elitewake", "OptionsResume", "RESUME GAME"));
        ResumeButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::Resume);
        ResumeButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverResume);
        SaveButton = Button(PausePage, NSLOCTEXT("Elitewake", "OptionsSave", "SAVE GAME"));
        SaveButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::SaveGame);
        SaveButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverSave);
        OptionsButton = Button(PausePage, NSLOCTEXT("Elitewake", "OptionsOptions", "OPTIONS"));
        OptionsButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::OpenOptions);
        OptionsButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverOptions);
        MenuButton = Button(PausePage, NSLOCTEXT("Elitewake", "OptionsMainMenu", "MAIN MENU"));
        MenuButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::MainMenu);
        MenuButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverMenu);

        // The settings page.
        auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
        BrightnessSlider = AddSetting(NSLOCTEXT("Elitewake", "BrightnessLabel", "Brightness"),
            Normalize(PC ? PC->GetUserBrightness() : 0.f, MinBrightness, MaxBrightness));
        BrightnessSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnBrightnessChanged);
        // Look speeds (owner, October 30): left-right and up-down apart, for the mouse and for the controller.
        const FText LookNames[4] = {NSLOCTEXT("Elitewake", "MouseHorizontalLabel", "Mouse horizontal sensitivity"),
            NSLOCTEXT("Elitewake", "MouseVerticalLabel", "Mouse vertical sensitivity"),
            NSLOCTEXT("Elitewake", "ControllerHorizontalLabel", "Controller horizontal sensitivity"),
            NSLOCTEXT("Elitewake", "ControllerVerticalLabel", "Controller vertical sensitivity")};
        for (int32 Which = 0; Which < 4; ++Which)
            LookSliders.Add(AddSetting(LookNames[Which], Normalize(PC ? PC->GetLookSensitivity(Which) : 1.f, MinSensitivity, MaxSensitivity)));
        LookSliders[0]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnMouseHorizontalChanged);
        LookSliders[1]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnMouseVerticalChanged);
        LookSliders[2]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnControllerHorizontalChanged);
        LookSliders[3]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnControllerVerticalChanged);
        VolumeSlider = AddSetting(NSLOCTEXT("Elitewake", "VolumeLabel", "Master volume"), PC ? PC->GetMasterVolume() : 1.f);
        VolumeSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnVolumeChanged);
        // A dial beside the volume (owner, October 30), turning with the slider.
        VolumeDial = CreateWidget<UEWVolumeDial>(GetOwningPlayer());
        if (VolumeDial)
        {
            VolumeDial->SetValue(PC ? PC->GetMasterVolume() : 1.f);
            VolumeDial->OnTurned = [this](float Turned) { if (VolumeSlider) { VolumeSlider->SetValue(Turned); OnVolumeChanged(Turned); } };
            auto* DialSize = WidgetTree->ConstructWidget<USizeBox>();
            DialSize->SetWidthOverride(64); DialSize->SetHeightOverride(64); DialSize->SetContent(VolumeDial);
            if (auto* Row = Cast<UHorizontalBox>(VolumeSlider->GetParent()))
                Row->AddChildToHorizontalBox(DialSize)->SetPadding(FMargin(10, 0, 0, 0));
        }
        // Sound effects and ambience, each under the master volume (owner, November 7).
        EffectsSlider = AddSetting(NSLOCTEXT("Elitewake", "EffectsVolumeLabel", "Sound effects volume"), UEWGameInstance::GetSoundEffectsVolume());
        EffectsSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnEffectsVolumeChanged);
        AmbienceSlider = AddSetting(NSLOCTEXT("Elitewake", "AmbienceVolumeLabel", "Ambience volume"), UEWGameInstance::GetAmbienceVolume());
        AmbienceSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnAmbienceVolumeChanged);
        // Graphics (owner, November 1; CLAUDE.md 9.6): the overall quality, then each group, Low to Epic.
        QualitySlider = AddSetting(NSLOCTEXT("Elitewake", "GraphicsQualityLabel", "Graphics quality"), 0.f);
        QualitySlider->SetStepSize(QualityStep);
        QualitySlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnQualityChanged);
        for (int32 Group = 0; Group < FEWGraphicsSettings::GroupCount; ++Group)
        {
            USlider* Slider = AddSetting(FEWGraphicsSettings::GroupName(static_cast<FEWGraphicsSettings::EGroup>(Group)), 0.f);
            Slider->SetStepSize(QualityStep);
            GraphicsSliders.Add(Slider);
        }
        GraphicsSliders[0]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnTexturesChanged);
        GraphicsSliders[1]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnShadowsChanged);
        GraphicsSliders[2]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnFoliageChanged);
        GraphicsSliders[3]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnReflectionsChanged);
        GraphicsSliders[4]->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnEffectsChanged);
        SyncGraphicsSliders();
        // Button icons (owner, November 1): follow the connected controller, or always Xbox or PlayStation.
        ButtonIconsSlider = AddSetting(NSLOCTEXT("Elitewake", "ButtonIconsLabel", "Button icons"),
            (PC ? int32(PC->GetButtonIconsChoice()) : 0) * IconsStep);
        ButtonIconsSlider->SetStepSize(IconsStep);
        ButtonIconsSlider->OnValueChanged.AddDynamic(this, &UEWOptionsWidget::OnButtonIconsChanged);
        // Controls (owner, November 7): every control, for the keyboard or the controller in use.
        ControlsButton = Button(OptionsPage, NSLOCTEXT("Elitewake", "OptionsControls", "CONTROLS"));
        ControlsButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::OpenControls);
        ControlsButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverControls);
        {
            ControlsHeading = WidgetTree->ConstructWidget<UTextBlock>();
            auto HeadFont = ControlsHeading->GetFont(); HeadFont.Size = 15; HeadFont.LetterSpacing = 150;
            ControlsHeading->SetFont(HeadFont);
            ControlsHeading->SetColorAndOpacity(FLinearColor(.93f, .86f, .7f));
            ControlsHeading->SetJustification(ETextJustify::Center);
            ControlsPage->AddChildToVerticalBox(ControlsHeading)->SetPadding(FMargin(0, 0, 0, 8));
            auto* ListHeight = WidgetTree->ConstructWidget<USizeBox>();
            ListHeight->SetHeightOverride(560);
            ControlsScroll = WidgetTree->ConstructWidget<UScrollBox>();
            ListHeight->SetContent(ControlsScroll);
            ControlsPage->AddChildToVerticalBox(ListHeight);
            for (int32 Index = 0; Index < EWControls::Count; ++Index)
            {
                const EWControls::FControl& Control = EWControls::List[Index];
                if (Control.Section)
                {
                    auto* Section = WidgetTree->ConstructWidget<UTextBlock>();
                    Section->SetText(FText::FromString(Control.Section));
                    auto SectionFont = Section->GetFont(); SectionFont.Size = 13; SectionFont.LetterSpacing = 250;
                    Section->SetFont(SectionFont);
                    Section->SetColorAndOpacity(FLinearColor(.25f, .88f, 1.f));
                    ControlsScroll->AddChild(Section);
                    if (auto* SectionSlot = Cast<UScrollBoxSlot>(Section->Slot)) SectionSlot->SetPadding(FMargin(4, Index == 0 ? 0 : 14, 4, 4));
                }
                auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
                auto* ActionText = WidgetTree->ConstructWidget<UTextBlock>();
                ActionText->SetText(FText::FromString(Control.Action));
                auto RowFont = ActionText->GetFont(); RowFont.Size = 14; ActionText->SetFont(RowFont);
                ActionText->SetAutoWrapText(true);
                Row->AddChildToHorizontalBox(ActionText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
                auto* Binding = WidgetTree->ConstructWidget<UTextBlock>();
                Binding->SetFont(RowFont);
                Binding->SetColorAndOpacity(FLinearColor(.93f, .86f, .7f));
                Binding->SetJustification(ETextJustify::Right);
                Binding->SetAutoWrapText(true);
                Row->AddChildToHorizontalBox(Binding)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
                ControlsScroll->AddChild(Row);
                if (auto* RowSlot = Cast<UScrollBoxSlot>(Row->Slot)) RowSlot->SetPadding(FMargin(8, 3));
                ControlTexts.Add(Binding);
            }
            ControlsBackButton = Button(ControlsPage, NSLOCTEXT("Elitewake", "OptionsControlsBack", "BACK"));
            ControlsBackButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::CloseControls);
        }
        BackButton = Button(OptionsPage, NSLOCTEXT("Elitewake", "OptionsBack", "BACK"));
        BackButton->OnClicked.AddDynamic(this, &UEWOptionsWidget::BackToButtons);
        BackButton->OnHovered.AddDynamic(this, &UEWOptionsWidget::HoverBack);

        Status = Text(FText::GetEmpty(), 13, FLinearColor(.75f, .82f, .84f));
        Hint = Text(FText::GetEmpty(), 11, FLinearColor(.5f, .58f, .6f));
        if (!IsSaveShown())
        {
            SaveButton->SetVisibility(ESlateVisibility::Collapsed);
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
    Tab = FMath::Clamp(NewTab, 0, 2);
    Selected = Tab == 1 ? 0 : ItemResume;
    if (PausePage) PausePage->SetVisibility(Tab == 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (OptionsPage) OptionsPage->SetVisibility(Tab == 1 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (ControlsPage) ControlsPage->SetVisibility(Tab == 2 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (PanelWidth) PanelWidth->SetWidthOverride(Tab == 2 ? 820.f : 560.f);
    if (Title) Title->SetText(Tab == 2 ? NSLOCTEXT("Elitewake", "ControlsPageTitle", "CONTROLS")
        : Tab == 1 ? NSLOCTEXT("Elitewake", "OptionsPageTitle", "OPTIONS") : NSLOCTEXT("Elitewake", "OptionsTitle", "PAUSED"));
    if (Hint) Hint->SetText(Tab == 2
        ? NSLOCTEXT("Elitewake", "ControlsHint", "Up/Down or the wheel to scroll · Escape or B back")
        : Tab == 1 ? NSLOCTEXT("Elitewake", "OptionsSettingsHint", "Up/Down select · Left/Right adjust · Escape or B back")
        : NSLOCTEXT("Elitewake", "OptionsHint", "Up/Down select · Enter choose · Escape resume"));
    if (Tab == 2) { RefreshControls(true); if (ControlsScroll) ControlsScroll->ScrollToStart(); }
}

void UEWOptionsWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    const auto Light = [this](UButton* Button, int32 Item, int32 OnTab) { if (Button) Button->SetBackgroundColor(Tab == OnTab && Selected == Item ? Lit : Idle); };
    Light(ResumeButton, ItemResume, 0);
    Light(SaveButton, ItemSave, 0);
    Light(OptionsButton, ItemOptions, 0);
    Light(MenuButton, ItemMainMenu, 0);
    Light(BackButton, SettingBack, 1);
    Light(ControlsButton, SettingControls, 1);
    if (Tab == 2) RefreshControls(false);
    for (int32 Index = 0; Index < SettingLabels.Num(); ++Index)
        SettingLabels[Index]->SetColorAndOpacity(Tab == 1 && Selected == Index ? FLinearColor(.25f,.88f,1.f) : FLinearColor::White);
}

void UEWOptionsWidget::RefreshSettingLabels()
{
    if (SettingValues.Num() < SettingCount) return;
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const float Brightness = PC ? PC->GetUserBrightness() : 0.f;
    SettingValues[0]->SetText(FText::AsNumber(FMath::RoundToInt((Brightness - MinBrightness) / (MaxBrightness - MinBrightness) * 100.f)));
    for (int32 Which = 0; Which < 4; ++Which)
        SettingValues[1 + Which]->SetText(FText::AsNumber(FMath::RoundToInt((PC ? PC->GetLookSensitivity(Which) : 1.f) * 100.f)));
    SettingValues[5]->SetText(FText::AsNumber(FMath::RoundToInt((PC ? PC->GetMasterVolume() : 1.f) * 100.f)));
    SettingValues[6]->SetText(FText::AsNumber(FMath::RoundToInt(UEWGameInstance::GetSoundEffectsVolume() * 100.f)));
    SettingValues[7]->SetText(FText::AsNumber(FMath::RoundToInt(UEWGameInstance::GetAmbienceVolume() * 100.f)));
    SettingValues[SettingGraphics]->SetText(FEWGraphicsSettings::LevelName(FEWGraphicsSettings::GetOverall()));
    for (int32 Group = 0; Group < FEWGraphicsSettings::GroupCount; ++Group)
        SettingValues[SettingGraphics + 1 + Group]->SetText(FEWGraphicsSettings::LevelName(FEWGraphicsSettings::Get(static_cast<FEWGraphicsSettings::EGroup>(Group))));
    if (VolumeDial) VolumeDial->SetValue(PC ? PC->GetMasterVolume() : 1.f);
    const EEWButtonIconsChoice Icons = PC ? PC->GetButtonIconsChoice() : EEWButtonIconsChoice::Automatic;
    const EEWGamepadFamily Connected = FEWControllerIcons::DetectConnected();
    SettingValues[SettingButtonIcons]->SetText(Icons == EEWButtonIconsChoice::Xbox ? NSLOCTEXT("Elitewake", "IconsXbox", "Xbox")
        : Icons == EEWButtonIconsChoice::PlayStation ? NSLOCTEXT("Elitewake", "IconsPlayStation", "PlayStation")
        : Connected == EEWGamepadFamily::Xbox ? NSLOCTEXT("Elitewake", "IconsAutoXbox", "Automatic (Xbox)")
        : Connected == EEWGamepadFamily::PlayStation ? NSLOCTEXT("Elitewake", "IconsAutoPlayStation", "Automatic (PlayStation)")
        : NSLOCTEXT("Elitewake", "IconsAuto", "Automatic"));
}

void UEWOptionsWidget::OnBrightnessChanged(float Value)
{
    Selected = 0;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetUserBrightness(Denormalize(Value, MinBrightness, MaxBrightness));
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnLookChanged(int32 Which, float Value)
{
    Selected = 1 + Which;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetLookSensitivity(Which, Denormalize(Value, MinSensitivity, MaxSensitivity));
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnVolumeChanged(float Value)
{
    Selected = 5;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetMasterVolume(Value);
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnEffectsVolumeChanged(float Value)
{
    Selected = 6;
    UEWGameInstance::SetSoundEffectsVolume(Value);
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnAmbienceVolumeChanged(float Value)
{
    Selected = 7;
    UEWGameInstance::SetAmbienceVolume(Value);
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnQualityChanged(float Value)
{
    if (bSyncingGraphics) return;
    Selected = SettingGraphics;
    FEWGraphicsSettings::SetOverall(FMath::RoundToInt(Value / QualityStep));
    SyncGraphicsSliders();
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnGraphicsChanged(int32 Group, float Value)
{
    if (bSyncingGraphics) return;
    Selected = SettingGraphics + 1 + Group;
    FEWGraphicsSettings::Set(static_cast<FEWGraphicsSettings::EGroup>(Group), FMath::RoundToInt(Value / QualityStep));
    SyncGraphicsSliders();
    RefreshSettingLabels();
}

void UEWOptionsWidget::OnButtonIconsChanged(float Value)
{
    Selected = SettingButtonIcons;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer()))
        PC->SetButtonIconsChoice(static_cast<EEWButtonIconsChoice>(FMath::Clamp(FMath::RoundToInt(Value / IconsStep), 0, 2)));
    RefreshSettingLabels();
}

void UEWOptionsWidget::SyncGraphicsSliders()
{
    TGuardValue<bool> Syncing(bSyncingGraphics, true);
    const int32 Overall = FEWGraphicsSettings::GetOverall();
    if (QualitySlider && Overall != INDEX_NONE) QualitySlider->SetValue(Overall * QualityStep);
    for (int32 Group = 0; Group < GraphicsSliders.Num(); ++Group)
        if (GraphicsSliders[Group]) GraphicsSliders[Group]->SetValue(FEWGraphicsSettings::Get(static_cast<FEWGraphicsSettings::EGroup>(Group)) * QualityStep);
}

void UEWOptionsWidget::AdjustSelectedSetting(float Direction)
{
    USlider* Sliders[SettingCount] = {BrightnessSlider, LookSliders[0], LookSliders[1], LookSliders[2], LookSliders[3], VolumeSlider, EffectsSlider, AmbienceSlider, QualitySlider,
        GraphicsSliders[0], GraphicsSliders[1], GraphicsSliders[2], GraphicsSliders[3], GraphicsSliders[4], ButtonIconsSlider};
    if (Selected < 0 || Selected >= SettingCount || !Sliders[Selected]) return;
    // The graphics settings move a whole level at a time (and the slider's change handler applies it).
    const float Step = Selected == SettingButtonIcons ? IconsStep : Selected >= SettingGraphics ? QualityStep : .02f;
    const float Value = FMath::Clamp(Sliders[Selected]->GetValue() + Direction * Step, 0.f, 1.f);
    Sliders[Selected]->SetValue(Value);
    if (Selected == SettingGraphics) OnQualityChanged(Value);
    else if (Selected == SettingButtonIcons) OnButtonIconsChanged(Value);
    else if (Selected > SettingGraphics) OnGraphicsChanged(Selected - SettingGraphics - 1, Value);
}

FReply UEWOptionsWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    // The menu notices the device in use too (gameplay input does not reach the controller while a menu is up), so the
    // Controls page and prompts follow a controller picked up mid-menu.
    if (auto* Owner = Cast<AEWPlayerController>(GetOwningPlayer())) Owner->RecordInputDevice(Key);
    if (Tab == 2) RefreshControls(false);
    if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
    {
        // From the settings, back to the buttons; from the buttons, back to the game.
        if (Tab == 2) CloseControls();
        else if (Tab == 1) BackToButtons();
        else if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetOptionsMenuOpen(false);
        return FReply::Handled();
    }
    const bool bUp = Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool bDown = Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    const bool bLeft = Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left;
    const bool bRight = Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right;
    const bool bAccept = Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom;
    if (Tab == 2)
    {
        if ((bUp || bDown) && ControlsScroll) ControlsScroll->SetScrollOffset(FMath::Max(0.f, ControlsScroll->GetScrollOffset() + (bUp ? -60.f : 60.f)));
        else if (bAccept && !Event.IsRepeat()) CloseControls();
        return FReply::Handled();
    }
    if (bUp || bDown)
    {
        if (Tab == 1) Selected = FMath::Clamp(Selected + (bUp ? -1 : 1), 0, SettingBack);
        else
        {
            const TArray<int32> Items = ButtonItems();
            const int32 Place = FMath::Max(0, Items.IndexOfByKey(Selected));
            Selected = Items[FMath::Clamp(Place + (bUp ? -1 : 1), 0, Items.Num() - 1)];
        }
        return FReply::Handled();
    }
    if ((bLeft || bRight) && Tab == 1)
    {
        AdjustSelectedSetting(bLeft ? -1.f : 1.f);
        return FReply::Handled();
    }
    if (bAccept)
    {
        if (Event.IsRepeat()) return FReply::Handled();
        if (Tab == 1) { if (Selected == SettingBack) BackToButtons(); else if (Selected == SettingControls) OpenControls(); }
        else if (Selected == ItemResume) Resume();
        else if (Selected == ItemSave) SaveGame();
        else if (Selected == ItemOptions) OpenOptions();
        else if (Selected == ItemMainMenu) MainMenu();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UEWOptionsWidget::Resume()
{
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetOptionsMenuOpen(false);
}

void UEWOptionsWidget::SaveGame()
{
    Selected = ItemSave;
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!PC || !IsSaveShown() || !Status) return;
    Status->SetText(PC->SaveSurvivorGame()
        ? FText::Format(NSLOCTEXT("Elitewake", "OptionsSaved", "Game saved {0}. Single Player resumes from here."), FText::AsTime(FDateTime::Now()))
        : NSLOCTEXT("Elitewake", "OptionsSaveFailed", "The game could not be saved."));
}

void UEWOptionsWidget::MainMenu()
{
    Selected = ItemMainMenu;
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->ReturnToMainMenu();
}

FString UEWOptionsWidget::GetControlText(int32 Index) const
{
    return ControlTexts.IsValidIndex(Index) && ControlTexts[Index] ? ControlTexts[Index]->GetText().ToString() : FString();
}

void UEWOptionsWidget::RefreshControls(bool bForce)
{
    // The input last used decides (as the prompts do); a controller is named for its make (Xbox, PlayStation).
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const bool bPad = PC && PC->UsesControllerPrompts();
    const EEWGamepadFamily Family = PC ? FEWControllerIcons::Resolve(PC->GetButtonIconsChoice(), FEWControllerIcons::DetectConnected()) : EEWGamepadFamily::Unknown;
    if (!bForce && bPad == bControlsForPad && Family == ControlsFamily) return;
    bControlsForPad = bPad;
    ControlsFamily = Family;
    if (ControlsHeading)
        ControlsHeading->SetText(bPad ? FText::Format(NSLOCTEXT("Elitewake", "ControlsForPad", "CONTROLLER ({0})"),
            FText::FromString(FEWControllerIcons::FamilyName(Family))) : NSLOCTEXT("Elitewake", "ControlsForKeys", "KEYBOARD AND MOUSE"));
    for (int32 Index = 0; Index < ControlTexts.Num() && Index < EWControls::Count; ++Index)
        ControlTexts[Index]->SetText(FText::FromString(bPad ? FEWControllerIcons::Expand(FString(EWControls::List[Index].Controller), Family, false)
            : FString(EWControls::List[Index].Keyboard)));
}

FReply UEWOptionsWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (!Event.GetCursorDelta().IsNearlyZero())
        if (auto* Owner = Cast<AEWPlayerController>(GetOwningPlayer())) Owner->RecordInputDevice(EKeys::MouseX);
    return Super::NativeOnMouseMove(Geometry, Event);
}
