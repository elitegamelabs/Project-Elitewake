#include "EWCompanyWidget.h"
#include "EWCompanyComponent.h"
#include "EWInventoryWidget.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerState.h"
#include "InputCoreTypes.h"
#include "Misc/DateTime.h"

namespace
{
    const FLinearColor Gold(1.f, .85f, .35f, 1.f);
    const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
    const FLinearColor PanelColour(.03f, .036f, .042f, .78f);
    const FLinearColor RowColour(.07f, .085f, .1f, 1.f);
    const FLinearColor RowPicked(.2f, .24f, .29f, 1.f);
    const FLinearColor Muted(.6f, .66f, .72f);
    const FLinearColor OnlineGreen(.5f, .85f, .55f);
    const int32 ActionCount = 5;

    FLinearColor RankColour(EEWCompanyRank Rank)
    {
        switch (Rank)
        {
            case EEWCompanyRank::Leader: return Gold;
            case EEWCompanyRank::Officer: return FLinearColor(.55f, .78f, 1.f);
            default: return FLinearColor::White;
        }
    }
}

FString UEWCompanyWidget::RankName(EEWCompanyRank Rank)
{
    switch (Rank)
    {
        case EEWCompanyRank::Leader: return TEXT("Leader");
        case EEWCompanyRank::Officer: return TEXT("Officer");
        default: return TEXT("Member");
    }
}

FString UEWCompanyWidget::PolicyName(int32 Policy)
{
    switch (Policy)
    {
        case 1: return TEXT("Personal, shared: each ship stays her owner's, every member may sail her");
        case 2: return TEXT("Company: every member may sail every member's ship");
        default: return TEXT("Personal: only a ship's owner may sail her");
    }
}

UEWCompanyComponent* UEWCompanyWidget::GetCompany() const
{
    const auto* Player = Cast<AEWPlayerController>(GetOwningPlayer());
    return Player ? Player->GetCompanyComponent() : nullptr;
}

int32 UEWCompanyWidget::IndexOfName(const FString& Name) const
{
    return Members.IndexOfByPredicate([&Name](const FEWCompanyRow& M) { return M.Name == Name; });
}

const FEWCompanyRow* UEWCompanyWidget::You() const { return Members.FindByPredicate([](const FEWCompanyRow& M) { return M.bYou; }); }
const FEWCompanyRow* UEWCompanyWidget::SelectedMember() const { return Members.IsValidIndex(Selected) ? &Members[Selected] : nullptr; }
bool UEWCompanyWidget::IsInCompany() const { const auto* C = GetCompany(); return C && C->GetCompany().Id.IsValid(); }
FString UEWCompanyWidget::GetCompanyName() const { const auto* C = GetCompany(); return C ? C->GetCompany().Name : FString(); }
FString UEWCompanyWidget::GetIncomingInvitation() const { const auto* C = GetCompany(); return C ? C->GetInvitationName() : FString(); }
FString UEWCompanyWidget::GetStatusText() const { const auto* C = GetCompany(); return C ? C->GetLastResult() : FString(); }
int32 UEWCompanyWidget::GetShipPolicy() const { const auto* C = GetCompany(); return C ? static_cast<int32>(C->GetCompany().Ships) : 0; }
int32 UEWCompanyWidget::GetOnlineCount() const { int32 N = 0; for (const auto& M : Members) N += M.bOnline ? 1 : 0; return N; }
FText UEWCompanyWidget::GetSelectedName() const { const auto* M = SelectedMember(); return M ? FText::FromString(M->Name) : FText::GetEmpty(); }
FText UEWCompanyWidget::GetSelectedRankText() const { const auto* M = SelectedMember(); return M ? FText::FromString(RankName(M->Rank)) : FText::GetEmpty(); }
int32 UEWCompanyWidget::GetSelectedRank() const { const auto* M = SelectedMember(); return M ? static_cast<int32>(M->Rank) : -1; }
int32 UEWCompanyWidget::GetViewerRank() const { const auto* M = You(); return M ? static_cast<int32>(M->Rank) : -1; }
bool UEWCompanyWidget::IsTyping() const
{
    return (SearchBox && SearchBox->HasKeyboardFocus()) || (InviteBox && InviteBox->HasKeyboardFocus()) || (CreateBox && CreateBox->HasKeyboardFocus());
}

