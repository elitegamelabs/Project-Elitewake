#include "EWCompanyWidget.h"
#include "EWInventoryWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "InputCoreTypes.h"
#include "Misc/DateTime.h"

namespace
{
    const FLinearColor Gold(1.f, .85f, .35f, 1.f);
    const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
    const FLinearColor PanelColour(.03f, .036f, .042f, .78f);
    const FLinearColor RowColour(.07f, .085f, .1f, 1.f);
    const FLinearColor RowPicked(.2f, .24f, .29f, 1.f);
    const TCHAR* YouName = TEXT("Survivor (you)");
    const int32 ActionCount = 5;

    FLinearColor RankColour(EEWSampleRank Rank)
    {
        switch (Rank)
        {
            case EEWSampleRank::Leader: return Gold;
            case EEWSampleRank::Officer: return FLinearColor(.55f, .78f, 1.f);
            case EEWSampleRank::Member: return FLinearColor::White;
            default: return FLinearColor(.65f, .68f, .72f);
        }
    }
}

FString UEWCompanyWidget::RankName(EEWSampleRank Rank)
{
    switch (Rank)
    {
        case EEWSampleRank::Leader: return TEXT("Leader");
        case EEWSampleRank::Officer: return TEXT("Officer");
        case EEWSampleRank::Member: return TEXT("Member");
        default: return TEXT("Recruit");
    }
}

int32 UEWCompanyWidget::IndexOfName(const FString& Name) const
{
    return Members.IndexOfByPredicate([&Name](const FEWSampleMember& M) { return M.Name == Name; });
}
int32 UEWCompanyWidget::YouIndex() const { return IndexOfName(YouName); }

void UEWCompanyWidget::BuildSampleData()
{
    auto Add = [this](const TCHAR* Name, EEWSampleRank Rank, bool bOnline, const TCHAR* Played, const TCHAR* Seen, const TCHAR* Info)
    {
        FEWSampleMember M; M.Name = Name; M.Rank = Rank; M.bOnline = bOnline; M.TimePlayed = Played; M.LastSeen = Seen; M.Info = Info; Members.Add(M);
    };
    Add(TEXT("Captain Maren Voss"), EEWSampleRank::Leader, true, TEXT("412 h"), TEXT("Online now"), TEXT("Founder. Keeps the ledger and the fleet in order."));
    Add(TEXT("Tobias Reed"), EEWSampleRank::Officer, true, TEXT("288 h"), TEXT("Online now"), TEXT("Quartermaster. Ask him before drawing from the stores."));
    Add(TEXT("Ilsa Brandt"), EEWSampleRank::Officer, false, TEXT("301 h"), TEXT("3 hours ago"), TEXT("Navigator. Charts the northern reefs."));
    Add(YouName, EEWSampleRank::Officer, true, TEXT("96 h"), TEXT("Online now"), TEXT("That is you."));
    Add(TEXT("Cato Fenwick"), EEWSampleRank::Member, true, TEXT("140 h"), TEXT("Online now"), TEXT("Carpenter. Always short of timber."));
    Add(TEXT("Wren Alder"), EEWSampleRank::Member, false, TEXT("77 h"), TEXT("Yesterday"), TEXT("Forager and cook."));
    Add(TEXT("Dara Oyelaran"), EEWSampleRank::Member, false, TEXT("122 h"), TEXT("2 days ago"), TEXT("Gunner on the Brigantine."));
    Add(TEXT("Nia Castellan"), EEWSampleRank::Member, false, TEXT("64 h"), TEXT("9 days ago"), TEXT("Rarely online. Trades in the spice islands."));
    Add(TEXT("Pip Marlowe"), EEWSampleRank::Recruit, true, TEXT("11 h"), TEXT("Online now"), TEXT("New this week. Eager."));
    Add(TEXT("Jonas Kell"), EEWSampleRank::Recruit, false, TEXT("6 h"), TEXT("5 days ago"), TEXT("Joined on a recommendation from Cato."));

    FEWSampleInvite Out; Out.Name = TEXT("Rook Thistle"); Out.Sent = TEXT("Sent yesterday"); Invites.Add(Out);
    FEWSampleInvite In; In.Name = TEXT("The Ashgrove Wardens"); In.Sent = TEXT("Invited you 2 hours ago"); In.bIncoming = true; Invites.Add(In);

    auto Entry = [this](const TCHAR* Time, const TCHAR* Glyph, const TCHAR* Text)
    { FEWSampleLog L; L.Time = Time; L.Glyph = Glyph; L.Text = Text; Log.Add(L); };
    Entry(TEXT("09:12"), TEXT("★"), TEXT("Captain Maren Voss raised the company to level 7."));
    Entry(TEXT("08:47"), TEXT("▲"), TEXT("Tobias Reed promoted Cato Fenwick to Member."));
    Entry(TEXT("Yesterday"), TEXT("✉"), TEXT("Ilsa Brandt invited Rook Thistle."));
    Entry(TEXT("Yesterday"), TEXT("⚓"), TEXT("The Brigantine was docked at the central harbour."));
    Entry(TEXT("2 days ago"), TEXT("+"), TEXT("Pip Marlowe joined the company as a Recruit."));
    Entry(TEXT("5 days ago"), TEXT("✖"), TEXT("A recruit left the company."));
    Selected = YouIndex() == 0 ? 1 : 0;
}

