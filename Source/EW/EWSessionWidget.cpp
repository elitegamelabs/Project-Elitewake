#include "EWSessionWidget.h"
#include "EWGameInstance.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/SizeBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/EditableTextBox.h"
#include "Components/Button.h"
#include "Engine/World.h"
#include "InputCoreTypes.h"

TSharedRef<SWidget> UEWSessionWidget::RebuildWidget()
{
    SetIsFocusable(true);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Root=WidgetTree->ConstructWidget<UBorder>(); Root->SetBrushColor(FLinearColor(.015f,.025f,.035f,.96f));
        Root->SetHorizontalAlignment(HAlign_Center); Root->SetVerticalAlignment(VAlign_Center); Root->SetPadding(FMargin(24)); WidgetTree->RootWidget=Root;
        auto* Width=WidgetTree->ConstructWidget<USizeBox>(); Width->SetWidthOverride(620); Root->SetContent(Width);
        auto* Body=WidgetTree->ConstructWidget<UVerticalBox>(); Width->SetContent(Body);
        auto Text=[&](const FText& Value,int32 Size)
        {
            auto* Label=WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(Value); Label->SetAutoWrapText(true);
            auto Font=Label->GetFont(); Font.Size=Size; Label->SetFont(Font); Body->AddChildToVerticalBox(Label)->SetPadding(FMargin(0,0,0,8)); return Label;
        };
        Text(NSLOCTEXT("Elitewake","SessionTitle","PRIVATE TEST CONNECTION"),26);
        if (auto* Instance = GetGameInstance<UEWGameInstance>())
        {
            Text(FText::Format(NSLOCTEXT("Elitewake", "SessionBuildLabel", "Build: {0}"), Instance->GetPrivateBuildLabel()), 16);
        }
        Text(NSLOCTEXT("Elitewake","SessionAddressHelp","Same PC: 127.0.0.1:7777. LAN: the host PC's private IPv4 address. Internet: the host's public IP (or host name) with port 7777; the host forwards UDP port 7777 on their router to their PC and allows EW through Windows Firewall."),16);
        Address=WidgetTree->ConstructWidget<UEditableTextBox>(); Address->SetText(FText::FromString(TEXT("127.0.0.1:7777"))); Body->AddChildToVerticalBox(Address);
        Status=Text(FText::GetEmpty(),18);
        auto Button=[&](const FText& Value)
        {
            auto* Control=WidgetTree->ConstructWidget<UButton>(); Control->SetBackgroundColor(FLinearColor(.04f,.16f,.2f));
            auto* Label=WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(Value); Label->SetAutoWrapText(true); auto Font=Label->GetFont(); Font.Size=20; Label->SetFont(Font); Control->SetContent(Label); Body->AddChildToVerticalBox(Control)->SetPadding(FMargin(0,4)); return Control;
        };
        HostButton=Button(NSLOCTEXT("Elitewake","SessionHostButton","Host Game")); HostButton->OnClicked.AddDynamic(this,&UEWSessionWidget::Host);
        JoinButton=Button(NSLOCTEXT("Elitewake","SessionJoinButton","Join Game")); JoinButton->OnClicked.AddDynamic(this,&UEWSessionWidget::Join);
        LeaveButton=Button(NSLOCTEXT("Elitewake","SessionLeaveButton","Leave / Cancel (host departure disconnects players)")); LeaveButton->OnClicked.AddDynamic(this,&UEWSessionWidget::Leave);
        auto* CloseButton=Button(NSLOCTEXT("Elitewake","SessionCloseButton","Return to game (F10 / Escape)")); CloseButton->OnClicked.AddDynamic(this,&UEWSessionWidget::Close);
        Text(NSLOCTEXT("Elitewake","SessionProgressNotice","Host, Join and Leave reload the map. Current session progress is not saved. Opening this panel does not pause the world."),16);
    }
    return Super::RebuildWidget();
}
void UEWSessionWidget::NativeTick(const FGeometry& Geometry,float Delta)
{
    Super::NativeTick(Geometry,Delta);
    auto* Instance=GetGameInstance<UEWGameInstance>(); if (!Instance || !Status) return;
    Status->SetText(Instance->GetConnectionStatus());
    const bool bGame=GetWorld() && GetWorld()->WorldType==EWorldType::Game;
    const bool bCanStart=bGame && GetWorld()->GetNetMode()==NM_Standalone && !Instance->IsConnectionPending();
    HostButton->SetIsEnabled(bCanStart); JoinButton->SetIsEnabled(bCanStart);
    LeaveButton->SetIsEnabled(bGame && (Instance->IsConnectionPending() || GetWorld()->GetNetMode()!=NM_Standalone));
    Address->SetIsEnabled(bCanStart);
    if (!bGame) Status->SetText(NSLOCTEXT("Elitewake","SessionPIEHelp","Use Play > Standalone Game to test Host/Join. This panel cannot travel during in-editor Play."));
}
FReply UEWSessionWidget::NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event)
{
    if (Event.GetKey()==EKeys::F10 || Event.GetKey()==EKeys::Escape) { Close(); return FReply::Handled(); }
    return Super::NativeOnKeyDown(Geometry,Event);
}
void UEWSessionWidget::Host() { if (auto* Instance=GetGameInstance<UEWGameInstance>()) Instance->HostLocalGame(); }
void UEWSessionWidget::Join() { if (auto* Instance=GetGameInstance<UEWGameInstance>()) Instance->JoinLocalGame(Address->GetText().ToString()); }
void UEWSessionWidget::Leave() { if (auto* Instance=GetGameInstance<UEWGameInstance>()) Instance->LeaveLocalGame(); }
void UEWSessionWidget::Close() { if (auto* PC=Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetSessionMenuOpen(false); }