bool UEWCompanyWidget::IsPointerOverTextBox(const FVector2D& At) const
{
    for (const UEditableTextBox* Box : {SearchBox.Get(), InviteBox.Get(), CreateBox.Get()})
        if (Box && Box->IsVisible() && Box->GetCachedGeometry().IsUnderLocation(At)) return true;
    return false;
}

void UEWCompanyWidget::Send(uint8 Action, const FString& Text, int32 Target)
{
    if (UEWCompanyComponent* Company = GetCompany()) Company->ServerCommand(static_cast<EEWCompanyAction>(Action), Text, Target);
    SyncIn = .25f;
}

TSharedRef<SWidget> UEWCompanyWidget::RebuildWidget()
{
    if (!WidgetTree || WidgetTree->RootWidget) return Super::RebuildWidget();

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
    auto SizedButton = [&](UVerticalBox* Into, const FString& Label, float Width, UEWRecipeButton*& Out)
    {
        UBorder* Ring; Button(Label, 0, 14, Ring, Out);
        auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(Width); Size->SetContent(Ring);
        auto* Slot = Into->AddChildToVerticalBox(Size); Slot->SetHorizontalAlignment(HAlign_Left); Slot->SetPadding(FMargin(0, 0, 0, 8));
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

    // Centre: the company, or making one.
    auto* OverBorder = Panel(FMargin(18)); Column(OverBorder, 1.35f, FMargin(0, 0, 10, 10));
    auto* Over = WidgetTree->ConstructWidget<UVerticalBox>(); OverBorder->SetContent(Over);
    auto* Head = WidgetTree->ConstructWidget<UHorizontalBox>(); Over->AddChildToVerticalBox(Head)->SetPadding(FMargin(0, 0, 0, 12));
    auto* Emblem = WidgetTree->ConstructWidget<UBorder>(); Emblem->SetBrushColor(FLinearColor(.1f, .14f, .2f, 1.f)); Emblem->SetHorizontalAlignment(HAlign_Center); Emblem->SetVerticalAlignment(VAlign_Center);
    EmblemText = Text(nullptr, TEXT("?"), 52, Gold, 0, false); Emblem->SetContent(EmblemText);
    auto* EmblemSize = WidgetTree->ConstructWidget<USizeBox>(); EmblemSize->SetWidthOverride(96); EmblemSize->SetHeightOverride(96); EmblemSize->SetContent(Emblem);
    Head->AddChildToHorizontalBox(EmblemSize)->SetPadding(FMargin(0, 0, 16, 0));
    auto* HeadText = WidgetTree->ConstructWidget<UVerticalBox>(); Head->AddChildToHorizontalBox(HeadText)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CompanyTitle = Text(HeadText, TEXT(""), 27, FLinearColor::White, 2);
    CompanySubtitle = Text(HeadText, TEXT(""), 15, Gold, 6);

    auto* With = WidgetTree->ConstructWidget<UVerticalBox>(); InCompanyBox = With; Over->AddChildToVerticalBox(With);
    OverviewCounts = Text(With, TEXT(""), 16, FLinearColor::White, 4);
    OverviewLeader = Text(With, TEXT(""), 16, FLinearColor::White, 12);
    Text(With, TEXT("SHIPS"), 13, FLinearColor(.88f, .86f, .8f), 4, false);
    PolicyText = Text(With, TEXT(""), 15, FLinearColor(.85f, .87f, .9f), 6);
    {
        UEWRecipeButton* B; SizedButton(With, TEXT("Change who may sail"), 260, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::PolicyPressed); PolicyButton = B;
        SizedButton(With, TEXT("Leave the Company"), 260, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::LeavePressed);
    }

    auto* Without = WidgetTree->ConstructWidget<UVerticalBox>(); NoCompanyBox = Without; Over->AddChildToVerticalBox(Without);
    Text(Without, TEXT("Sail with friends: make a Company, invite the players here, and choose whether members may sail each other's ships."), 15, FLinearColor(.85f, .87f, .9f), 10);
    CreateBox = WidgetTree->ConstructWidget<UEditableTextBox>(); CreateBox->SetHintText(FText::FromString(TEXT("Company name (3 to 32 letters)"))); EWStyleSearchBox(CreateBox);
    CreateBox->OnTextCommitted.AddDynamic(this, &UEWCompanyWidget::CreateCommitted);
    Without->AddChildToVerticalBox(CreateBox)->SetPadding(FMargin(0, 0, 0, 6));
    {
        UEWRecipeButton* B; SizedButton(Without, TEXT("Create the Company"), 260, B);
        B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::CreatePressed);
    }
    NoCompanyInvite = Text(Without, TEXT(""), 15, FLinearColor(.75f, .85f, .95f), 6);
    StatusText = Text(Over, TEXT(""), 13, FLinearColor(.95f, .75f, .35f), 0);

    // Right: the picked member and what can be done with them.
    auto* DetailBorder = Panel(FMargin(16)); Column(DetailBorder, 1.1f, FMargin(0, 0, 0, 10));
    auto* Detail = WidgetTree->ConstructWidget<UVerticalBox>(); DetailBorder->SetContent(Detail);
    auto* DetailTop = WidgetTree->ConstructWidget<UHorizontalBox>(); Detail->AddChildToVerticalBox(DetailTop)->SetPadding(FMargin(0, 0, 0, 10));
    auto* Portrait = WidgetTree->ConstructWidget<UBorder>(); Portrait->SetBrushColor(FLinearColor(.015f, .02f, .026f, .95f)); Portrait->SetHorizontalAlignment(HAlign_Center); Portrait->SetVerticalAlignment(VAlign_Center);
    DetailGlyph = Text(nullptr, TEXT("?"), 38, Muted, 0, false); Portrait->SetContent(DetailGlyph);
    auto* PortraitSize = WidgetTree->ConstructWidget<USizeBox>(); PortraitSize->SetWidthOverride(84); PortraitSize->SetHeightOverride(84); PortraitSize->SetContent(Portrait);
    DetailTop->AddChildToHorizontalBox(PortraitSize)->SetPadding(FMargin(0, 0, 14, 0));
    auto* DetailHead = WidgetTree->ConstructWidget<UVerticalBox>(); DetailTop->AddChildToHorizontalBox(DetailHead)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    DetailName = Text(DetailHead, TEXT(""), 21, FLinearColor::White, 2);
    DetailRank = Text(DetailHead, TEXT(""), 16, Gold, 2);
    DetailStatus = Text(DetailHead, TEXT(""), 14, OnlineGreen, 0);
    DetailInfo = Text(Detail, TEXT(""), 14, FLinearColor(.85f, .87f, .9f), 12);
    Text(Detail, TEXT("ACTIONS"), 13, FLinearColor(.88f, .86f, .8f), 6, false);
    const TCHAR* ActionLabels[] = {TEXT("Promote to Officer"), TEXT("Demote to Member"), TEXT("Invite a player"), TEXT("Remove from company"), TEXT("Transfer leadership")};
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
    InviteBox = WidgetTree->ConstructWidget<UEditableTextBox>(); InviteBox->SetHintText(FText::FromString(TEXT("Name of a player here"))); EWStyleSearchBox(InviteBox);
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

    Sync(true);
    SetSubTab(0);
    return Super::RebuildWidget();
}

void UEWCompanyWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if ((SyncIn -= InDeltaTime) <= 0.f) { SyncIn = .5f; Sync(); }  // tuning
}

void UEWCompanyWidget::Sync(bool bForce)
{
    const UEWCompanyComponent* Company = GetCompany();
    const FEWCompanySnapshot Snapshot = Company ? Company->GetCompany() : FEWCompanySnapshot();
    const APlayerController* Player = GetOwningPlayer();
    const int32 YouId = Player && Player->PlayerState ? Player->PlayerState->GetPlayerId() : INDEX_NONE;

    // The server's answer to the last request, once.
    const FString Answer = Company ? Company->GetLastResult() : FString();
    if (!Answer.IsEmpty() && Answer != LastAnswer) AddLog(TEXT("•"), Answer);
    LastAnswer = Answer;

    FString NewSignature = Snapshot.Id.ToString() + Snapshot.Name + FString::FromInt(Snapshot.OwnerId) + FString::FromInt(static_cast<int32>(Snapshot.Ships))
        + (Company ? Company->GetInvitationName() : FString()) + Answer;
    for (const FEWCompanyMember& M : Snapshot.Members) NewSignature += FString::Printf(TEXT("|%d%s%d%d"), M.PlayerId, *M.Name, M.bManager, M.bOnline);
    if (Company) for (const FEWCompanyMember& M : Company->GetOnlinePlayers()) NewSignature += FString::Printf(TEXT("/%d%s"), M.PlayerId, *M.Name);
    if (!bForce && NewSignature == Signature) return;
    Signature = NewSignature;

    // Who joined and who left, while this screen has been watching.
    if (!bForce)
    {
        for (const FEWCompanyMember& M : Snapshot.Members)
            if (M.PlayerId != YouId && !Members.ContainsByPredicate([&M](const FEWCompanyRow& R) { return R.PlayerId == M.PlayerId; }) && Members.Num())
                AddLog(TEXT("+"), FString::Printf(TEXT("%s joined the company."), *M.Name));
        for (const FEWCompanyRow& R : Members)
            if (!Snapshot.Members.ContainsByPredicate([&R](const FEWCompanyMember& M) { return M.PlayerId == R.PlayerId; }) && !R.bYou)
                AddLog(TEXT("✖"), FString::Printf(TEXT("%s left the company."), *R.Name));
    }

    const FString PickedName = SelectedMember() ? SelectedMember()->Name : FString();
    Members.Reset();
    for (const FEWCompanyMember& M : Snapshot.Members)
    {
        FEWCompanyRow Row; Row.Name = M.Name; Row.PlayerId = M.PlayerId; Row.bOnline = M.bOnline; Row.bYou = M.PlayerId == YouId;
        Row.Rank = M.PlayerId == Snapshot.OwnerId ? EEWCompanyRank::Leader : M.bManager ? EEWCompanyRank::Officer : EEWCompanyRank::Member;
        Members.Add(Row);
    }
    Members.StableSort([](const FEWCompanyRow& A, const FEWCompanyRow& B) { return A.Rank > B.Rank; });
    OnlineNames.Reset(); OnlineIds.Reset();
    if (Company)
        for (const FEWCompanyMember& M : Company->GetOnlinePlayers())
            if (!Snapshot.Members.ContainsByPredicate([&M](const FEWCompanyMember& C) { return C.PlayerId == M.PlayerId; }))
            { OnlineNames.Add(M.Name); OnlineIds.Add(M.PlayerId); }
    Selected = FMath::Max(0, IndexOfName(PickedName));
    if (PickedName.IsEmpty()) { const int32 Other = Members.IndexOfByPredicate([](const FEWCompanyRow& R) { return !R.bYou; }); Selected = Other == INDEX_NONE ? 0 : Other; }

    const bool bIn = Snapshot.Id.IsValid();
    if (InCompanyBox) InCompanyBox->SetVisibility(bIn ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (NoCompanyBox) NoCompanyBox->SetVisibility(bIn ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (EmblemText) EmblemText->SetText(FText::FromString(bIn ? Snapshot.Name.Left(1).ToUpper() : TEXT("?")));
    if (CompanyTitle) CompanyTitle->SetText(FText::FromString(bIn ? Snapshot.Name : TEXT("No Company")));
    if (CompanySubtitle) CompanySubtitle->SetText(FText::FromString(bIn ? (You() ? FString::Printf(TEXT("COMPANY  ·  you are %s"), *RankName(You()->Rank)) : TEXT("COMPANY"))
        : TEXT("You sail alone")));
    if (PolicyText) PolicyText->SetText(FText::FromString(PolicyName(static_cast<int32>(Snapshot.Ships))));
    if (NoCompanyInvite)
    {
        const FString Invitation = Company ? Company->GetInvitationName() : FString();
        NoCompanyInvite->SetText(FText::FromString(Invitation.IsEmpty() ? FString()
            : FString::Printf(TEXT("%s has invited you. Accept it under Invitations below."), *Invitation)));
    }
    if (StatusText) StatusText->SetText(FText::FromString(Answer));
    RebuildList(); RefreshInvites(); RefreshRoles(); RefreshAll();
}

bool UEWCompanyWidget::IsActionEnabled(int32 Action) const
{
    const FEWCompanyRow* Viewer = You();
    if (!Viewer) return false;
    const bool bLeader = Viewer->Rank == EEWCompanyRank::Leader;
    const bool bOfficer = Viewer->Rank >= EEWCompanyRank::Officer;
    if (Action == 2) return bOfficer;
    if (Action == 5) return !bLeader || Members.Num() == 1;
    const FEWCompanyRow* Target = SelectedMember();
    if (!Target || Target->bYou) return false;
    // The server's rules (AEWCompanyRegistry::Command).
    switch (Action)
    {
        case 0: return bLeader && Target->Rank == EEWCompanyRank::Member;
        case 1: return bLeader && Target->Rank == EEWCompanyRank::Officer;
        case 3: return Target->Rank != EEWCompanyRank::Leader && (bLeader || (bOfficer && Target->Rank == EEWCompanyRank::Member));
        case 4: return bLeader && Target->bOnline;
        default: return false;
    }
}

void UEWCompanyWidget::AddLog(const FString& Glyph, const FString& Text)
{
    FEWCompanyLogLine L; L.Time = FDateTime::Now().ToString(TEXT("%H:%M")); L.Glyph = Glyph; L.Text = Text;
    Log.Insert(L, 0);
    if (Log.Num() > 60) Log.SetNum(60);
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
        const FEWCompanyRow& M = Members[Index];
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
        auto* NameText = WidgetTree->ConstructWidget<UTextBlock>(); NameText->SetText(FText::FromString(M.bYou ? M.Name + TEXT(" (you)") : M.Name)); { auto F = NameText->GetFont(); F.Size = 15; NameText->SetFont(F); }
        Words->AddChildToVerticalBox(NameText);
        auto* Sub = WidgetTree->ConstructWidget<UTextBlock>(); Sub->SetText(FText::FromString(FString::Printf(TEXT("%s  ·  %s"), *RankName(M.Rank), M.bOnline ? TEXT("Online") : TEXT("Offline"))));
        Sub->SetColorAndOpacity(FSlateColor(M.bOnline ? OnlineGreen : Muted)); { auto F = Sub->GetFont(); F.Size = 12; Sub->SetFont(F); }
        Words->AddChildToVerticalBox(Sub);
        if (M.Rank == EEWCompanyRank::Leader)
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
        auto* None = WidgetTree->ConstructWidget<UTextBlock>(); None->SetAutoWrapText(true); None->SetColorAndOpacity(FSlateColor(Muted));
        None->SetText(FText::FromString(Members.IsEmpty() ? TEXT("You are not in a Company yet.") : TEXT("No member matches that search.")));
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
    if (const FEWCompanyRow* M = SelectedMember(); M && DetailName)
    {
        DetailName->SetText(FText::FromString(M->Name)); DetailRank->SetText(FText::FromString(RankName(M->Rank))); DetailRank->SetColorAndOpacity(FSlateColor(RankColour(M->Rank)));
        DetailStatus->SetText(FText::FromString(M->bOnline ? TEXT("● Online") : TEXT("○ Offline")));
        DetailStatus->SetColorAndOpacity(FSlateColor(M->bOnline ? OnlineGreen : Muted));
        DetailInfo->SetText(FText::FromString(M->bYou ? TEXT("That is you.") : M->Rank == EEWCompanyRank::Leader ? TEXT("Leads the company and sets who may sail its ships.")
            : M->Rank == EEWCompanyRank::Officer ? TEXT("An officer: invites players and removes members.") : TEXT("A member of the company.")));
        DetailGlyph->SetText(FText::FromString(M->Name.Left(1)));
    }
    else if (DetailName)
    {
        DetailName->SetText(FText::FromString(TEXT("No member picked"))); DetailRank->SetText(FText::GetEmpty()); DetailStatus->SetText(FText::GetEmpty());
        DetailInfo->SetText(FText::GetEmpty()); DetailGlyph->SetText(FText::FromString(TEXT("?")));
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
        const auto* Leader = Members.FindByPredicate([](const FEWCompanyRow& Candidate) { return Candidate.Rank == EEWCompanyRank::Leader; });
        OverviewLeader->SetText(FText::FromString(FString::Printf(TEXT("Leader  ★ %s"), Leader ? *Leader->Name : TEXT("none"))));
    }
    const bool bLeader = GetViewerRank() == static_cast<int32>(EEWCompanyRank::Leader);
    if (PolicyButton) { PolicyButton->SetIsEnabled(bLeader); PolicyButton->SetRenderOpacity(bLeader ? 1.f : .4f); }
    for (int32 Tab = 0; Tab < TabRings.Num(); ++Tab) TabRings[Tab]->SetBrushColor(Tab == SubTab ? Gold : Clear);
    for (int32 Choice = 0; Choice < DialogRings.Num(); ++Choice) DialogRings[Choice]->SetBrushColor(Choice == DialogChoice ? Gold : Clear);
}

void UEWCompanyWidget::RefreshLog()
{
    if (!LogBox) return;
    LogBox->ClearChildren();
    if (Log.IsEmpty())
    {
        auto* None = WidgetTree->ConstructWidget<UTextBlock>(); None->SetText(FText::FromString(TEXT("Nothing has happened this session yet."))); None->SetColorAndOpacity(FSlateColor(Muted));
        LogBox->AddChildToVerticalBox(None); return;
    }
    for (const FEWCompanyLogLine& L : Log)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Time = WidgetTree->ConstructWidget<UTextBlock>(); Time->SetText(FText::FromString(L.Time)); Time->SetColorAndOpacity(FSlateColor(Muted)); { auto F = Time->GetFont(); F.Size = 13; Time->SetFont(F); }
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
    auto AddRow = [this](const FString& Words, TArray<TPair<FString, int32>> Buttons)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Words)); { auto F = Label->GetFont(); F.Size = 14; Label->SetFont(F); }
        Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        for (const auto& [Text, Code] : Buttons)
        {
            auto* B = WidgetTree->ConstructWidget<UEWRecipeButton>(); B->Initialize(Code); B->SetBackgroundColor(RowColour);
            B->OnRecipePressed.AddDynamic(this, &UEWCompanyWidget::InviteRowPressed);
            auto* T = WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Text)); T->SetJustification(ETextJustify::Center); { auto F = T->GetFont(); F.Size = 13; T->SetFont(F); } B->SetContent(T);
            auto* S = WidgetTree->ConstructWidget<USizeBox>(); S->SetWidthOverride(96); S->SetContent(B);
            Row->AddChildToHorizontalBox(S)->SetPadding(FMargin(6, 0, 0, 0));
        }
        InviteListBox->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 5));
    };
    const FString Invitation = GetIncomingInvitation();
    if (!Invitation.IsEmpty())
        AddRow(FString::Printf(TEXT("Incoming: %s invited you%s"), *Invitation, IsInCompany() ? TEXT(" (leave your Company first)") : TEXT("")),
            {{TEXT("Accept"), 100}, {TEXT("Decline"), 200}});
    const bool bCanInvite = IsActionEnabled(2);
    for (int32 Index = 0; Index < OnlineNames.Num(); ++Index)
        AddRow(FString::Printf(TEXT("Here now: %s"), *OnlineNames[Index]), bCanInvite ? TArray<TPair<FString, int32>>{{TEXT("Invite"), 300 + Index}} : TArray<TPair<FString, int32>>{});
    if (Invitation.IsEmpty() && OnlineNames.IsEmpty())
    {
        auto* None = WidgetTree->ConstructWidget<UTextBlock>(); None->SetAutoWrapText(true); None->SetColorAndOpacity(FSlateColor(Muted));
        None->SetText(FText::FromString(TEXT("No invitations, and no other players here to invite. Friends join with F10, Join Game.")));
        InviteListBox->AddChildToVerticalBox(None);
    }
    if (InviteStatus && !IsInCompany()) InviteStatus->SetText(FText::FromString(TEXT("Create a Company above to invite players.")));
    else if (InviteStatus && !bCanInvite) InviteStatus->SetText(FText::FromString(TEXT("Only Officers and the Leader can send invitations.")));
    else if (InviteStatus) InviteStatus->SetText(FText::GetEmpty());
}