TSharedRef<SWidget> UEWCompanyWidget::RebuildWidget()
{
    if (!WidgetTree || WidgetTree->RootWidget) return Super::RebuildWidget();
    BuildSampleData();

    auto Text = [this](UVerticalBox* Into, const FString& Value, int32 Size, const FLinearColor& Colour, float Below, bool bWrap = true)
    {
        auto* T = WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Value)); T->SetAutoWrapText(bWrap);
        T->SetColorAndOpacity(FSlateColor(Colour)); auto F = T->GetFont(); F.Size = Size; T->SetFont(F);
        if (Into) Into->AddChildToVerticalBox(T)->SetPadding(FMargin(0, 0, 0, Below));
        return T;
    };
    auto Panel = [this](const FMargin& Inset)
    {
        auto* B = WidgetTree->ConstructWidget<UBorder>(); B->SetPadding(Inset); B->SetBrushColor(PanelColour); return B;
    };
    // A button wearing a ring: the ring is the cursor, gold on the picked one.
    auto Button = [this](const FString& Label, int32 Index, int32 Size, UBorder*& Ring, UEWRecipeButton*& Out)
    {
        Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(2)); Ring->SetBrushColor(Clear);
        Out = WidgetTree->ConstructWidget<UEWRecipeButton>(); Out->Initialize(Index); Out->SetBackgroundColor(RowColour);
        auto* T = WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Label)); T->SetJustification(ETextJustify::Center);
        auto F = T->GetFont(); F.Size = Size; T->SetFont(F); Out->SetContent(T); Ring->SetContent(Out);
    };

    auto* Root = WidgetTree->ConstructWidget<UOverlay>(); WidgetTree->RootWidget = Root;
    auto* Main = WidgetTree->ConstructWidget<UVerticalBox>(); Root->AddChildToOverlay(Main);
    auto* Top = WidgetTree->ConstructWidget<UHorizontalBox>(); Main->AddChildToVerticalBox(Top)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto Column = [&](UWidget* Widget, float Weight, const FMargin& Inset)
    {
        auto* S = Top->AddChildToHorizontalBox(Widget); auto Size = FSlateChildSize(ESlateSizeRule::Fill); Size.Value = Weight; S->SetSize(Size); S->SetPadding(Inset);
    };

    // Left: the members, with search.
    auto* ListBorder = Panel(FMargin(14)); Column(ListBorder, 1.f, FMargin(0, 0, 10, 10));
    auto* ListColumn = WidgetTree->ConstructWidget<UVerticalBox>(); ListBorder->SetContent(ListColumn);
    ListHeading = Text(ListColumn, TEXT("COMPANY MEMBERS"), 17, FLinearColor(.88f, .86f, .8f), 8, false);
    SearchBox = WidgetTree->ConstructWidget<UEditableTextBox>(); SearchBox->SetHintText(FText::FromString(TEXT("Search members"))); EWStyleSearchBox(SearchBox);
    SearchBox->OnTextChanged.AddDynamic(this, &UEWCompanyWidget::SearchChanged);
    ListColumn->AddChildToVerticalBox(SearchBox)->SetPadding(FMargin(0, 0, 0, 8));
    MemberScroll = WidgetTree->ConstructWidget<UScrollBox>(); ListColumn->AddChildToVerticalBox(MemberScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    MemberList = WidgetTree->ConstructWidget<UVerticalBox>(); MemberScroll->AddChild(MemberList);

    // Centre: the company.
    auto* OverBorder = Panel(FMargin(18)); Column(OverBorder, 1.35f, FMargin(0, 0, 10, 10));
    auto* Over = WidgetTree->ConstructWidget<UVerticalBox>(); OverBorder->SetContent(Over);
    Text(Over, TEXT("FRONT-END PREVIEW  ·  sample data only. Nothing on this screen is sent to a server or changes the real game."), 12, FLinearColor(.95f, .75f, .35f), 12);
    auto* Head = WidgetTree->ConstructWidget<UHorizontalBox>(); Over->AddChildToVerticalBox(Head)->SetPadding(FMargin(0, 0, 0, 12));
    auto* Emblem = WidgetTree->ConstructWidget<UBorder>(); Emblem->SetBrushColor(FLinearColor(.1f, .14f, .2f, 1.f)); Emblem->SetHorizontalAlignment(HAlign_Center); Emblem->SetVerticalAlignment(VAlign_Center);
    auto* EmblemGlyph = Text(nullptr, TEXT("⚓"), 52, Gold, 0, false); Emblem->SetContent(EmblemGlyph);
    auto* EmblemSize = WidgetTree->ConstructWidget<USizeBox>(); EmblemSize->SetWidthOverride(96); EmblemSize->SetHeightOverride(96); EmblemSize->SetContent(Emblem);
    Head->AddChildToHorizontalBox(EmblemSize)->SetPadding(FMargin(0, 0, 16, 0));
    auto* HeadText = WidgetTree->ConstructWidget<UVerticalBox>(); Head->AddChildToHorizontalBox(HeadText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Text(HeadText, TEXT("The Gilded Gull Company"), 27, FLinearColor::White, 2);
    Text(HeadText, TEXT("LEVEL 7 COMPANY  ·  Open to new recruits"), 15, Gold, 6);
    auto* XpBar = WidgetTree->ConstructWidget<UProgressBar>(); XpBar->SetFillColorAndOpacity(FLinearColor(.45f, .78f, .95f)); XpBar->SetPercent(3450.f / 5000.f);
    auto* XpSize = WidgetTree->ConstructWidget<USizeBox>(); XpSize->SetHeightOverride(10); XpSize->SetContent(XpBar);
    HeadText->AddChildToVerticalBox(XpSize)->SetPadding(FMargin(0, 0, 0, 3));
    Text(HeadText, TEXT("Shared experience  3,450 / 5,000"), 12, FLinearColor(.7f, .76f, .82f), 0);
    Text(Over, TEXT("A trading and sailing company of the central islands. Members pool timber, share the docks and look out for one another on the open sea."), 15, FLinearColor(.85f, .87f, .9f), 14);
    OverviewCounts = Text(Over, TEXT(""), 16, FLinearColor::White, 4);
    OverviewLeader = Text(Over, TEXT(""), 16, FLinearColor::White, 4);
    Text(Over, TEXT("Created  2 October 2026"), 16, FLinearColor(.75f, .8f, .86f), 4);
    Text(Over, TEXT("Status  Recruiting · invitations welcome"), 16, FLinearColor(.75f, .8f, .86f), 14);
    ViewerText = Text(Over, TEXT(""), 15, FLinearColor(.75f, .85f, .95f), 6);
    {
        UBorder* Ring; UEWRecipeButton* B; Button(TEXT("Preview as another rank"), 0, 14, Ring, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::ViewAsPressed);
        auto* ViewSize = WidgetTree->ConstructWidget<USizeBox>(); ViewSize->SetWidthOverride(260); ViewSize->SetContent(Ring);
        Over->AddChildToVerticalBox(ViewSize)->SetHorizontalAlignment(HAlign_Left);
    }

    // Right: the picked member and what can be done with them.
    auto* DetailBorder = Panel(FMargin(16)); Column(DetailBorder, 1.1f, FMargin(0, 0, 0, 10));
    auto* Detail = WidgetTree->ConstructWidget<UVerticalBox>(); DetailBorder->SetContent(Detail);
    auto* DetailTop = WidgetTree->ConstructWidget<UHorizontalBox>(); Detail->AddChildToVerticalBox(DetailTop)->SetPadding(FMargin(0, 0, 0, 10));
    auto* Portrait = WidgetTree->ConstructWidget<UBorder>(); Portrait->SetBrushColor(FLinearColor(.015f, .02f, .026f, .95f)); Portrait->SetHorizontalAlignment(HAlign_Center); Portrait->SetVerticalAlignment(VAlign_Center);
    DetailGlyph = Text(nullptr, TEXT("?"), 38, FLinearColor(.6f, .66f, .72f), 0, false); Portrait->SetContent(DetailGlyph);
    auto* PortraitSize = WidgetTree->ConstructWidget<USizeBox>(); PortraitSize->SetWidthOverride(84); PortraitSize->SetHeightOverride(84); PortraitSize->SetContent(Portrait);
    DetailTop->AddChildToHorizontalBox(PortraitSize)->SetPadding(FMargin(0, 0, 14, 0));
    auto* DetailHead = WidgetTree->ConstructWidget<UVerticalBox>(); DetailTop->AddChildToHorizontalBox(DetailHead)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    DetailName = Text(DetailHead, TEXT(""), 21, FLinearColor::White, 2);
    DetailRank = Text(DetailHead, TEXT(""), 16, Gold, 2);
    DetailStatus = Text(DetailHead, TEXT(""), 14, FLinearColor(.5f, .85f, .55f), 0);
    DetailTime = Text(Detail, TEXT(""), 14, FLinearColor(.75f, .8f, .86f), 6);
    DetailInfo = Text(Detail, TEXT(""), 14, FLinearColor(.85f, .87f, .9f), 12);
    Text(Detail, TEXT("ACTIONS"), 13, FLinearColor(.88f, .86f, .8f), 6, false);
    const TCHAR* ActionLabels[] = {TEXT("Promote"), TEXT("Demote"), TEXT("Invite a player"), TEXT("Remove from company"), TEXT("Transfer leadership")};
    for (int32 Action = 0; Action < ActionCount; ++Action)
    {
        UBorder* Ring; UEWRecipeButton* B; Button(ActionLabels[Action], Action, 15, Ring, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::ActionPressed);
        Detail->AddChildToVerticalBox(Ring)->SetPadding(FMargin(0, 0, 0, 4));
        ActionRings.Add(Ring); ActionButtons.Add(B);
    }
    Text(Detail, TEXT("Left/Right pick an action · A or Enter does it · Up/Down pick a member · X or R changes the lower panel"), 11, FLinearColor(.55f, .6f, .66f), 0);

    // Bottom: activity, invitations, ranks.
    auto* BottomBorder = Panel(FMargin(14));
    auto* BottomSize = WidgetTree->ConstructWidget<USizeBox>(); BottomSize->SetHeightOverride(250); BottomSize->SetContent(BottomBorder);
    Main->AddChildToVerticalBox(BottomSize);
    auto* Bottom = WidgetTree->ConstructWidget<UVerticalBox>(); BottomBorder->SetContent(Bottom);
    auto* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>(); Bottom->AddChildToVerticalBox(Tabs)->SetPadding(FMargin(0, 0, 0, 8));
    const TCHAR* TabLabels[] = {TEXT("ACTIVITY"), TEXT("INVITATIONS"), TEXT("RANKS & PERMISSIONS")};
    for (int32 Tab = 0; Tab < 3; ++Tab)
    {
        UBorder* Ring; UEWRecipeButton* B; Button(TabLabels[Tab], Tab, 13, Ring, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::SubTabPressed);
        auto* S = Tabs->AddChildToHorizontalBox(Ring); S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetPadding(FMargin(0, 0, 4, 0));
        TabRings.Add(Ring);
    }
    auto* Pages = WidgetTree->ConstructWidget<UOverlay>(); Bottom->AddChildToVerticalBox(Pages)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* LogScroll = WidgetTree->ConstructWidget<UScrollBox>(); LogPage = LogScroll; Pages->AddChildToOverlay(LogScroll);
    LogBox = WidgetTree->ConstructWidget<UVerticalBox>(); LogScroll->AddChild(LogBox);
    auto* InviteColumn = WidgetTree->ConstructWidget<UVerticalBox>(); InvitePage = InviteColumn; Pages->AddChildToOverlay(InviteColumn);
    auto* InviteRow = WidgetTree->ConstructWidget<UHorizontalBox>(); InviteColumn->AddChildToVerticalBox(InviteRow)->SetPadding(FMargin(0, 0, 0, 6));
    InviteBox = WidgetTree->ConstructWidget<UEditableTextBox>(); InviteBox->SetHintText(FText::FromString(TEXT("Player name (leave empty for a sample player)"))); EWStyleSearchBox(InviteBox);
    InviteBox->OnTextCommitted.AddDynamic(this, &UEWCompanyWidget::InviteCommitted);
    InviteRow->AddChildToHorizontalBox(InviteBox)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    {
        UBorder* Ring; UEWRecipeButton* B; Button(TEXT("Invite"), 0, 14, Ring, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::InviteButtonPressed);
        auto* InviteSize = WidgetTree->ConstructWidget<USizeBox>(); InviteSize->SetWidthOverride(120); InviteSize->SetContent(Ring);
        InviteRow->AddChildToHorizontalBox(InviteSize)->SetPadding(FMargin(8, 0, 0, 0));
    }
    InviteStatus = Text(InviteColumn, TEXT(""), 12, FLinearColor(.95f, .75f, .35f), 4);
    auto* InviteScroll = WidgetTree->ConstructWidget<UScrollBox>(); InviteColumn->AddChildToVerticalBox(InviteScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    InviteListBox = WidgetTree->ConstructWidget<UVerticalBox>(); InviteScroll->AddChild(InviteListBox);
    auto* RolesScroll = WidgetTree->ConstructWidget<UScrollBox>(); RolesPage = RolesScroll; Pages->AddChildToOverlay(RolesScroll);
    RolesBox = WidgetTree->ConstructWidget<UVerticalBox>(); RolesScroll->AddChild(RolesBox);

    // The confirmation dialog for destructive actions.
    auto* Dim = WidgetTree->ConstructWidget<UBorder>(); Dim->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, .6f)); Dim->SetHorizontalAlignment(HAlign_Center); Dim->SetVerticalAlignment(VAlign_Center);
    DialogLayer = Dim; Root->AddChildToOverlay(Dim);
    auto* DialogBorder = WidgetTree->ConstructWidget<UBorder>(); DialogBorder->SetBrushColor(FLinearColor(.05f, .06f, .075f, 1.f)); DialogBorder->SetPadding(FMargin(24));
    auto* DialogSize = WidgetTree->ConstructWidget<USizeBox>(); DialogSize->SetWidthOverride(480); DialogSize->SetContent(DialogBorder); Dim->SetContent(DialogSize);
    auto* Dialog = WidgetTree->ConstructWidget<UVerticalBox>(); DialogBorder->SetContent(Dialog);
    DialogText = Text(Dialog, TEXT(""), 17, FLinearColor::White, 18);
    auto* DialogButtons = WidgetTree->ConstructWidget<UHorizontalBox>(); Dialog->AddChildToVerticalBox(DialogButtons);
    for (int32 Choice = 0; Choice < 2; ++Choice)
    {
        UBorder* Ring; UEWRecipeButton* B; Button(Choice == 0 ? TEXT("Cancel") : TEXT("Confirm"), Choice, 16, Ring, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::DialogPressed);
        auto* S = DialogButtons->AddChildToHorizontalBox(Ring); S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); S->SetPadding(FMargin(Choice == 0 ? 0 : 6, 0, Choice == 0 ? 6 : 0, 0));
        DialogRings.Add(Ring);
    }
    Dim->SetVisibility(ESlateVisibility::Collapsed);

    RebuildList(); RefreshInvites(); RefreshLog(); RefreshRoles(); RefreshAll();
    SetSubTab(0);
    return Super::RebuildWidget();
}

