#include "EWJournalWidget.h"
#include "EWInventoryWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

namespace
{
const FLinearColor Ink(.85f, .87f, .9f);
const FLinearColor Chosen(.5f, .52f, .55f), Unchosen(.07f, .085f, .1f);

UTextBlock* MakeText(UWidgetTree* Tree, const FText& Value, int32 Size, const FLinearColor& Colour = Ink)
{
    auto* T = Tree->ConstructWidget<UTextBlock>();
    T->SetText(Value); T->SetAutoWrapText(true); T->SetColorAndOpacity(FSlateColor(Colour));
    auto Font = T->GetFont(); Font.Size = Size; T->SetFont(Font);
    return T;
}
}

TSharedRef<SWidget> UEWJournalWidget::RebuildWidget()
{
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
    if (const UEWJournalData* Data = Journal.LoadSynchronous()) Pages = Data->Entries;
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    WidgetTree->RootWidget = Row;

    // The list of pages, grouped by section.
    auto* ListBorder = WidgetTree->ConstructWidget<UBorder>();
    ListBorder->SetPadding(FMargin(12)); ListBorder->SetBrushColor(FLinearColor(.025f, .035f, .045f, .94f));
    auto* ListSlot = Row->AddChildToHorizontalBox(ListBorder);
    FSlateChildSize ListSize(ESlateSizeRule::Fill); ListSize.Value = .7f;
    ListSlot->SetSize(ListSize); ListSlot->SetPadding(FMargin(0, 12, 16, 0));
    auto* ListScroll = WidgetTree->ConstructWidget<UScrollBox>(); ListBorder->SetContent(ListScroll);
    auto* List = WidgetTree->ConstructWidget<UVerticalBox>(); ListScroll->AddChild(List);
    List->AddChildToVerticalBox(MakeText(WidgetTree, NSLOCTEXT("Elitewake", "JournalHeading", "JOURNAL"), 18))->SetPadding(FMargin(0, 0, 0, 4));
    List->AddChildToVerticalBox(MakeText(WidgetTree, NSLOCTEXT("Elitewake", "JournalTestNote",
        "Playtest guides. The Quartermaster's own guidance will replace them."), 12, FLinearColor(.6f, .64f, .68f)))->SetPadding(FMargin(0, 0, 0, 12));
    FString LastSection;
    for (int32 Index = 0; Index < Pages.Num(); ++Index)
    {
        const FString Section = Pages[Index].Section.ToString();
        if (Section != LastSection)
        {
            List->AddChildToVerticalBox(MakeText(WidgetTree, FText::FromString(Section.ToUpper()), 13, FLinearColor(.75f, .66f, .45f)))
                ->SetPadding(FMargin(0, 10, 0, 4));
            LastSection = Section;
        }
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
        Button->OnRecipePressed.AddDynamic(this, &UEWJournalWidget::ShowPage);
        Button->SetContent(MakeText(WidgetTree, Pages[Index].Title, 15));
        List->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 0, 0, 4));
        PageButtons.Add(Button);
    }

    // The chosen page.
    auto* PageBorder = WidgetTree->ConstructWidget<UBorder>();
    PageBorder->SetPadding(FMargin(20)); PageBorder->SetBrushColor(FLinearColor(.035f, .045f, .055f, .95f));
    auto* PageSlot = Row->AddChildToHorizontalBox(PageBorder);
    FSlateChildSize PageSize(ESlateSizeRule::Fill); PageSize.Value = 1.6f;
    PageSlot->SetSize(PageSize); PageSlot->SetPadding(FMargin(0, 12, 16, 0));
    auto* PageScroll = WidgetTree->ConstructWidget<UScrollBox>(); PageBorder->SetContent(PageScroll);
    auto* Page = WidgetTree->ConstructWidget<UVerticalBox>(); PageScroll->AddChild(Page);
    PageTitle = MakeText(WidgetTree, FText::GetEmpty(), 22);
    Page->AddChildToVerticalBox(PageTitle)->SetPadding(FMargin(0, 0, 0, 14));
    PageBody = MakeText(WidgetTree, Pages.IsEmpty() ? NSLOCTEXT("Elitewake", "JournalEmpty", "No pages yet.") : FText::GetEmpty(), 16);
    Page->AddChildToVerticalBox(PageBody);
    if (!Pages.IsEmpty()) ShowPage(0);
    return Super::RebuildWidget();
}

void UEWJournalWidget::ShowPage(int32 Index)
{
    if (!Pages.IsValidIndex(Index) || !PageTitle || !PageBody) return;
    Selected = Index;
    PageTitle->SetText(Pages[Index].Title);
    PageBody->SetText(Pages[Index].Body);
    for (int32 I = 0; I < PageButtons.Num(); ++I)
        PageButtons[I]->SetBackgroundColor(I == Selected ? Chosen : Unchosen);
}

FText UEWJournalWidget::GetShownTitle() const
{
    return Pages.IsValidIndex(Selected) ? Pages[Selected].Title : FText::GetEmpty();
}
