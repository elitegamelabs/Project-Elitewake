#include "EWDialogueWidget.h"
#include "EWCharacter.h"
#include "EWInventoryWidget.h"
#include "EWPlayerController.h"
#include "EWTownsfolk.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Ships/EWShip.h"

namespace
{
// Dark weathered timber with brass lettering: a waterfront signboard, not a menu.
const FLinearColor DialoguePanel(.055f, .04f, .028f, .94f);
const FLinearColor DialogueBrass(.93f, .74f, .38f);
const FLinearColor DialogueSpeech(.92f, .88f, .8f);
const FLinearColor DialogueFaded(.5f, .46f, .4f);

UTextBlock* MakeDialogueText(UWidgetTree* Tree, const FText& Value, int32 Size, const FLinearColor& Colour, bool bBold = false)
{
    auto* T = Tree->ConstructWidget<UTextBlock>();
    T->SetText(Value); T->SetAutoWrapText(true); T->SetColorAndOpacity(FSlateColor(Colour));
    auto Font = T->GetFont(); Font.Size = Size; if (bBold) Font.TypefaceFontName = FName("Bold");
    T->SetFont(Font);
    return T;
}
}

TSharedRef<SWidget> UEWDialogueWidget::RebuildWidget()
{
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
    // Takes keyboard focus, so its number keys, arrows and Leave reach it.
    SetIsFocusable(true);
    auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    WidgetTree->RootWidget = Canvas;
    auto* Frame = WidgetTree->ConstructWidget<UBorder>();
    Frame->SetBrushColor(DialoguePanel);
    Frame->SetPadding(FMargin(34, 24, 34, 24));
    auto* FrameSlot = Canvas->AddChildToCanvas(Frame);
    // Low and centred, clear of the crosshair, wide enough for a long line of goods.
    FrameSlot->SetAnchors(FAnchors(.5f, 1.f));
    FrameSlot->SetAlignment(FVector2D(.5f, 1.f));
    FrameSlot->SetPosition(FVector2D(0.f, -60.f));
    FrameSlot->SetAutoSize(true);
    auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
    Frame->SetContent(Column);
    NameText = MakeDialogueText(WidgetTree, FText::GetEmpty(), 22, DialogueBrass, true);
    NameText->SetAutoWrapText(false);
    Column->AddChildToVerticalBox(NameText)->SetPadding(FMargin(0, 0, 0, 6));
    auto* Rule = WidgetTree->ConstructWidget<UBorder>();
    Rule->SetBrushColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .4f));
    Rule->SetPadding(FMargin(380, 1));
    Column->AddChildToVerticalBox(Rule)->SetPadding(FMargin(0, 0, 0, 12));
    LineText = MakeDialogueText(WidgetTree, FText::GetEmpty(), 17, DialogueSpeech);
    LineText->SetWrapTextAt(760.f);
    Column->AddChildToVerticalBox(LineText)->SetPadding(FMargin(0, 0, 0, 16));
    OptionList = WidgetTree->ConstructWidget<UVerticalBox>();
    Column->AddChildToVerticalBox(OptionList);
    // The box for a choice that asks for text (a ship's name), shown in place of the choices.
    TextPanel = WidgetTree->ConstructWidget<UVerticalBox>();
    TextPanel->SetVisibility(ESlateVisibility::Collapsed);
    Column->AddChildToVerticalBox(TextPanel);
    TextPrompt = MakeDialogueText(WidgetTree, FText::GetEmpty(), 16, DialogueBrass);
    TextPanel->AddChildToVerticalBox(TextPrompt)->SetPadding(FMargin(0, 0, 0, 6));
    TextBox = WidgetTree->ConstructWidget<UEditableTextBox>();
    {
        FEditableTextBoxStyle Style = TextBox->WidgetStyle;
        Style.SetForegroundColor(FSlateColor(DialogueSpeech));
        Style.SetBackgroundColor(FSlateColor(FLinearColor(.12f, .09f, .06f, 1.f)));
        Style.TextStyle.Font.Size = 20;
        TextBox->WidgetStyle = Style;
    }
    TextBox->OnTextCommitted.AddDynamic(this, &UEWDialogueWidget::OnTextCommitted);
    TextPanel->AddChildToVerticalBox(TextBox)->SetPadding(FMargin(0, 0, 0, 10));
    auto* TextButtons = WidgetTree->ConstructWidget<UHorizontalBox>();
    TextPanel->AddChildToVerticalBox(TextButtons);
    const FText TextLabels[] = {NSLOCTEXT("Elitewake", "DialogueRegister", "Register (Enter / A)"),
        NSLOCTEXT("Elitewake", "DialogueSuggest", "Suggest a name (X)"), NSLOCTEXT("Elitewake", "DialogueCancel", "Cancel (Esc / B)")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(TextLabels); ++Index)
    {
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>();
        Button->Initialize(Index);
        Button->OnRecipePressed.AddDynamic(this, &UEWDialogueWidget::OnTextButton);
        FButtonStyle Flat = Button->GetStyle();
        Flat.Normal.TintColor = FSlateColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .1f));
        Flat.Hovered.TintColor = FSlateColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .22f));
        Flat.Pressed.TintColor = FSlateColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .35f));
        Button->SetStyle(Flat);
        Button->SetContent(MakeDialogueText(WidgetTree, TextLabels[Index], 15, DialogueSpeech));
        TextButtons->AddChildToHorizontalBox(Button)->SetPadding(FMargin(0, 0, 10, 0));
        if (Index == 1) SuggestButton = Button;
    }
    Column->AddChildToVerticalBox(MakeDialogueText(WidgetTree, NSLOCTEXT("Elitewake", "DialogueLeave", "Leave: Esc / E / B"), 12, DialogueFaded))->SetPadding(FMargin(0, 12, 0, 0));
    return Super::RebuildWidget();
}