const FEWSampleMember* UEWCompanyWidget::SelectedMember() const { return Members.IsValidIndex(Selected) ? &Members[Selected] : nullptr; }
int32 UEWCompanyWidget::GetOnlineCount() const { int32 N = 0; for (const auto& M : Members) N += M.bOnline ? 1 : 0; return N; }
int32 UEWCompanyWidget::GetPendingInviteCount() const { int32 N = 0; for (const auto& I : Invites) N += I.bIncoming ? 0 : 1; return N; }
FText UEWCompanyWidget::GetSelectedName() const { const auto* M = SelectedMember(); return M ? FText::FromString(M->Name) : FText::GetEmpty(); }
FText UEWCompanyWidget::GetSelectedRankText() const { const auto* M = SelectedMember(); return M ? FText::FromString(RankName(M->Rank)) : FText::GetEmpty(); }
int32 UEWCompanyWidget::GetSelectedRank() const { const auto* M = SelectedMember(); return M ? static_cast<int32>(M->Rank) : -1; }
int32 UEWCompanyWidget::GetViewerRank() const { return Members.IsValidIndex(YouIndex()) ? static_cast<int32>(Members[YouIndex()].Rank) : 0; }
bool UEWCompanyWidget::IsTyping() const { return (SearchBox && SearchBox->HasKeyboardFocus()) || (InviteBox && InviteBox->HasKeyboardFocus()); }

