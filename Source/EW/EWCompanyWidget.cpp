#include "EWCompanyWidget.h"
#include "EWCompanyComponent.h"
#include "EWPlayerController.h"
#include "EWInventoryWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/VerticalBox.h"
#include "Components/HorizontalBox.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/EditableTextBox.h"
#include "Components/WrapBox.h"
#include "Components/WrapBoxSlot.h"
#include "Components/Border.h"

namespace
{
UEWCompanyComponent* Company(UUserWidget* W) { auto* P=Cast<AEWPlayerController>(W->GetOwningPlayer()); return P?P->GetCompanyComponent():nullptr; }
FString Policy(EEWCompanyOwnership P)
{
    return P==EEWCompanyOwnership::Personal?TEXT("Personal"):P==EEWCompanyOwnership::PersonalShared?TEXT("Personal / shared access"):TEXT("Company owned");
}
}
TSharedRef<SWidget> UEWCompanyWidget::RebuildWidget()
{
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
    auto* Backdrop=WidgetTree->ConstructWidget<UBorder>(); Backdrop->SetPadding(FMargin(16));
    Backdrop->SetBrushColor(FLinearColor(.025f,.035f,.045f,.94f)); WidgetTree->RootWidget=Backdrop;
    auto* Scroll=WidgetTree->ConstructWidget<UScrollBox>(); Backdrop->SetContent(Scroll);
    auto* Body=WidgetTree->ConstructWidget<UVerticalBox>(); Scroll->AddChild(Body);
    auto Text=[&](const FString& Value) { auto* T=WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Value)); T->SetAutoWrapText(true); auto Font=T->GetFont(); Font.Size=16; T->SetFont(Font); T->SetColorAndOpacity(FSlateColor(FLinearColor(.85f,.87f,.9f))); Body->AddChildToVerticalBox(T); return T; };
    Text(TEXT("COMPANY"));
    Text(TEXT("Session prototype • membership and leadership are live. Asset transfer and saving are pending."));
    Roster=Text(TEXT("No Company"));
    NameInput=WidgetTree->ConstructWidget<UEditableTextBox>(); NameInput->SetHintText(FText::FromString(TEXT("Company name"))); Body->AddChildToVerticalBox(NameInput);
    auto* Actions=WidgetTree->ConstructWidget<UWrapBox>(); Actions->SetInnerSlotPadding(FVector2D(8,8)); Body->AddChildToVerticalBox(Actions);
    const TCHAR* Labels[]={TEXT("Create"),TEXT("Rename"),TEXT("Invite selected player"),TEXT("Accept invitation"),TEXT("Decline invitation"),TEXT("Promote manager"),TEXT("Demote manager"),TEXT("Remove member"),TEXT("Transfer leadership"),TEXT("Leave Company"),TEXT("Cycle ship policy"),TEXT("Cycle structure policy"),TEXT("Cycle tame policy")};
    for (int32 I=0;I<13;++I)
    {
        auto* B=WidgetTree->ConstructWidget<UEWRecipeButton>(); B->Initialize(I); B->OnRecipePressed.AddDynamic(this,&UEWCompanyWidget::Action);
        B->SetBackgroundColor(FLinearColor(.09f,.12f,.15f));
        auto* T=WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Labels[I])); auto Font=T->GetFont(); Font.Size=16; T->SetFont(Font); B->SetContent(T); Actions->AddChildToWrapBox(B);
    }
    TargetLabel=Text(TEXT("Select a player below to invite or manage."));
    People=WidgetTree->ConstructWidget<UVerticalBox>(); Body->AddChildToVerticalBox(People);
    Policies=Text(TEXT("")); Result=Text(TEXT("")); Refresh();
    return Super::RebuildWidget();
}
void UEWCompanyWidget::NativeTick(const FGeometry& G,float Delta)
{
    Super::NativeTick(G,Delta); RefreshRemaining-=Delta;
    if (RefreshRemaining<=0) { RefreshRemaining=.5f; Refresh(); }
}
void UEWCompanyWidget::Refresh()
{
    auto* C=Company(this); if (!C || !Roster) return;
    const auto Co=C->GetCompany();
    FString Text=Co.Id.IsValid()?Co.Name:TEXT("No Company. Create one or accept an invitation.");
    for (const auto& M:Co.Members) Text+=FString::Printf(TEXT("\n%s  •  %s  •  %s"),*M.Name,M.PlayerId==Co.OwnerId?TEXT("Owner"):M.bManager?TEXT("Manager"):TEXT("Member"),M.bOnline?TEXT("Online"):TEXT("Offline"));
    if (!C->GetInvitationName().IsEmpty()) Text+=TEXT("\nInvitation: ")+C->GetInvitationName();
    Roster->SetText(FText::FromString(Text)); Result->SetText(FText::FromString(C->GetLastResult()));
    Policies->SetText(FText::FromString(Co.Id.IsValid()?TEXT("Ships: ")+Policy(Co.Ships)+TEXT("\nStructures: ")+Policy(Co.Structures)+TEXT("\nTames: ")+Policy(Co.Tames)+TEXT("\nLimits: 25 per player / 75 total per Company, including personal tames.\nPolicies do not yet transfer or control world assets."):FString()));
    auto Candidates=C->GetOnlinePlayers();
    for (const auto& M:Co.Members) if (!Candidates.ContainsByPredicate([&M](const auto& P){return P.PlayerId==M.PlayerId;})) Candidates.Add(M);
    FString Signature;
    for (const auto& M:Candidates) Signature+=FString::FromInt(M.PlayerId)+M.Name+TEXT(";");
    if (Signature!=PeopleSignature)
    {
        PeopleSignature=Signature; People->ClearChildren(); Targets.Reset();
        for (const auto& M:Candidates)
        {
            const int32 Index=Targets.Add(M.PlayerId);
            auto* B=WidgetTree->ConstructWidget<UEWRecipeButton>(); B->Initialize(100+Index); B->OnRecipePressed.AddDynamic(this,&UEWCompanyWidget::Action);
            B->SetBackgroundColor(FLinearColor(.09f,.12f,.15f));
            auto* T=WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(M.Name)); auto Font=T->GetFont(); Font.Size=16; T->SetFont(Font); B->SetContent(T); People->AddChildToVerticalBox(B);
        }
    }
    const auto* Selected=Candidates.FindByPredicate([this](const auto& M){return M.PlayerId==SelectedTarget;});
    TargetLabel->SetText(FText::FromString(Selected?TEXT("Selected: ")+Selected->Name:TEXT("Select a player below to invite or manage.")));
}
void UEWCompanyWidget::Action(int32 Index)
{
    auto* C=Company(this); if (!C) return;
    if (Index>=100) { if (Targets.IsValidIndex(Index-100)) SelectedTarget=Targets[Index-100]; Refresh(); return; }
    if (Index>=10 && Index<13)
    {
        const auto Co=C->GetCompany(); const auto Current=Index==10?Co.Ships:Index==11?Co.Structures:Co.Tames;
        C->ServerSetPolicy(Index-10,static_cast<EEWCompanyOwnership>((static_cast<uint8>(Current)+1)%3)); return;
    }
    if (Index>=0 && Index<10) C->ServerCommand(static_cast<EEWCompanyAction>(Index),NameInput->GetText().ToString(),SelectedTarget);
}
