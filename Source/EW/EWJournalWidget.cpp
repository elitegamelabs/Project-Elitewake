#include "EWJournalWidget.h"
#include "EWInventoryWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Texture2D.h"
#include "EWDiscoveryComponent.h"
#include "EWPlayerController.h"
#include "World/EWClimateRegion.h"
#include "World/EWPlaces.h"

namespace
{
// An explorer's journal (owner, October 22): dark ink on aged paper. The list is a strip of the same paper a shade darker, the chosen entry underlined in a brown wash.
const FLinearColor Ink(.17f, .1f, .05f);
const FLinearColor InkFaded(.28f, .18f, .09f);
const FLinearColor InkTitle(.36f, .08f, .05f);

UTextBlock* MakeText(UWidgetTree* Tree, const FText& Value, int32 Size, const FLinearColor& Colour = Ink, bool bBold = false)
{
    auto* T = Tree->ConstructWidget<UTextBlock>();
    T->SetText(Value); T->SetAutoWrapText(true); T->SetColorAndOpacity(FSlateColor(Colour));
    auto Font = T->GetFont(); Font.Size = Size; if (bBold) Font.TypefaceFontName = FName("Bold");
    T->SetFont(Font);
    return T;
}

/** A page of aged paper behind whatever goes in it: the picture fills the frame, the content sits inside a margin. */
UOverlay* PaperWith(UWidgetTree* Tree, UWidget* Content, const FMargin& Margin, const FLinearColor& Tint)
{
    auto* Overlay = Tree->ConstructWidget<UOverlay>();
    auto* Paper = Tree->ConstructWidget<UImage>();
    if (UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/Elitewake/UI/Journal/T_JournalParchment.T_JournalParchment")))
        Paper->SetBrushFromTexture(Texture, false);
    Paper->SetColorAndOpacity(Tint);
    auto* PaperSlot = Overlay->AddChildToOverlay(Paper);
    PaperSlot->SetHorizontalAlignment(HAlign_Fill); PaperSlot->SetVerticalAlignment(VAlign_Fill);
    auto* ContentSlot = Overlay->AddChildToOverlay(Content);
    ContentSlot->SetHorizontalAlignment(HAlign_Fill); ContentSlot->SetVerticalAlignment(VAlign_Fill); ContentSlot->SetPadding(Margin);
    return Overlay;
}
}

TSharedRef<SWidget> UEWJournalWidget::RebuildWidget()
{
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
    if (const UEWJournalData* Data = Journal.LoadSynchronous()) GuidePages = Data->Entries;
    Pages = GuidePages;
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    WidgetTree->RootWidget = Row;

    // The list of pages, grouped by section, on a strip of paper a shade darker than the page.
    auto* ListScroll = WidgetTree->ConstructWidget<UScrollBox>();
    PageList = WidgetTree->ConstructWidget<UVerticalBox>(); ListScroll->AddChild(PageList);
    auto* ListSlot = Row->AddChildToHorizontalBox(PaperWith(WidgetTree, ListScroll, FMargin(30, 26, 24, 26), FLinearColor(.82f, .72f, .6f)));
    FSlateChildSize ListSize(ESlateSizeRule::Fill); ListSize.Value = .7f;
    ListSlot->SetSize(ListSize); ListSlot->SetPadding(FMargin(0, 12, 8, 0));
    FillList();

    // The chosen page: a leaf of aged paper written in dark ink.
    auto* PageScroll = WidgetTree->ConstructWidget<UScrollBox>();
    auto* Page = WidgetTree->ConstructWidget<UVerticalBox>(); PageScroll->AddChild(Page);
    auto* PageSlot = Row->AddChildToHorizontalBox(PaperWith(WidgetTree, PageScroll, FMargin(54, 40, 50, 40), FLinearColor::White));
    FSlateChildSize PageSize(ESlateSizeRule::Fill); PageSize.Value = 1.6f;
    PageSlot->SetSize(PageSize); PageSlot->SetPadding(FMargin(0, 12, 16, 0));
    PageTitle = MakeText(WidgetTree, FText::GetEmpty(), 26, InkTitle, true);
    Page->AddChildToVerticalBox(PageTitle)->SetPadding(FMargin(0, 0, 0, 6));
    // An ink rule under the heading.
    auto* Rule = WidgetTree->ConstructWidget<UBorder>(); Rule->SetBrushColor(FLinearColor(.17f, .1f, .05f, .55f)); Rule->SetPadding(FMargin(0, 1));
    Page->AddChildToVerticalBox(Rule)->SetPadding(FMargin(0, 0, 0, 16));
    PageBody = MakeText(WidgetTree, Pages.IsEmpty() ? NSLOCTEXT("Elitewake", "JournalEmpty", "No pages yet.") : FText::GetEmpty(), 17);
    Page->AddChildToVerticalBox(PageBody);
    if (!Pages.IsEmpty()) ShowPage(0);
    return Super::RebuildWidget();
}

void UEWJournalWidget::FillList()
{
    if (!PageList) return;
    PageList->ClearChildren();
    PageButtons.Reset();
    PageList->AddChildToVerticalBox(MakeText(WidgetTree, NSLOCTEXT("Elitewake", "JournalHeading", "JOURNAL"), 20, InkTitle, true))->SetPadding(FMargin(0, 0, 0, 4));
    PageList->AddChildToVerticalBox(MakeText(WidgetTree, NSLOCTEXT("Elitewake", "JournalTestNote",
        "Your discoveries, then the playtest guides. The Quartermaster's own guidance will replace the guides."), 12, InkFaded))->SetPadding(FMargin(0, 0, 0, 12));
    FString LastSection;
    for (int32 Index = 0; Index < Pages.Num(); ++Index)
    {
        const FString Section = Pages[Index].Section.ToString();
        if (Section != LastSection)
        {
            PageList->AddChildToVerticalBox(MakeText(WidgetTree, FText::FromString(Section.ToUpper()), 13, InkTitle, true))
                ->SetPadding(FMargin(0, 12, 0, 4));
            LastSection = Section;
        }
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
        Button->OnRecipePressed.AddDynamic(this, &UEWJournalWidget::ShowPage);
        Button->SetContent(MakeText(WidgetTree, Pages[Index].Title, 15));
        // Paper shows through the buttons: only the chosen one is washed in brown.
        FButtonStyle Flat = Button->GetStyle();
        Flat.Normal.TintColor = FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f)); Flat.Hovered.TintColor = FSlateColor(FLinearColor(.45f, .27f, .1f, .14f));
        Flat.Pressed.TintColor = FSlateColor(FLinearColor(.45f, .27f, .1f, .3f)); Flat.Disabled.TintColor = Flat.Normal.TintColor;
        Button->SetStyle(Flat);
        PageList->AddChildToVerticalBox(Button)->SetPadding(FMargin(0, 0, 0, 2));
        PageButtons.Add(Button);
    }
}