bool UEWCompanyWidget::IsPointerOverTextBox(const FVector2D& At) const
{
    return (SearchBox && SearchBox->GetCachedGeometry().IsUnderLocation(At)) || (InviteBox && InviteBox->GetCachedGeometry().IsUnderLocation(At));
}

bool UEWCompanyWidget::IsActionEnabled(int32 Action) const
{
    if (!Members.IsValidIndex(YouIndex())) return false;
    const EEWSampleRank Viewer = Members[YouIndex()].Rank;
    const bool bOfficer = Viewer >= EEWSampleRank::Officer;
    if (Action == 2) return bOfficer;
    const FEWSampleMember* Target = SelectedMember();
    if (!Target || Selected == YouIndex()) return false;
    const EEWSampleRank T = Target->Rank;
    switch (Action)
    {
        case 0: return bOfficer && T < EEWSampleRank::Officer && (Viewer == EEWSampleRank::Leader || T == EEWSampleRank::Recruit);
        case 1: return bOfficer && T > EEWSampleRank::Recruit && T < Viewer;
        case 3: return bOfficer && T < Viewer;
        case 4: return Viewer == EEWSampleRank::Leader;
        default: return false;
    }
}

void UEWCompanyWidget::AddLog(const FString& Glyph, const FString& Text)
{
    FEWSampleLog L; L.Time = FDateTime::Now().ToString(TEXT("%H:%M")); L.Glyph = Glyph; L.Text = Text;
    Log.Insert(L, 0);
    RefreshLog();
}

