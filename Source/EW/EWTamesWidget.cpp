// Copyright Elite Game Labs. All Rights Reserved.

#include "EWTamesWidget.h"
#include "EWInventoryWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

namespace
{
    const FLinearColor Gold(1.f, .85f, .35f, 1.f);
    const FLinearColor Panel(.03f, .036f, .042f, .78f);

    UTextBlock* Label(UWidgetTree* Tree, UVerticalBox* Into, const FString& Value, int32 Size, const FLinearColor& Colour, float Below)
    {
        auto* Text = Tree->ConstructWidget<UTextBlock>(); Text->SetText(FText::FromString(Value)); Text->SetAutoWrapText(true);
        Text->SetColorAndOpacity(FSlateColor(Colour)); auto Font = Text->GetFont(); Font.Size = Size; Text->SetFont(Font);
        if (Into) Into->AddChildToVerticalBox(Text)->SetPadding(FMargin(0, 0, 0, Below));
        return Text;
    }
}

TSharedRef<SWidget> UEWTamesWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        // Sample creatures of the species that exist in the world; replaced by the player's real tames once taming is built.
        auto Make = [](const TCHAR* Name, const TCHAR* Species, int32 Level, int32 Xp, int32 XpNext, const TCHAR* Sire, const TCHAR* Dam, const TCHAR* SS, const TCHAR* SD, const TCHAR* DS, const TCHAR* DD, int32 Generation, float Hp, float Sta, float Food, float Weight, float Attack, float Speed)
        {
            FEWTameEntry E; E.Name = Name; E.Species = Species; E.Level = Level; E.Experience = Xp; E.ExperienceForNext = XpNext; E.Sire = Sire; E.Dam = Dam;
            E.SireSire = SS; E.SireDam = SD; E.DamSire = DS; E.DamDam = DD; E.Generation = Generation;
            E.Health = Hp; E.Stamina = Sta; E.Food = Food; E.Weight = Weight; E.Attack = Attack; E.Speed = Speed; return E;
        };
        Tames.Add(Make(TEXT("Shellby"), TEXT("Tortoise"), 4, 130, 260, TEXT("Old Barnacle"), TEXT("Pebble"), TEXT("Wild"), TEXT("Wild"), TEXT("Wild"), TEXT("Wild"), 2, 160.f, 70.f, 80.f, 90.f, 20.f, 40.f));
        Tames.Add(Make(TEXT("Ember"), TEXT("Flamingo"), 6, 410, 520, TEXT("Rosie"), TEXT("Wild"), TEXT("Wild"), TEXT("Wild"), TEXT("-"), TEXT("-"), 2, 90.f, 140.f, 70.f, 30.f, 35.f, 110.f));
        Tames.Add(Make(TEXT("Biscuit"), TEXT("Squirrel Monkey"), 3, 60, 200, TEXT("Wild"), TEXT("Wild"), TEXT("-"), TEXT("-"), TEXT("-"), TEXT("-"), 1, 70.f, 110.f, 60.f, 12.f, 25.f, 130.f));
        Tames.Add(Make(TEXT("Gator Jack"), TEXT("Alligator"), 9, 880, 1200, TEXT("Wild"), TEXT("Marsh Queen"), TEXT("-"), TEXT("-"), TEXT("Wild"), TEXT("Wild"), 2, 320.f, 100.f, 150.f, 220.f, 95.f, 55.f));
        Tames.Add(Make(TEXT("Skipper"), TEXT("Pelican"), 5, 240, 380, TEXT("Wild"), TEXT("Wild"), TEXT("-"), TEXT("-"), TEXT("-"), TEXT("-"), 1, 85.f, 120.f, 75.f, 45.f, 30.f, 95.f));

        auto* Root = WidgetTree->ConstructWidget<UHorizontalBox>(); WidgetTree->RootWidget = Root;
        // Left: the list of creatures.
        auto* ListBorder = WidgetTree->ConstructWidget<UBorder>(); ListBorder->SetPadding(FMargin(14)); ListBorder->SetBrushColor(Panel);
        auto* ListSlot = Root->AddChildToHorizontalBox(ListBorder); { auto S = FSlateChildSize(ESlateSizeRule::Fill); S.Value = 1.f; ListSlot->SetSize(S); }
        ListSlot->SetPadding(FMargin(0, 0, 12, 0));
        auto* ListColumn = WidgetTree->ConstructWidget<UVerticalBox>(); ListBorder->SetContent(ListColumn);
        Label(WidgetTree, ListColumn, FString::Printf(TEXT("TAMES  (%d)"), Tames.Num()), 18, FLinearColor(.88f, .86f, .8f), 4);
        Label(WidgetTree, ListColumn, TEXT("Sample creatures: taming is not in the game yet. Your own tames will fill this list."), 12, FLinearColor(.6f, .66f, .72f), 10);
        auto* ListScroll = WidgetTree->ConstructWidget<UScrollBox>(); ListColumn->AddChildToVerticalBox(ListScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* Rows = WidgetTree->ConstructWidget<UVerticalBox>(); ListScroll->AddChild(Rows);
        for (int32 Index = 0; Index < Tames.Num(); ++Index)
        {
            auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(2)); Ring->SetBrushColor(FLinearColor(0, 0, 0, 0));
            auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
            Button->SetBackgroundColor(FLinearColor(.07f, .085f, .1f, 1.f));
            Button->OnRecipePressed.AddDynamic(this, &UEWTamesWidget::RowPressed);
            auto* Row = WidgetTree->ConstructWidget<UVerticalBox>();
            Label(WidgetTree, Row, Tames[Index].Name, 17, FLinearColor::White, 0);
            Label(WidgetTree, Row, FString::Printf(TEXT("%s  ·  Level %d"), *Tames[Index].Species, Tames[Index].Level), 13, FLinearColor(.7f, .76f, .82f), 0);
            Button->SetContent(Row); Ring->SetContent(Button);
            Rows->AddChildToVerticalBox(Ring)->SetPadding(FMargin(0, 0, 0, 6));
            Rings.Add(Ring);
        }
        // Right: the picked creature.
        auto* DetailBorder = WidgetTree->ConstructWidget<UBorder>(); DetailBorder->SetPadding(FMargin(18)); DetailBorder->SetBrushColor(Panel);
        auto* DetailSlot = Root->AddChildToHorizontalBox(DetailBorder); { auto S = FSlateChildSize(ESlateSizeRule::Fill); S.Value = 2.2f; DetailSlot->SetSize(S); }
        auto* DetailScroll = WidgetTree->ConstructWidget<UScrollBox>(); DetailBorder->SetContent(DetailScroll);
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>(); DetailScroll->AddChild(Column);
        auto* Top = WidgetTree->ConstructWidget<UHorizontalBox>(); Column->AddChildToVerticalBox(Top)->SetPadding(FMargin(0, 0, 0, 16));
        // The picture. No creature art is in the game yet, so a framed placeholder stands in for it.
        auto* Frame = WidgetTree->ConstructWidget<UBorder>(); Frame->SetBrushColor(FLinearColor(.015f, .02f, .026f, .95f)); Frame->SetPadding(FMargin(8));
        auto* FrameSize = WidgetTree->ConstructWidget<USizeBox>(); FrameSize->SetWidthOverride(300); FrameSize->SetHeightOverride(220); FrameSize->SetContent(Frame);
        auto* FrameBody = WidgetTree->ConstructWidget<UVerticalBox>(); Frame->SetContent(FrameBody); Frame->SetHorizontalAlignment(HAlign_Center); Frame->SetVerticalAlignment(VAlign_Center);
        ImageGlyph = Label(WidgetTree, FrameBody, TEXT("❦"), 64, FLinearColor(.45f, .5f, .56f), 6); ImageGlyph->SetJustification(ETextJustify::Center);
        ImageCaption = Label(WidgetTree, FrameBody, TEXT(""), 13, FLinearColor(.6f, .66f, .72f), 0); ImageCaption->SetJustification(ETextJustify::Center);
        Top->AddChildToHorizontalBox(FrameSize)->SetPadding(FMargin(0, 0, 18, 0));
        auto* Heading = WidgetTree->ConstructWidget<UVerticalBox>(); Top->AddChildToHorizontalBox(Heading)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        NameText = Label(WidgetTree, Heading, TEXT(""), 28, FLinearColor::White, 2);
        SpeciesText = Label(WidgetTree, Heading, TEXT(""), 16, FLinearColor(.75f, .8f, .86f), 12);
        LevelText = Label(WidgetTree, Heading, TEXT(""), 20, Gold, 4);
        ExperienceBar = WidgetTree->ConstructWidget<UProgressBar>(); ExperienceBar->SetFillColorAndOpacity(FLinearColor(.45f, .78f, .95f));
        auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(10); BarSize->SetContent(ExperienceBar);
        Heading->AddChildToVerticalBox(BarSize);
        Label(WidgetTree, Column, TEXT("LINEAGE"), 15, FLinearColor(.88f, .86f, .8f), 6);
        LineageText = Label(WidgetTree, Column, TEXT(""), 15, FLinearColor(.85f, .87f, .9f), 18);
        Label(WidgetTree, Column, TEXT("STATS"), 15, FLinearColor(.88f, .86f, .8f), 6);
        static const TCHAR* StatNames[] = {TEXT("Health"), TEXT("Stamina"), TEXT("Food"), TEXT("Weight"), TEXT("Attack"), TEXT("Speed")};
        static const FLinearColor StatColours[] = {FLinearColor(.72f, .12f, .1f), FLinearColor(.86f, .68f, .12f), FLinearColor(.78f, .42f, .14f), FLinearColor(.55f, .6f, .66f), FLinearColor(.8f, .3f, .25f), FLinearColor(.3f, .75f, .5f)};
        for (int32 Stat = 0; Stat < 6; ++Stat)
        {
            auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>(); Column->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 8));
            auto* Name = Label(WidgetTree, nullptr, StatNames[Stat], 15, FLinearColor(.78f, .82f, .88f), 0);
            auto* NameSize = WidgetTree->ConstructWidget<USizeBox>(); NameSize->SetWidthOverride(110); NameSize->SetContent(Name);
            Row->AddChildToHorizontalBox(NameSize)->SetVerticalAlignment(VAlign_Center);
            auto* Bar = WidgetTree->ConstructWidget<UProgressBar>(); Bar->SetFillColorAndOpacity(StatColours[Stat]);
            auto* StatBarSize = WidgetTree->ConstructWidget<USizeBox>(); StatBarSize->SetHeightOverride(10); StatBarSize->SetContent(Bar);
            auto* BarSlot = Row->AddChildToHorizontalBox(StatBarSize); BarSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); BarSlot->SetVerticalAlignment(VAlign_Center);
            auto* Value = Label(WidgetTree, nullptr, TEXT(""), 15, FLinearColor::White, 0); Value->SetJustification(ETextJustify::Right);
            auto* ValueSize = WidgetTree->ConstructWidget<USizeBox>(); ValueSize->SetWidthOverride(70); ValueSize->SetContent(Value);
            Row->AddChildToHorizontalBox(ValueSize)->SetVerticalAlignment(VAlign_Center);
            StatValues.Add(Value); StatBars.Add(Bar);
        }
        Refresh();
    }
    return Super::RebuildWidget();
}

