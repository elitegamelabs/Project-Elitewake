#include "EWGameInstance.h"
#include "EWPlayerController.h"
#include "EW.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Containers/Ticker.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace { const FName LocalMap(TEXT("/Game/ThirdPerson/Lvl_ThirdPerson")); }

bool UEWGameInstance::NormalizePrivateAddress(const FString& Input, FString& Output)
{
    Output.Reset();
    FString Address=Input.TrimStartAndEnd();
    if (Address.Len()>64 || Address.IsEmpty()) return false;
    FString Host, Port;
    if (!Address.Split(TEXT(":"),&Host,&Port)) Host=Address;
    else if (Port.IsEmpty() || Port.Len()>5 || !Port.IsNumeric() || FCString::Atoi(*Port)<1 || FCString::Atoi(*Port)>65535) return false;
    for (TCHAR C:Port) if (C<TEXT('0') || C>TEXT('9')) return false;
    if (Host.Equals(TEXT("localhost"),ESearchCase::IgnoreCase)) Host=TEXT("127.0.0.1");
    TArray<FString> Parts; Host.ParseIntoArray(Parts,TEXT("."),false);
    if (Parts.Num()!=4) return false;
    int32 Values[4];
    for (int32 I=0;I<4;++I)
    {
        if (Parts[I].IsEmpty() || Parts[I].Len()>3) return false;
        for (TCHAR C:Parts[I]) if (C<TEXT('0') || C>TEXT('9')) return false;
        Values[I]=FCString::Atoi(*Parts[I]); if (Values[I]>255) return false;
    }
    if (!(Values[0]==127 || Values[0]==10 || (Values[0]==172 && Values[1]>=16 && Values[1]<=31)
        || (Values[0]==192 && Values[1]==168))) return false;
    Output=FString::Printf(TEXT("%d.%d.%d.%d:%d"),Values[0],Values[1],Values[2],Values[3],Port.IsEmpty()?7777:FCString::Atoi(*Port));
    return true;
}
void UEWGameInstance::Init()
{
    Super::Init();
    FString Label;
    const bool bLoadedLabel = FFileHelper::LoadFileToString(Label, *(FPaths::ProjectDir() / TEXT("PrivateBuildLabel.txt")));
    Label.TrimStartAndEndInline();
    if (bLoadedLabel && !Label.IsEmpty() && Label.Len() <= 160
        && !Label.Contains(TEXT("\n")) && !Label.Contains(TEXT("\r")))
    {
        PrivateBuildLabel = FText::FromString(Label);
    }
    else
    {
        PrivateBuildLabel = NSLOCTEXT("Elitewake", "UnlabelledBuild", "Unlabelled development build");
    }
    UE_LOG(LogEW, Log, TEXT("Private test build: %s"), *PrivateBuildLabel.ToString());
    if (GEngine)
    {
        NetworkFailureHandle=GEngine->OnNetworkFailure().AddUObject(this,&UEWGameInstance::NetworkFailed);
        TravelFailureHandle=GEngine->OnTravelFailure().AddUObject(this,&UEWGameInstance::TravelFailed);
    }
}
void UEWGameInstance::Shutdown()
{
    if (GEngine) { GEngine->OnNetworkFailure().Remove(NetworkFailureHandle); GEngine->OnTravelFailure().Remove(TravelFailureHandle); }
    if (RecoveryHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(RecoveryHandle);
    if (ArrivalHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(ArrivalHandle);
    Super::Shutdown();
}
bool UEWGameInstance::CanStart()
{
    auto* World=GetWorld();
    if (!World || World->WorldType!=EWorldType::Game)
    { Status=NSLOCTEXT("Elitewake","SessionStandalone","Use Play > Standalone Game for Host/Join. In-editor Play cannot travel through this panel."); return false; }
    if (bPending) return false;
    if (World->GetNetMode()!=NM_Standalone)
    { Status=NSLOCTEXT("Elitewake","SessionLeaveFirst","Leave the current session before hosting or joining another."); return false; }
    return true;
}
bool UEWGameInstance::HostLocalGame()
{
    if (!CanStart()) return false;
    bHasConnectionError=false; bPending=true; bShowMenuOnArrival=true;
    Status=NSLOCTEXT("Elitewake","SessionHosting","Starting a local host...");
    UGameplayStatics::OpenLevel(this,LocalMap,true,TEXT("listen")); return true;
}
bool UEWGameInstance::JoinLocalGame(const FString& Address)
{
    FString Target;
    if (!NormalizePrivateAddress(Address,Target))
    { Status=NSLOCTEXT("Elitewake","SessionInvalidAddress","Enter a local or LAN IPv4 address, such as 127.0.0.1:7777. Internet connection setup is pending."); return false; }
    if (!CanStart()) return false;
    auto* Controller=UGameplayStatics::GetPlayerController(this,0);
    if (!Controller || !Controller->IsLocalController()) return false;
    bHasConnectionError=false; bPending=true; bShowMenuOnArrival=true;
    Status=NSLOCTEXT("Elitewake","SessionJoining","Connecting... Use Leave / Cancel to return to local play.");
    Controller->ClientTravel(Target,TRAVEL_Absolute); return true;
}
bool UEWGameInstance::LeaveLocalGame()
{
    if (!GetWorld() || GetWorld()->WorldType!=EWorldType::Game)
    { Status=NSLOCTEXT("Elitewake","SessionLeavePIE","Stop Play to leave an in-editor test session."); return false; }
    bHasConnectionError=false; bPending=true; bShowMenuOnArrival=true;
    Status=NSLOCTEXT("Elitewake","SessionLeaving","Returning to local play...");
    UGameplayStatics::OpenLevel(this,LocalMap,true); return true;
}
void UEWGameInstance::LocalControllerReady(AEWPlayerController* Controller)
{
    if (!Controller || !Controller->IsLocalController() || Controller->GetGameInstance()!=this) return;
    if (ArrivalHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(ArrivalHandle);
    TWeakObjectPtr<UEWGameInstance> WeakThis(this);
    TWeakObjectPtr<AEWPlayerController> WeakController(Controller);
    ArrivalHandle=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WeakThis,WeakController](float)
    {
        auto* Instance=WeakThis.Get(); auto* PC=WeakController.Get();
        if (!Instance || !PC || PC->IsActorBeingDestroyed()) return false;
        if (!PC->GetPawn() || (PC->GetWorld()->GetNetMode()==NM_Client && PC->AcknowledgedPawn!=PC->GetPawn())) return true;
        Instance->CompleteArrival(PC); return false;
    }),.1f);
}
void UEWGameInstance::CompleteArrival(AEWPlayerController* Controller)
{
    const bool bWasPending=bPending;
    bPending=false;
    const ENetMode Mode=Controller->GetWorld()->GetNetMode();
    if (Mode==NM_ListenServer) Status=NSLOCTEXT("Elitewake","SessionHostReady","Hosting a local/LAN game. Leaving disconnects all joined players.");
    else if (Mode==NM_Client) Status=NSLOCTEXT("Elitewake","SessionClientReady","Connected to the host. The world continues while this menu is open.");
    else if (!bHasConnectionError && (bWasPending || !bShowMenuOnArrival)) Status=NSLOCTEXT("Elitewake","SessionLocalReady","Local play. F10 opens the private-test connection panel.");
    if (bShowMenuOnArrival || (Mode==NM_Standalone && bHasConnectionError)) { bShowMenuOnArrival=false; Controller->SetSessionMenuOpen(true); }
}
void UEWGameInstance::ReturnAfterFailure()
{
    bHasConnectionError=true; bPending=false; bShowMenuOnArrival=true;
    if (RecoveryHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(RecoveryHandle);
    TWeakObjectPtr<UEWGameInstance> WeakThis(this);
    RecoveryHandle=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WeakThis](float)
    {
        if (auto* Instance=WeakThis.Get())
            if (Instance->GetWorld() && Instance->GetWorld()->WorldType==EWorldType::Game)
            {
                if (Instance->GetWorld()->GetNetMode()!=NM_Standalone) UGameplayStatics::OpenLevel(Instance,LocalMap,true);
                else if (auto* PC=Cast<AEWPlayerController>(UGameplayStatics::GetPlayerController(Instance,0))) Instance->LocalControllerReady(PC);
            }
        return false;
    }),.1f);
}
void UEWGameInstance::NetworkFailed(UWorld* World, UNetDriver* Driver, ENetworkFailure::Type Type, const FString& Error)
{
    const FWorldContext* PendingContext=GEngine && Driver ? GEngine->GetWorldContextFromPendingNetGameNetDriver(Driver) : nullptr;
    if ((!World || World->GetGameInstance()!=this) && (!PendingContext || PendingContext->OwningGameInstance!=this)) return;
    UE_LOG(LogEW,Warning,TEXT("Private-test network failure (%d): %s"),static_cast<int32>(Type),*Error);
    Status=Type==ENetworkFailure::ConnectionLost ? NSLOCTEXT("Elitewake","SessionLost","Connection to the host was lost. You are back in local play.")
        : NSLOCTEXT("Elitewake","SessionConnectFailed","Could not connect. Check the address, matching build and that the host is running, then try again.");
    ReturnAfterFailure();
}
void UEWGameInstance::TravelFailed(UWorld* World, ETravelFailure::Type Type, const FString& Error)
{
    if (!World || World->GetGameInstance()!=this) return;
    UE_LOG(LogEW,Warning,TEXT("Private-test travel failure (%d): %s"),static_cast<int32>(Type),*Error);
    Status=NSLOCTEXT("Elitewake","SessionTravelFailed","Could not open the session map. Return to local play and check that both builds include the same map.");
    // Avoid a retry loop if the retained local map itself is missing.
    bHasConnectionError=true; bPending=false; bShowMenuOnArrival=true;
    if (auto* PC=Cast<AEWPlayerController>(UGameplayStatics::GetPlayerController(this,0))) PC->SetSessionMenuOpen(true);
}