void UEWCompanyWidget::RebuildList()
{
    if (!MemberList) return;
    MemberList->ClearChildren(); MemberRings.Reset(); Shown.Reset();
    for (int32 Index = 0; Index < Members.Num(); ++Index)
        if (Filter.IsEmpty() || Members[Index].Name.Contains(Filter, ESearchCase::IgnoreCase)) Shown.Add(Index);
    for (int32 Index : Shown)
    {
        const FEWSampleMember& M = Members[Index];
        auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(2));
        auto* Row = WidgetTree->ConstructWidget<UEWRecipeButton>(); Row->Initialize(Index);
        Row->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::MemberPressed);
        Row->SetBackgroundColor(Index == Selected ? RowPicked : RowColour);
        auto* Line = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Face = WidgetTree->ConstructWidget<UBorder>(); Face->SetBrushColor(FLinearColor(.015f, .02f, .026f, .95f)); Face->SetHorizontalAlignment(HAlign_Center); Face->SetVerticalAlignment(VAlign_Center);
        auto* Initial = WidgetTree->ConstructWidget<UTextBlock>(); Initial->SetText(FText::FromString(M.Name.Left(1))); { auto F = Initial->GetFont(); F.Size = 18; Initial->SetFont(F); }
        Initial->SetColorAndOpacity(FSlateColor(RankColour(M.Rank))); Face->SetContent(Initial);
        auto* FaceSize = WidgetTree->ConstructWidget<USizeBox>(); FaceSize->SetWidthOverride(42); FaceSize->SetHeightOverride(42); FaceSize->SetContent(Face);
        Line->AddChildToHorizontalBox(FaceSize)->SetPadding(FMargin(0, 0, 10, 0));
        auto* Words = WidgetTree->ConstructWidget<UVerticalBox>(); Line->AddChildToHorizontalBox(Words)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* NameText = WidgetTree->ConstructWidget<UTextBlock>(); NameText->SetText(FText::FromString(M.Name)); { auto F = NameText->GetFont(); F.Size = 15; NameText->SetFont(F); }
        Words->AddChildToVerticalBox(NameText);
        auto* Sub = WidgetTree->ConstructWidget<UTextBlock>(); Sub->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s"), *RankName(M.Rank), M.bOnline ? TEXT("Online") : TEXT("Offline"))));
        Sub->SetColorAndOpacity(FSlateColor(M.bOnline ? FLinearColor(.5f, .85f, .55f) : FLinearColor(.6f, .64f, .68f))); { auto F = Sub->GetFont(); F.Size = 12; Sub->SetFont(F); }
        Words->AddChildToVerticalBox(Sub);
        if (M.Rank == EEWSampleRank::Leader)
        {
            auto* Star = WidgetTree->ConstructWidget<UTextBlock>(); Star->SetText(FText::FromString(TEXT("★"))); Star->SetColorAndOpacity(FSlateColor(Gold)); { auto F = Star->GetFont(); F.Size = 20; Star->SetFont(F); }
            Line->AddChildToHorizontalBox(Star)->SetVerticalAlignment(VAlign_Center);
        }
        Row->SetContent(Line); Ring->SetContent(Row);
        MemberList->AddChildToVerticalBox(Ring)->SetPadding(FMargin(0, 0, 0, 4));
        MemberRings.Add(Ring);
    }
    if (ListHeading) ListHeading->SetText(FText::FromString(FString::Printf(TEXT("COMPANY MEMBERS  (%d)"), Filter.IsEmpty() ? Members.Num() : Shown.Num())));
    if (Shown.IsEmpty())
    {
        auto* None = WidgetTree->ConstructWidget<UTextBlock>(); None->SetText(FText::FromString(TEXT("No member matches that search."))); None->SetColorAndOpacity(FSlateColor(FLinearColor(.6f, .66f, .72f)));
        MemberList->AddChildToVerticalBox(None);
    }
}