void UEWTamesWidget::SelectTame(int32 Index)
{
    if (Tames.IsEmpty()) return;
    Selected = FMath::Clamp(Index, 0, Tames.Num() - 1);
    Refresh();
}

void UEWTamesWidget::Refresh()
{
    if (!Tames.IsValidIndex(Selected) || !NameText) return;
    for (int32 Index = 0; Index < Rings.Num(); ++Index) Rings[Index]->SetBrushColor(Index == Selected ? Gold : FLinearColor(0, 0, 0, 0));
    const FEWTameEntry& T = Tames[Selected];
    NameText->SetText(FText::FromString(T.Name));
    SpeciesText->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  Generation %d"), *T.Species, T.Generation)));
    LevelText->SetText(FText::FromString(FString::Printf(TEXT("LEVEL %d     %d / %d xp"), T.Level, T.Experience, T.ExperienceForNext)));
    ExperienceBar->SetPercent(T.ExperienceForNext > 0 ? FMath::Clamp(float(T.Experience) / T.ExperienceForNext, 0.f, 1.f) : 1.f);
    ImageCaption->SetText(FText::FromString(FString::Printf(TEXT("%s\n(picture placeholder)"), *T.Species)));
    LineageText->SetText(FText::FromString(FString::Printf(
        TEXT("Sire:  %s          Dam:  %s\n   Sire's sire:  %s          Dam's sire:  %s\n   Sire's dam:  %s          Dam's dam:  %s"),
        *T.Sire, *T.Dam, *T.SireSire, *T.DamSire, *T.SireDam, *T.DamDam)));
    const float Values[] = {T.Health, T.Stamina, T.Food, T.Weight, T.Attack, T.Speed};
    for (int32 Stat = 0; Stat < StatValues.Num(); ++Stat)
    {
        StatValues[Stat]->SetText(FText::FromString(FString::Printf(TEXT("%.0f"), Values[Stat])));
        StatBars[Stat]->SetPercent(FMath::Clamp(Values[Stat] / 350.f, 0.f, 1.f));
    }
}

FText UEWTamesWidget::GetShownName() const { return NameText ? NameText->GetText() : FText::GetEmpty(); }
FText UEWTamesWidget::GetShownLineage() const { return LineageText ? LineageText->GetText() : FText::GetEmpty(); }
FText UEWTamesWidget::GetShownLevel() const { return LevelText ? LevelText->GetText() : FText::GetEmpty(); }