void UEWJournalWidget::RefreshDiscoveries()
{
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const UEWDiscoveryComponent* Found = PC ? PC->GetDiscoveries() : nullptr;
    const int32 Count = Found ? Found->GetDiscoveries().Num() : 0;
    if (Count == ShownDiscoveries && Pages.Num() > 0) return;
    ShownDiscoveries = Count;
    const FText Section = NSLOCTEXT("Elitewake", "JournalDiscoveries", "Discoveries");
    TArray<FEWJournalEntry> Built;
    // The summary: how much of the world has been found, kind by kind.
    {
        FEWJournalEntry& Summary = Built.AddDefaulted_GetRef();
        Summary.Section = Section;
        Summary.Title = NSLOCTEXT("Elitewake", "JournalDiscoveriesSummary", "The voyage so far");
        FString Body = TEXT("Every island, Freeport, reef and cave you reach, and every kind of creature you come near, is written here.\n\n");
        for (EEWPlaceKind Kind : {EEWPlaceKind::Island, EEWPlaceKind::Freeport, EEWPlaceKind::Reef, EEWPlaceKind::Cave})
            Body += FString::Printf(TEXT("%s: %d of %d\n"), *EWPlaces::KindName(Kind).ToString(), Found ? Found->CountOf(Kind) : 0,
                UEWDiscoveryComponent::PlacesOf(Kind));
        Body += FString::Printf(TEXT("%s: %d\n"), *EWPlaces::KindName(EEWPlaceKind::Creature).ToString(),
            Found ? Found->CountOf(EEWPlaceKind::Creature) : 0);
        if (Count == 0) Body += TEXT("\nNothing yet. Go and look.");
        Summary.Body = FText::FromString(Body);
    }
    // One page a discovery, grouped by kind, in the order found.
    if (Found)
        for (EEWPlaceKind Kind : {EEWPlaceKind::Island, EEWPlaceKind::Freeport, EEWPlaceKind::Reef, EEWPlaceKind::Cave, EEWPlaceKind::Creature})
            for (const FEWDiscovery& D : Found->GetDiscoveries())
            {
                if (D.Kind != Kind) continue;
                FEWJournalEntry& Page = Built.AddDefaulted_GetRef();
                Page.Section = FText::Format(NSLOCTEXT("Elitewake", "JournalDiscoveredKind", "Discovered {0}"), EWPlaces::KindName(Kind));
                Page.Title = D.Name;
                FString Body;
                if (const EWPlaces::FPlace* Place = EWPlaces::Find(D.Id))
                    if (Place->Region != EEWRegion::OpenSea) Body = AEWClimateRegion::RegionName(Place->Region).ToString() + TEXT(". ");
                Page.Body = FText::FromString(Body + D.Note.ToString());
            }
    const FText Shown = GetShownTitle();
    Pages = MoveTemp(Built);
    Pages.Append(GuidePages);
    FillList();
    // Keep the same page open if it is still there.
    int32 Keep = 0;
    for (int32 I = 0; I < Pages.Num(); ++I) if (Pages[I].Title.EqualTo(Shown)) { Keep = I; break; }
    if (!Pages.IsEmpty()) ShowPage(Keep);
}

void UEWJournalWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (GetVisibility() != ESlateVisibility::Collapsed) RefreshDiscoveries();
}

void UEWJournalWidget::ShowPage(int32 Index)
{
    if (!Pages.IsValidIndex(Index) || !PageTitle || !PageBody) return;
    Selected = Index;
    PageTitle->SetText(Pages[Index].Title);
    PageBody->SetText(Pages[Index].Body);
    for (int32 I = 0; I < PageButtons.Num(); ++I)
        PageButtons[I]->SetBackgroundColor(I == Selected ? FLinearColor(.45f, .27f, .1f, .55f) : FLinearColor(1.f, 1.f, 1.f, 1.f));
}

FText UEWJournalWidget::GetShownTitle() const
{
    return Pages.IsValidIndex(Selected) ? Pages[Selected].Title : FText::GetEmpty();
}