void UEWCompanyWidget::RefreshRoles()
{
    if (!RolesBox) return;
    RolesBox->ClearChildren();
    const int32 Viewer = GetViewerRank();
    const TCHAR* Ranks[] = {TEXT("Member"), TEXT("Officer"), TEXT("Leader")};
    struct FPermission { const TCHAR* Name; int32 MinRank; };
    const FPermission Permissions[] = {
        {TEXT("Sail members' ships (when the ship policy shares them)"), 0}, {TEXT("Leave the company"), 0}, {TEXT("Invite players"), 1},
        {TEXT("Remove members"), 1}, {TEXT("Promote and demote officers"), 2}, {TEXT("Remove officers"), 2}, {TEXT("Choose who may sail the ships"), 2},
        {TEXT("Transfer leadership"), 2}};
    auto Row = [&](const FString& First, const FString (&Cells)[3], bool bHeader)
    {
        auto* Line = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Name = WidgetTree->ConstructWidget<UTextBlock>(); Name->SetText(FText::FromString(First)); { auto F = Name->GetFont(); F.Size = 13; Name->SetFont(F); }
        if (bHeader) Name->SetColorAndOpacity(FSlateColor(FLinearColor(.88f, .86f, .8f)));
        Line->AddChildToHorizontalBox(Name)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        for (int32 Rank = 0; Rank < 3; ++Rank)
        {
            auto* Cell = WidgetTree->ConstructWidget<UTextBlock>(); Cell->SetText(FText::FromString(Cells[Rank])); Cell->SetJustification(ETextJustify::Center); { auto F = Cell->GetFont(); F.Size = 13; Cell->SetFont(F); }
            Cell->SetColorAndOpacity(FSlateColor(Rank == Viewer ? Gold : (bHeader ? FLinearColor(.88f, .86f, .8f) : FLinearColor(.8f, .84f, .88f))));
            auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(96); Size->SetContent(Cell); Line->AddChildToHorizontalBox(Size);
        }
        RolesBox->AddChildToVerticalBox(Line)->SetPadding(FMargin(0, 0, 0, 3));
    };
    const FString Head[3] = {Ranks[0], Ranks[1], Ranks[2]};
    Row(TEXT("What each rank may do"), Head, true);
    for (const FPermission& P : Permissions)
    {
        FString Cells[3];
        for (int32 Rank = 0; Rank < 3; ++Rank) Cells[Rank] = Rank >= P.MinRank ? TEXT("✔") : TEXT("—");
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

void UEWCompanyWidget::DoAction(int32 Action)
{
    if (!IsActionEnabled(Action) || Confirming != INDEX_NONE) return;
    if (Action < ActionCount) ActionCursor = Action;
    const FEWCompanyRow* Target = SelectedMember();
    const FString Company = GetCompanyName();
    switch (Action)
    {
        case 0: Send(static_cast<uint8>(EEWCompanyAction::Promote), FString(), Target->PlayerId); break;
        case 1: Send(static_cast<uint8>(EEWCompanyAction::Demote), FString(), Target->PlayerId); break;
        case 2:
            SetSubTab(1);
            if (InviteBox) InviteBox->SetKeyboardFocus();
            return;
        case 3: case 4: case 5:
            Confirming = Action; DialogChoice = 0; PendingTarget = Action == 5 ? INDEX_NONE : Target->PlayerId;
            DialogText->SetText(FText::FromString(Action == 3 ? FString::Printf(TEXT("Remove %s from %s?"), *Target->Name, *Company)
                : Action == 4 ? FString::Printf(TEXT("Make %s the leader of %s? You would become a Member."), *Target->Name, *Company)
                : FString::Printf(TEXT("Leave %s? Members' ships it shared with you are no longer yours to sail."), *Company)));
            DialogLayer->SetVisibility(ESlateVisibility::Visible);
            break;
    }
    RefreshAll();
}

void UEWCompanyWidget::ConfirmDialog(bool bConfirm)
{
    if (Confirming == INDEX_NONE) return;
    const int32 Action = Confirming;
    Confirming = INDEX_NONE; DialogChoice = 0;
    if (DialogLayer) DialogLayer->SetVisibility(ESlateVisibility::Collapsed);
    if (bConfirm)
    {
        if (Action == 3) Send(static_cast<uint8>(EEWCompanyAction::Remove), FString(), PendingTarget);
        else if (Action == 4) Send(static_cast<uint8>(EEWCompanyAction::TransferOwner), FString(), PendingTarget);
        else if (Action == 5) Send(static_cast<uint8>(EEWCompanyAction::Leave), FString(), INDEX_NONE);
    }
    PendingTarget = INDEX_NONE;
    RefreshAll();
}

void UEWCompanyWidget::CreateCompany(const FString& Name)
{
    const FString Trimmed = Name.TrimStartAndEnd();
    if (!UEWCompanyComponent::IsValidCompanyName(Trimmed))
    {
        if (StatusText) StatusText->SetText(FText::FromString(TEXT("Choose a name of 3 to 32 letters, numbers, spaces, apostrophes or hyphens.")));
        return;
    }
    Send(static_cast<uint8>(EEWCompanyAction::Create), Trimmed, INDEX_NONE);
    if (CreateBox) CreateBox->SetText(FText::GetEmpty());
}

void UEWCompanyWidget::InvitePlayer(const FString& Name)
{
    if (!InviteStatus) return;
    if (!IsActionEnabled(2)) { InviteStatus->SetText(FText::FromString(IsInCompany() ? TEXT("Only Officers and the Leader can send invitations.") : TEXT("Create a Company above to invite players."))); return; }
    const FString Wanted = Name.TrimStartAndEnd();
    const int32 Index = OnlineNames.IndexOfByPredicate([&Wanted](const FString& N) { return N.Equals(Wanted, ESearchCase::IgnoreCase); });
    if (Wanted.IsEmpty() || Index == INDEX_NONE)
    {
        InviteStatus->SetText(FText::FromString(Wanted.IsEmpty() ? TEXT("Type the name of a player here, or press Invite beside them.")
            : IndexOfName(Wanted) != INDEX_NONE ? Wanted + TEXT(" is already in the company.") : TEXT("No player of that name is here (outside a Company).")));
        return;
    }
    Send(static_cast<uint8>(EEWCompanyAction::Invite), FString(), OnlineIds[Index]);
    InviteStatus->SetText(FText::FromString(FString::Printf(TEXT("Invitation sent to %s."), *OnlineNames[Index])));
    AddLog(TEXT("✉"), FString::Printf(TEXT("You invited %s."), *OnlineNames[Index]));
    if (InviteBox) InviteBox->SetText(FText::GetEmpty());
}

void UEWCompanyWidget::AnswerInvitation(bool bAccept)
{
    if (GetIncomingInvitation().IsEmpty()) return;
    Send(static_cast<uint8>(bAccept ? EEWCompanyAction::AcceptInvite : EEWCompanyAction::DeclineInvite), FString(), INDEX_NONE);
}

void UEWCompanyWidget::CycleShipPolicy()
{
    if (GetViewerRank() != static_cast<int32>(EEWCompanyRank::Leader)) return;
    if (UEWCompanyComponent* Company = GetCompany())
        Company->ServerSetPolicy(0, static_cast<EEWCompanyOwnership>((GetShipPolicy() + 1) % 3));
    SyncIn = .25f;
}

void UEWCompanyWidget::InviteButtonPressed(int32 Index) { InvitePlayer(InviteBox ? InviteBox->GetText().ToString() : FString()); }
void UEWCompanyWidget::InviteCommitted(const FText& Text, ETextCommit::Type Method) { if (Method == ETextCommit::OnEnter) InvitePlayer(Text.ToString()); }
void UEWCompanyWidget::CreatePressed(int32 Index) { CreateCompany(CreateBox ? CreateBox->GetText().ToString() : FString()); }
void UEWCompanyWidget::CreateCommitted(const FText& Text, ETextCommit::Type Method) { if (Method == ETextCommit::OnEnter) CreateCompany(Text.ToString()); }

void UEWCompanyWidget::InviteRowPressed(int32 Code)
{
    if (Code == 100 || Code == 200) AnswerInvitation(Code == 100);
    else if (OnlineNames.IsValidIndex(Code - 300)) InvitePlayer(OnlineNames[Code - 300]);
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
        // On the Invitations page Enter answers an invitation first; otherwise it does the picked action.
        if (SubTab == 1 && !GetIncomingInvitation().IsEmpty()) AnswerInvitation(true);
        else if (SubTab == 1 && OnlineNames.Num() && IsActionEnabled(2)) InvitePlayer(OnlineNames[0]);
        else DoAction(ActionCursor);
        return true;
    }
    if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Left) { SetSubTab((SubTab + 1) % 3); return true; }
    return false;
}
