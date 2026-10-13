#include "Title/EWCharacterCreatorWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

namespace
{
const FLinearColor CreatorInk(.95f, .91f, .82f);
const FLinearColor CreatorGold(1.f, .8f, .45f);
const FLinearColor CreatorPanel(.02f, .025f, .03f, .78f);
const FLinearColor CreatorChoice(.12f, .13f, .14f, .9f);
const FLinearColor CreatorChosen(.55f, .4f, .2f, 1.f);
}

UButton* UEWCharacterCreatorWidget::MakeButton(const FText& Label, int32 FontSize)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>();
    Button->SetBackgroundColor(CreatorChoice);
    if (!Label.IsEmpty())
    {
        UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>();
        Text->SetText(Label);
        FSlateFontInfo Font = Text->GetFont();
        Font.Size = FontSize;
        Font.LetterSpacing = 120;
        Text->SetFont(Font);
        Text->SetColorAndOpacity(CreatorInk);
        Text->SetJustification(ETextJustify::Center);
        Button->AddChild(Text);
        if (auto* ButtonSlot = Cast<UButtonSlot>(Button->GetContentSlot())) ButtonSlot->SetPadding(FMargin(18, 8));
    }
    return Button;
}

TSharedRef<SWidget> UEWCharacterCreatorWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Canvas;
        auto* Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetBrushColor(CreatorPanel);
        Panel->SetPadding(FMargin(40, 44));
        auto* PanelSlot = Canvas->AddChildToCanvas(Panel);
        PanelSlot->SetAnchors(FAnchors(0, 0, 0, 1));
        PanelSlot->SetOffsets(FMargin(0, 0, 470, 0));
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
        Panel->SetContent(Column);

        auto Text = [&](const FText& String, int32 Size, const FLinearColor& Colour, float Gap, int32 Spacing = 0)
        {
            UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>();
            Block->SetText(String);
            FSlateFontInfo Font = Block->GetFont();
            Font.Size = Size;
            Font.LetterSpacing = Spacing;
            Block->SetFont(Font);
            Block->SetColorAndOpacity(Colour);
            Block->SetAutoWrapText(true);
            Column->AddChildToVerticalBox(Block)->SetPadding(FMargin(0, Gap, 0, 0));
            return Block;
        };
        Text(NSLOCTEXT("Elitewake", "CreatorTitle", "MAKE YOUR SURVIVOR"), 26, CreatorInk, 0, 260);
        Text(NSLOCTEXT("Elitewake", "CreatorLead", "Who wakes on the shore? Choose a body, colouring and height."), 13, CreatorInk * FLinearColor(1, 1, 1, .7f), 10);

        // Bodies, from the roster.
        Text(NSLOCTEXT("Elitewake", "CreatorBody", "BODY"), 12, CreatorGold, 34, 200);
        auto* Bodies = WidgetTree->ConstructWidget<UHorizontalBox>();
        Column->AddChildToVerticalBox(Bodies)->SetPadding(FMargin(0, 10, 0, 0));
        for (int32 Index = 0; Roster && Index < Roster->Bodies.Num(); ++Index)
        {
            UButton* Button = MakeButton(Roster->Bodies[Index].DisplayName, 15);
            Button->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleBodyClicked);
            Bodies->AddChildToHorizontalBox(Button)->SetPadding(FMargin(0, 0, 10, 0));
            BodyButtons.Add(Button);
        }

        // Tones: swatches.
        Text(NSLOCTEXT("Elitewake", "CreatorTone", "COLOURING"), 12, CreatorGold, 30, 200);
        auto* Tones = WidgetTree->ConstructWidget<UHorizontalBox>();
        Column->AddChildToVerticalBox(Tones)->SetPadding(FMargin(0, 10, 0, 0));
        for (int32 Index = 0; Roster && Index < Roster->Tones.Num(); ++Index)
        {
            UButton* Button = MakeButton(FText::GetEmpty(), 12);
            Button->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleToneClicked);
            auto* Size = WidgetTree->ConstructWidget<USizeBox>();
            Size->SetWidthOverride(44);
            Size->SetHeightOverride(44);
            Size->AddChild(Button);
            Tones->AddChildToHorizontalBox(Size)->SetPadding(FMargin(0, 0, 8, 0));
            ToneButtons.Add(Button);
        }

        // Height.
        Text(NSLOCTEXT("Elitewake", "CreatorHeight", "HEIGHT"), 12, CreatorGold, 30, 200);
        auto* Height = WidgetTree->ConstructWidget<UHorizontalBox>();
        Column->AddChildToVerticalBox(Height)->SetPadding(FMargin(0, 10, 0, 0));
        UButton* Shorter = MakeButton(FText::FromString(TEXT("-")), 16);
        Shorter->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleShorter);
        Height->AddChildToHorizontalBox(Shorter);
        HeightText = WidgetTree->ConstructWidget<UTextBlock>();
        HeightText->SetColorAndOpacity(CreatorInk);
        HeightText->SetMinDesiredWidth(110);
        HeightText->SetJustification(ETextJustify::Center);
        auto* HeightSlot = Height->AddChildToHorizontalBox(HeightText);
        HeightSlot->SetVerticalAlignment(VAlign_Center);
        UButton* Taller = MakeButton(FText::FromString(TEXT("+")), 16);
        Taller->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleTaller);
        Height->AddChildToHorizontalBox(Taller);

        auto* Fill = WidgetTree->ConstructWidget<USpacer>();
        Column->AddChildToVerticalBox(Fill)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        UButton* Sail = MakeButton(NSLOCTEXT("Elitewake", "CreatorSetSail", "SET SAIL"), 20);
        Sail->SetBackgroundColor(CreatorChosen);
        Sail->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleSetSail);
        Column->AddChildToVerticalBox(Sail)->SetPadding(FMargin(0, 0, 0, 12));
        UButton* Back = MakeButton(NSLOCTEXT("Elitewake", "CreatorBack", "BACK"), 13);
        Back->OnClicked.AddDynamic(this, &UEWCharacterCreatorWidget::HandleBack);
        Column->AddChildToVerticalBox(Back);

        auto* Hint = WidgetTree->ConstructWidget<UTextBlock>();
        Hint->SetText(NSLOCTEXT("Elitewake", "CreatorHint", "Drag across your survivor to turn them"));
        Hint->SetColorAndOpacity(CreatorInk * FLinearColor(1, 1, 1, .55f));
        auto* HintSlot = Canvas->AddChildToCanvas(Hint);
        HintSlot->SetAnchors(FAnchors(1, 1));
        HintSlot->SetAlignment(FVector2D(1, 1));
        HintSlot->SetAutoSize(true);
        HintSlot->SetPosition(FVector2D(-36, -30));
    }
    return Super::RebuildWidget();
}

void UEWCharacterCreatorWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetIsFocusable(true);
    SetKeyboardFocus();
    Appearance = Appearance.Clamped(Roster);
    Refresh();
}

void UEWCharacterCreatorWidget::Refresh()
{
    for (int32 Index = 0; Index < BodyButtons.Num(); ++Index)
        BodyButtons[Index]->SetBackgroundColor(Index == Appearance.Body ? CreatorChosen : CreatorChoice);
    for (int32 Index = 0; Index < ToneButtons.Num(); ++Index)
    {
        // A chosen swatch is drawn brighter than the rest.
        const FLinearColor Tone = Roster->Tones[Index];
        ToneButtons[Index]->SetBackgroundColor(Index == Appearance.Tone ? Tone * 1.6f : Tone * .8f);
        ToneButtons[Index]->SetRenderScale(FVector2D(Index == Appearance.Tone ? 1.15f : 1.f));
    }
    if (HeightText)
        HeightText->SetText(FText::Format(NSLOCTEXT("Elitewake", "CreatorHeightValue", "{0}%"), FText::AsNumber(FMath::RoundToInt(Appearance.Height * 100.f))));
    OnChanged.ExecuteIfBound();
}

void UEWCharacterCreatorWidget::SelectBody(int32 Index)
{
    if (!BodyButtons.IsValidIndex(Index)) return;
    Appearance.Body = static_cast<uint8>(Index);
    Refresh();
}

void UEWCharacterCreatorWidget::SelectTone(int32 Index)
{
    if (!ToneButtons.IsValidIndex(Index)) return;
    Appearance.Tone = static_cast<uint8>(Index);
    Refresh();
}

void UEWCharacterCreatorWidget::NudgeHeight(int32 Direction)
{
    Appearance.Height = FMath::Clamp(Appearance.Height + FMath::Sign(Direction) * .02f, FEWAppearance::MinHeight, FEWAppearance::MaxHeight);
    Refresh();
}

void UEWCharacterCreatorWidget::SetSail() { OnSetSail.ExecuteIfBound(); }
void UEWCharacterCreatorWidget::GoBack() { OnBack.ExecuteIfBound(); }

void UEWCharacterCreatorWidget::HandleBodyClicked()
{
    for (int32 Index = 0; Index < BodyButtons.Num(); ++Index) if (BodyButtons[Index]->IsHovered()) SelectBody(Index);
}

void UEWCharacterCreatorWidget::HandleToneClicked()
{
    for (int32 Index = 0; Index < ToneButtons.Num(); ++Index) if (ToneButtons[Index]->IsHovered()) SelectTone(Index);
}

void UEWCharacterCreatorWidget::HandleShorter() { NudgeHeight(-1); }
void UEWCharacterCreatorWidget::HandleTaller() { NudgeHeight(1); }
void UEWCharacterCreatorWidget::HandleSetSail() { SetSail(); }
void UEWCharacterCreatorWidget::HandleBack() { GoBack(); }

FReply UEWCharacterCreatorWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    bDragging = Event.GetEffectingButton() == EKeys::LeftMouseButton;
    return bDragging ? FReply::Handled().CaptureMouse(TakeWidget()) : FReply::Unhandled();
}

FReply UEWCharacterCreatorWidget::NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event)
{
    bDragging = false;
    return FReply::Handled().ReleaseMouseCapture();
}

FReply UEWCharacterCreatorWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bDragging) OnTurn.ExecuteIfBound(-Event.GetCursorDelta().X * .5f);
    return FReply::Handled();
}

FReply UEWCharacterCreatorWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Enter || Key == EKeys::Gamepad_Special_Right) { SetSail(); return FReply::Handled(); }
    if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) { GoBack(); return FReply::Handled(); }
    if (Key == EKeys::A || Key == EKeys::Left || Key == EKeys::Gamepad_LeftShoulder) { OnTurn.ExecuteIfBound(-15.f); return FReply::Handled(); }
    if (Key == EKeys::D || Key == EKeys::Right || Key == EKeys::Gamepad_RightShoulder) { OnTurn.ExecuteIfBound(15.f); return FReply::Handled(); }
    return FReply::Unhandled();
}