void UEWDialogueWidget::SetSpeaker(AEWTownsfolk* NewSpeaker)
{
    Speaker = NewSpeaker;
    TakeWidget();
    Keys.Reset(); ShownLabels.Reset(); Cursor = 0;
    if (!NewSpeaker || !NameText) return;
    NameText->SetText(NewSpeaker->RoleTitle.IsEmpty() ? NewSpeaker->NpcName
        : FText::Format(NSLOCTEXT("Elitewake", "DialogueName", "{0}  -  {1}"), NewSpeaker->NpcName, NewSpeaker->RoleTitle));
    const auto* Survivor = Cast<AEWCharacter>(GetOwningPlayerPawn());
    LineText->SetText(NewSpeaker->GetDialogueGreeting(Survivor));
    RefreshOptions();
}

void UEWDialogueWidget::ShowReply(const FText& Reply)
{
    if (LineText && !Reply.IsEmpty()) LineText->SetText(Reply);
    RefreshOptions();
}

FText UEWDialogueWidget::GetShownLine() const
{
    return LineText ? LineText->GetText() : FText::GetEmpty();
}

void UEWDialogueWidget::RefreshOptions()
{
    AEWTownsfolk* Person = Speaker.Get();
    if (!Person || !OptionList) return;
    const TArray<FEWDialogueOption> Options = Person->GetDialogueOptionsFor(Cast<AEWCharacter>(GetOwningPlayerPawn()));
    TArray<FString> Labels;
    for (int32 Index = 0; Index < Options.Num(); ++Index)
        Labels.Add(FString::Printf(TEXT("%d.  %s"), Index + 1, *Options[Index].Label.ToString()));
    TArray<bool> NowEnabled;
    for (const FEWDialogueOption& Option : Options) NowEnabled.Add(Option.bEnabled);
    AsksText.Reset();
    for (const FEWDialogueOption& Option : Options) AsksText.Add(Option.bAsksForText);
    Prompts.Reset(); Suggests.Reset();
    for (const FEWDialogueOption& Option : Options) { Prompts.Add(Option.TextPrompt); Suggests.Add(Option.bSuggestsShipName); }
    if (Labels == ShownLabels && NowEnabled == Enabled) return;
    ShownLabels = Labels;
    Enabled = NowEnabled;
    Keys.Reset();
    OptionList->ClearChildren();
    Buttons.Reset();
    for (int32 Index = 0; Index < Options.Num(); ++Index)
    {
        Keys.Add(Options[Index].Key);
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>();
        Button->Initialize(Index);
        Button->OnRecipePressed.AddDynamic(this, &UEWDialogueWidget::OnOptionPressed);
        FButtonStyle Flat = Button->GetStyle();
        Flat.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
        Flat.Hovered.TintColor = FSlateColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .16f));
        Flat.Pressed.TintColor = FSlateColor(FLinearColor(DialogueBrass.R, DialogueBrass.G, DialogueBrass.B, .3f));
        Flat.Disabled.TintColor = Flat.Normal.TintColor;
        Button->SetStyle(Flat);
        Button->SetContent(MakeDialogueText(WidgetTree, FText::FromString(Labels[Index]), 16, Options[Index].bEnabled ? DialogueSpeech : DialogueFaded));
        Button->SetIsEnabled(Options[Index].bEnabled);
        OptionList->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 1));
        Buttons.Add(Button);
    }
    Cursor = FMath::Clamp(Cursor, 0, FMath::Max(0, Buttons.Num() - 1));
    for (int32 Index = 0; Index < Buttons.Num(); ++Index)
        Buttons[Index]->SetBackgroundColor(Index == Cursor ? FLinearColor(1.f, .85f, .5f, 1.f) : FLinearColor::White);
}