void UEWCompanyWidget::RefreshAll()
{
    for (int32 Place = 0; Place < MemberRings.Num(); ++Place)
    {
        const bool bPicked = Shown.IsValidIndex(Place) && Shown[Place] == Selected;
        MemberRings[Place]->SetBrushColor(bPicked ? Gold : Clear);
        if (auto* Row = Cast<UEWRecipeButton>(MemberRings[Place]->GetContent())) Row->SetBackgroundColor(bPicked ? RowPicked : RowColour);
    }
    const FEWSampleMember* M = SelectedMember();
    if (M)
    {
        DetailName->SetText(FText::FromString(M->Name)); DetailRank->SetText(FText::FromString(RankName(M->Rank))); DetailRank->SetColorAndOpacity(FSlateColor(RankColour(M->Rank)));
        DetailStatus->SetText(FText::FromString(M->bOnline ? TEXT("● Online") : TEXT("○ Offline")));
        DetailStatus->SetColorAndOpacity(FSlateColor(M->bOnline ? FLinearColor(.5f, .85f, .55f) : FLinearColor(.6f, .64f, .68f)));
        DetailTime->SetText(FText::FromString(FString::Printf(TEXT("Time played  %s\nLast seen  %s"), *M->TimePlayed, *M->LastSeen)));
        DetailInfo->SetText(FText::FromString(M->Info));
        DetailGlyph->SetText(FText::FromString(M->Name.Left(1)));
    }
    else
    {
        DetailName->SetText(FText::FromString(TEXT("No member picked"))); DetailRank->SetText(FText::GetEmpty()); DetailStatus->SetText(FText::GetEmpty());
        DetailTime->SetText(FText::GetEmpty()); DetailInfo->SetText(FText::GetEmpty()); DetailGlyph->SetText(FText::FromString(TEXT("?")));
    }
    for (int32 Action = 0; Action < ActionButtons.Num(); ++Action)
    {
        const bool bEnabled = IsActionEnabled(Action);
        ActionButtons[Action]->SetIsEnabled(bEnabled); ActionButtons[Action]->SetRenderOpacity(bEnabled ? 1.f : .4f);
        ActionRings[Action]->SetBrushColor(Action == ActionCursor ? (bEnabled ? Gold : FLinearColor(.45f, .4f, .2f, 1.f)) : Clear);
    }
    if (OverviewCounts) OverviewCounts->SetText(FText::FromString(FString::Printf(TEXT("Members  %d total  ·  %d online"), Members.Num(), GetOnlineCount())));
    if (OverviewLeader)
    {
        const auto* Leader = Members.FindByPredicate([](const FEWSampleMember& Candidate) { return Candidate.Rank == EEWSampleRank::Leader; });
        OverviewLeader->SetText(FText::FromString(FString::Printf(TEXT("Leader  ★ %s"), Leader ? *Leader->Name : TEXT("none"))));
    }
    if (ViewerText && Members.IsValidIndex(YouIndex()))
        ViewerText->SetText(FText::FromString(FString::Printf(TEXT("You are viewing this screen as: %s"), *RankName(Members[YouIndex()].Rank))));
    for (int32 Tab = 0; Tab < TabRings.Num(); ++Tab) TabRings[Tab]->SetBrushColor(Tab == SubTab ? Gold : Clear);
    for (int32 Choice = 0; Choice < DialogRings.Num(); ++Choice) DialogRings[Choice]->SetBrushColor(Choice == DialogChoice ? Gold : Clear);
    RefreshRoles();
}

void UEWCompanyWidget::RefreshLog()
{
    if (!LogBox) return;
    LogBox->ClearChildren();
    for (const FEWSampleLog& L : Log)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Time = WidgetTree->ConstructWidget<UTextBlock>(); Time->SetText(FText::FromString(L.Time)); Time->SetColorAndOpacity(FSlateColor(FLinearColor(.6f, .66f, .72f))); { auto F = Time->GetFont(); F.Size = 13; Time->SetFont(F); }
        auto* TimeSize = WidgetTree->ConstructWidget<USizeBox>(); TimeSize->SetWidthOverride(86); TimeSize->SetContent(Time); Row->AddChildToHorizontalBox(TimeSize);
        auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(L.Glyph)); Glyph->SetColorAndOpacity(FSlateColor(Gold)); { auto F = Glyph->GetFont(); F.Size = 14; Glyph->SetFont(F); }
        auto* GlyphSize = WidgetTree->ConstructWidget<USizeBox>(); GlyphSize->SetWidthOverride(28); GlyphSize->SetContent(Glyph); Row->AddChildToHorizontalBox(GlyphSize);
        auto* Entry = WidgetTree->ConstructWidget<UTextBlock>(); Entry->SetText(FText::FromString(L.Text)); Entry->SetAutoWrapText(true); { auto F = Entry->GetFont(); F.Size = 14; Entry->SetFont(F); }
        Row->AddChildToHorizontalBox(Entry)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        LogBox->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 5));
    }
}

void UEWCompanyWidget::RefreshInvites()
{
    if (!InviteListBox) return;
    InviteListBox->ClearChildren();
    if (Invites.IsEmpty())
    {
        auto* None = WidgetTree->ConstructWidget<UTextBlock>(); None->SetText(FText::FromString(TEXT("No pending invitations."))); None->SetColorAndOpacity(FSlateColor(FLinearColor(.6f, .66f, .72f)));
        InviteListBox->AddChildToVerticalBox(None); return;
    }
    for (int32 Index = 0; Index < Invites.Num(); ++Index)
    {
        const FEWSampleInvite& I = Invites[Index];
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Words = WidgetTree->ConstructWidget<UTextBlock>();
        Words->SetText(FText::FromString(FString::Printf(TEXT("%s%s  ·  %s"), I.bIncoming ? TEXT("Incoming: ") : TEXT("Pending: "), *I.Name, *I.Sent))); { auto F = Words->GetFont(); F.Size = 14; Words->SetFont(F); }
        Row->AddChildToHorizontalBox(Words)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto AddButton = [&](const TCHAR* Label, int32 Code)
        {
            auto* B = WidgetTree->ConstructWidget<UEWRecipeButton>(); B->Initialize(Code); B->SetBackgroundColor(RowColour);
            B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::InviteRowPressed);
            auto* T = WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Label)); T->SetJustification(ETextJustify::Center); { auto F = T->GetFont(); F.Size = 13; T->SetFont(F); } B->SetContent(T);
            auto* S = WidgetTree->ConstructWidget<USizeBox>(); S->SetWidthOverride(96); S->SetContent(B);
            Row->AddChildToHorizontalBox(S)->SetPadding(FMargin(6, 0, 0, 0));
        };
        if (I.bIncoming) { AddButton(TEXT("Accept"), 100 + Index); AddButton(TEXT("Decline"), 200 + Index); }
        else AddButton(TEXT("Revoke"), Index);
        InviteListBox->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 5));
    }
}

void UEWCompanyWidget::RefreshRoles()
{
    if (!RolesBox || !Members.IsValidIndex(YouIndex())) return;
    RolesBox->ClearChildren();
    const int32 Viewer = static_cast<int32>(Members[YouIndex()].Rank);
    const TCHAR* Ranks[] = {TEXT("Recruit"), TEXT("Member"), TEXT("Officer"), TEXT("Leader")};
    struct FPermission { const TCHAR* Name; int32 MinRank; };
    const FPermission Permissions[] = {
        {TEXT("Use shared storage"), 1}, {TEXT("Dock company ships"), 1}, {TEXT("Invite players"), 2}, {TEXT("Promote and demote lower ranks"), 2},
        {TEXT("Remove lower ranks"), 2}, {TEXT("Edit the description and emblem"), 3}, {TEXT("Transfer leadership"), 3}};
    auto Row = [&](const FString& First, const FString (&Cells)[4], bool bHeader)
    {
        auto* Line = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Name = WidgetTree->ConstructWidget<UTextBlock>(); Name->SetText(FText::FromString(First)); { auto F = Name->GetFont(); F.Size = 13; Name->SetFont(F); }
        if (bHeader) Name->SetColorAndOpacity(FSlateColor(FLinearColor(.88f, .86f, .8f)));
        Line->AddChildToHorizontalBox(Name)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        for (int32 Rank = 0; Rank < 4; ++Rank)
        {
            auto* Cell = WidgetTree->ConstructWidget<UTextBlock>(); Cell->SetText(FText::FromString(Cells[Rank])); Cell->SetJustification(ETextJustify::Center); { auto F = Cell->GetFont(); F.Size = 13; Cell->SetFont(F); }
            Cell->SetColorAndOpacity(FSlateColor(Rank == Viewer ? Gold : (bHeader ? FLinearColor(.88f, .86f, .8f) : FLinearColor(.8f, .84f, .88f))));
            auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(96); Size->SetContent(Cell); Line->AddChildToHorizontalBox(Size);
        }
        RolesBox->AddChildToVerticalBox(Line)->SetPadding(FMargin(0, 0, 0, 3));
    };
    const FString Head[4] = {Ranks[0], Ranks[1], Ranks[2], Ranks[3]};
    Row(TEXT("What each rank may do (preview)"), Head, true);
    for (const FPermission& P : Permissions)
    {
        FString Cells[4];
        for (int32 Rank = 0; Rank < 4; ++Rank) Cells[Rank] = Rank >= P.MinRank ? TEXT("✔") : TEXT("—");
        Row(P.Name, Cells, false);
    }
}

void UEWCompanyWidget::SetSearch(const FString& Text)
{
    Filter = Text;
    RebuildList(); RefreshAll();
}

void UEWCompanyWidget::SelectMemberByName(const FString& Name)
{
    const int32 Index = IndexOfName(Name);
    if (Index != INDEX_NONE) MemberPressed(Index);
}

void UEWCompanyWidget::MemberPressed(int32 Index)
{
    if (!Members.IsValidIndex(Index)) return;
    Selected = Index;
    RefreshAll();
    const int32 Place = Shown.IndexOfByKey(Index);
    if (MemberScroll && MemberRings.IsValidIndex(Place)) MemberScroll->ScrollWidgetIntoView(MemberRings[Place], true);
}