bool UEWDialogueWidget::Choose(int32 Index)
{
    if (!Keys.IsValidIndex(Index) || !Enabled.IsValidIndex(Index) || !Enabled[Index]) return false;
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!Controller || !Speaker.IsValid()) return false;
    if (AsksText.IsValidIndex(Index) && AsksText[Index])
    {
        // Show the box in place of the choices. Typing goes to it; a controller keeps the window's own focus (A, X, B).
        TextKey = Keys[Index];
        bTextSuggests = Suggests.IsValidIndex(Index) && Suggests[Index];
        if (TextPrompt) TextPrompt->SetText(Prompts.IsValidIndex(Index) && !Prompts[Index].IsEmpty() ? Prompts[Index]
            : FText::Format(NSLOCTEXT("Elitewake", "DialogueNameAsk", "Her name, 2 to {0} letters:"), FText::AsNumber(AEWShip::MaxNameLength)));
        if (SuggestButton) SuggestButton->SetVisibility(bTextSuggests ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (TextBox) TextBox->SetText(FText::GetEmpty());
        if (OptionList) OptionList->SetVisibility(ESlateVisibility::Collapsed);
        if (TextPanel) TextPanel->SetVisibility(ESlateVisibility::Visible);
        if (TextBox && !bChosenByPad) TextBox->SetKeyboardFocus();
        return true;
    }
    Controller->ServerChooseDialogue(Speaker.Get(), Keys[Index]);
    return true;
}

FString UEWDialogueWidget::GetEnteredText() const
{
    return TextBox ? TextBox->GetText().ToString() : FString();
}

void UEWDialogueWidget::SetEnteredText(const FString& Text)
{
    if (TextBox) TextBox->SetText(FText::FromString(Text.Left(160)));
}

void UEWDialogueWidget::SuggestText()
{
    if (!IsAskingForText() || !bTextSuggests) return;
    SetEnteredText(AEWShip::SuggestName(GetWorld(), ++SuggestSeed + int32(FPlatformTime::Cycles() & 0xffff)));
}

void UEWDialogueWidget::SubmitText()
{
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!IsAskingForText() || !Controller || !Speaker.IsValid()) return;
    const FName Key = TextKey;
    const FString Text = GetEnteredText();
    CancelText();
    Controller->ServerChooseDialogueText(Speaker.Get(), Key, Text);
}

void UEWDialogueWidget::CancelText()
{
    TextKey = NAME_None;
    if (TextPanel) TextPanel->SetVisibility(ESlateVisibility::Collapsed);
    if (OptionList) OptionList->SetVisibility(ESlateVisibility::Visible);
    SetKeyboardFocus();
}

void UEWDialogueWidget::OnTextButton(int32 Index)
{
    if (Index == 0) SubmitText();
    else if (Index == 1) SuggestText();
    else CancelText();
}

void UEWDialogueWidget::OnTextCommitted(const FText& Text, ETextCommit::Type How)
{
    if (!IsAskingForText()) return;
    if (How == ETextCommit::OnEnter) SubmitText();
    else if (How == ETextCommit::OnCleared) CancelText();
}

void UEWDialogueWidget::Close()
{
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->CloseDialogue();
}

void UEWDialogueWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    const auto* Survivor = Cast<AEWCharacter>(GetOwningPlayerPawn());
    if (!Speaker.IsValid() || !Survivor || Survivor->IsDead()
        || FVector::Dist(Survivor->GetActorLocation(), Speaker->GetActorLocation()) > AEWTownsfolk::TalkReach + 150.f)
    {
        Close();
        return;
    }
    if ((RefreshClock += Delta) >= .5f)
    {
        RefreshClock = 0.f;
        RefreshOptions();
    }
}

FReply UEWDialogueWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    bChosenByPad = Key.IsGamepadKey();
    if (IsAskingForText())
    {
        // The box's own keys: register, suggest, cancel. Everything else (typing) belongs to the box.
        if (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) SubmitText();
        else if (Key == EKeys::Gamepad_FaceButton_Left) SuggestText();
        else if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) CancelText();
        return FReply::Handled();
    }
    if (Key == EKeys::Escape || Key == EKeys::E || Key == EKeys::Tab || Key == EKeys::Gamepad_FaceButton_Right)
    {
        Close();
        return FReply::Handled();
    }
    static const FKey Numbers[] = {EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four, EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Numbers); ++Index)
        if (Key == Numbers[Index] && !Event.IsRepeat()) { Choose(Index); return FReply::Handled(); }
    const bool bUp = Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::W;
    const bool bDown = Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::S;
    if ((bUp || bDown) && !Buttons.IsEmpty())
    {
        Cursor = (Cursor + (bDown ? 1 : Buttons.Num() - 1)) % Buttons.Num();
        for (int32 Index = 0; Index < Buttons.Num(); ++Index)
            Buttons[Index]->SetBackgroundColor(Index == Cursor ? FLinearColor(1.f, .85f, .5f, 1.f) : FLinearColor::White);
        return FReply::Handled();
    }
    if ((Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat())
    {
        Choose(Cursor);
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}