void UEWCompanyWidget::SetSubTab(int32 Tab)
{
    SubTab = FMath::Clamp(Tab, 0, 2);
    if (LogPage) LogPage->SetVisibility(SubTab == 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (InvitePage) InvitePage->SetVisibility(SubTab == 1 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (RolesPage) RolesPage->SetVisibility(SubTab == 2 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    RefreshAll();
}

void UEWCompanyWidget::SetViewerRank(EEWSampleRank Rank)
{
    const int32 You = YouIndex();
    if (!Members.IsValidIndex(You)) return;
    if (Members[You].Rank == EEWSampleRank::Leader && Rank != EEWSampleRank::Leader)
    {
        // The leader who stepped aside takes the lead again; if they have since gone, the highest rank left does.
        int32 Heir = IndexOfName(DisplacedLeader);
        if (Heir == INDEX_NONE || Heir == You)
        {
            Heir = INDEX_NONE;
            for (int32 Index = 0; Index < Members.Num(); ++Index)
                if (Index != You && (Heir == INDEX_NONE || Members[Index].Rank > Members[Heir].Rank)) Heir = Index;
        }
        if (Heir != INDEX_NONE) Members[Heir].Rank = EEWSampleRank::Leader;
        DisplacedLeader.Reset();
    }
    else if (Rank == EEWSampleRank::Leader)
    {
        for (auto& M : Members) if (M.Rank == EEWSampleRank::Leader) { DisplacedLeader = M.Name; M.Rank = EEWSampleRank::Officer; }
    }
    Members[You].Rank = Rank;
}

void UEWCompanyWidget::CycleViewerRank()
{
    SetViewerRank(static_cast<EEWSampleRank>((GetViewerRank() + 1) % 4));
    RebuildList(); RefreshAll();
}

void UEWCompanyWidget::DoAction(int32 Action)
{
    if (!IsActionEnabled(Action) || Confirming != INDEX_NONE) return;
    ActionCursor = Action;
    FEWSampleMember* Target = Members.IsValidIndex(Selected) ? &Members[Selected] : nullptr;
    switch (Action)
    {
        case 0:
            Target->Rank = static_cast<EEWSampleRank>(static_cast<int32>(Target->Rank) + 1);
            AddLog(TEXT("▲"), FString::Printf(TEXT("You promoted %s to %s."), *Target->Name, *RankName(Target->Rank)));
            break;
        case 1:
            Target->Rank = static_cast<EEWSampleRank>(static_cast<int32>(Target->Rank) - 1);
            AddLog(TEXT("▼"), FString::Printf(TEXT("You demoted %s to %s."), *Target->Name, *RankName(Target->Rank)));
            break;
        case 2:
            SetSubTab(1);
            if (InviteBox) InviteBox->SetKeyboardFocus();
            return;
        case 3: case 4:
            Confirming = Action; DialogChoice = 0;
            DialogText->SetText(FText::FromString(Action == 3
                ? FString::Printf(TEXT("Remove %s from The Gilded Gull Company?\n\nPreview only: nothing is sent to a server."), *Target->Name)
                : FString::Printf(TEXT("Make %s the leader of The Gilded Gull Company? You would become an Officer.\n\nPreview only: nothing is sent to a server."), *Target->Name)));
            DialogLayer->SetVisibility(ESlateVisibility::Visible);
            break;
    }
    RebuildList(); RefreshAll();
}

void UEWCompanyWidget::ConfirmDialog(bool bConfirm)
{
    if (Confirming == INDEX_NONE) return;
    const int32 Action = Confirming;
    Confirming = INDEX_NONE; DialogChoice = 0;
    if (DialogLayer) DialogLayer->SetVisibility(ESlateVisibility::Collapsed);
    if (bConfirm && Members.IsValidIndex(Selected) && Selected != YouIndex())
    {
        const FString Name = Members[Selected].Name;
        if (Action == 3)
        {
            Members.RemoveAt(Selected);
            Selected = FMath::Clamp(Selected, 0, Members.Num() - 1);
            AddLog(TEXT("✖"), FString::Printf(TEXT("You removed %s from the company."), *Name));
        }
        else if (Action == 4)
        {
            Members[Selected].Rank = EEWSampleRank::Leader;
            Members[YouIndex()].Rank = EEWSampleRank::Officer;
            DisplacedLeader.Reset();
            AddLog(TEXT("★"), FString::Printf(TEXT("You transferred leadership to %s."), *Name));
        }
    }
    RebuildList(); RefreshAll();
}

void UEWCompanyWidget::SendSampleInvite(const FString& TypedName)
{
    if (!InviteStatus) return;
    if (!IsActionEnabled(2)) { InviteStatus->SetText(FText::FromString(TEXT("Only Officers and the Leader can send invitations."))); return; }
    static const TCHAR* Samples[] = {TEXT("Sable Quill"), TEXT("Orrin Hale"), TEXT("Lysa Brandt"), TEXT("Fenn Tolliver"), TEXT("Marguerite Dunn")};
    FString Name = TypedName.TrimStartAndEnd();
    if (Name.IsEmpty()) Name = Samples[InviteCounter++ % UE_ARRAY_COUNT(Samples)];
    if (IndexOfName(Name) != INDEX_NONE) { InviteStatus->SetText(FText::FromString(Name + TEXT(" is already in the company."))); return; }
    if (Invites.ContainsByPredicate([&Name](const FEWSampleInvite& I) { return !I.bIncoming && I.Name == Name; })) { InviteStatus->SetText(FText::FromString(Name + TEXT(" already has a pending invitation."))); return; }
    FEWSampleInvite Invite; Invite.Name = Name; Invite.Sent = TEXT("Sent just now"); Invites.Add(Invite);
    InviteStatus->SetText(FText::FromString(FString::Printf(TEXT("Sample invitation made for %s (preview: nothing was sent)."), *Name)));
    if (InviteBox) InviteBox->SetText(FText::GetEmpty());
    AddLog(TEXT("✉"), FString::Printf(TEXT("You invited %s."), *Name));
    RefreshInvites(); RefreshAll();
}

void UEWCompanyWidget::InviteButtonPressed(int32 Index)
{
    SendSampleInvite(InviteBox ? InviteBox->GetText().ToString() : FString());
}

void UEWCompanyWidget::InviteCommitted(const FText& Text, ETextCommit::Type Method)
{
    if (Method == ETextCommit::OnEnter) SendSampleInvite(Text.ToString());
}

void UEWCompanyWidget::InviteRowPressed(int32 Code)
{
    const int32 Index = Code % 100;
    if (!Invites.IsValidIndex(Index)) return;
    const FEWSampleInvite Invite = Invites[Index];
    Invites.RemoveAt(Index);
    if (Code < 100) AddLog(TEXT("✖"), FString::Printf(TEXT("You revoked the invitation to %s."), *Invite.Name));
    else if (Code < 200) AddLog(TEXT("✔"), FString::Printf(TEXT("Preview: accepting %s would take you out of this company. Nothing changed."), *Invite.Name));
    else AddLog(TEXT("✖"), FString::Printf(TEXT("You declined the invitation from %s."), *Invite.Name));
    RefreshInvites(); RefreshAll();
}

bool UEWCompanyWidget::HandleMenuKey(const FKey& Key)
{
    const bool bUp = Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up, bDown = Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down;
    const bool bLeft = Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left, bRight = Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right;
    const bool bAccept = Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom;
    const bool bBack = Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right;
    if (Confirming != INDEX_NONE)
    {
        if (bBack) ConfirmDialog(false);
        else if (bLeft || bRight) { DialogChoice = 1 - DialogChoice; RefreshAll(); }
        else if (bAccept) ConfirmDialog(DialogChoice == 1);
        return true;
    }
    if (bBack) return false;
    if (bUp || bDown)
    {
        if (Shown.IsEmpty()) return true;
        const int32 Place = Shown.IndexOfByKey(Selected);
        MemberPressed(Shown[FMath::Clamp((Place == INDEX_NONE ? 0 : Place + (bDown ? 1 : -1)), 0, Shown.Num() - 1)]);
        return true;
    }
    if (bLeft || bRight) { ActionCursor = (ActionCursor + ActionCount + (bRight ? 1 : -1)) % ActionCount; RefreshAll(); return true; }
    if (bAccept)
    {
        if (SubTab == 1 && ActionCursor == 2) SendSampleInvite(FString());
        else DoAction(ActionCursor);
        return true;
    }
    if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Left) { SetSubTab((SubTab + 1) % 3); return true; }
    return false;
}
