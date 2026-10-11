#if WITH_EDITOR
#include "EWGameInstance.h"
#include "EWPlayerController.h"
#include "EWSessionWidget.h"
#include "EWCharacter.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "InputKeyEventArgs.h"
#include "InputCoreTypes.h"

namespace EWSessionTest
{
static FTSTicker::FDelegateHandle Handle;
static bool bHost=false;
static bool bRecovery=false;
static int32 Phase=0, Port=17887;
static double Started=0.;
static double Changed=0.;
static TArray<FString> Checks;
static FString Path(const TCHAR* Name) { return FPaths::ProjectSavedDir()/TEXT("SessionLifecycle")/Name; }
static void Write(const TCHAR* Name,const FString& Text) { FFileHelper::SaveStringToFile(Text,*Path(Name)); }
static bool Exists(const TCHAR* Name) { return IFileManager::Get().FileExists(*Path(Name)); }
static bool Finish(bool bPass,const FString& Error=FString())
{
    Write(bHost?TEXT("HostResult.txt"):TEXT("ClientResult.txt"),(bPass?TEXT("PASS\n"):TEXT("FAIL\n"))+FString::Join(Checks,TEXT("\n"))+TEXT("\n")+Error); return false;
}
static void F10(AEWPlayerController* PC)
{
    FInputKeyEventArgs Key; Key.Key=EKeys::F10; Key.Event=IE_Pressed; Key.AmountDepressed=1.f; PC->InputKey(Key);
}
static bool MenuReady(AEWPlayerController* PC)
{
    return PC->IsSessionMenuOpen() && PC->SessionWidget && PC->SessionWidget->IsInViewport() && PC->IsMoveInputIgnored() && PC->IsLookInputIgnored();
}
static bool Tick(float Delta)
{
    const double Now=FPlatformTime::Seconds();
    if (Now-Started>240.) return Finish(false,FString::Printf(TEXT("Lifecycle timed out at phase %d."),Phase));
    UWorld* World=nullptr;
    if (GEngine) for (const FWorldContext& Context:GEngine->GetWorldContexts())
        if (Context.WorldType==EWorldType::Game && Context.World()) { World=Context.World(); break; }
    auto* Instance=World?Cast<UEWGameInstance>(World->GetGameInstance()):nullptr;
    AEWPlayerController* Local=nullptr;
    if (World) for (TActorIterator<AEWPlayerController> It(World);It;++It) if (It->IsLocalController()) { Local=*It; break; }
    if (!Instance || !Local || !Local->GetPawn() || World->GetTimeSeconds()<1.f) return true;
    const ENetMode Mode=World->GetNetMode();
    if (bHost)
    {
        if (Phase==0 && Mode==NM_Standalone)
        {
            for (int I=0;I<5;++I)
            {
                F10(Local); if (!MenuReady(Local)) return Finish(false,TEXT("F10 panel failed to open."));
                Local->SetSessionMenuOpen(false);
                if (Local->IsMoveInputIgnored() || Local->IsLookInputIgnored()) return Finish(false,TEXT("Panel left input locks behind."));
            }
            Local->SetMapOpen(true); F10(Local);
            if (Local->IsMapOpen() || !MenuReady(Local)) return Finish(false,TEXT("Map-to-session switch failed."));
            Local->SetSessionMenuOpen(false); Local->SetInventoryOpen(true); F10(Local);
            if (Local->IsInventoryOpen() || !MenuReady(Local)) return Finish(false,TEXT("Inventory-to-session switch failed."));
            Local->SetSessionMenuOpen(false);
            Checks.Add(TEXT("F10 panel cycles and map/inventory switching preserve balanced local input locks"));
            if (!Instance->HostLocalGame()) return Finish(false,TEXT("Host request failed.")); Phase=1;
        }
        else if (Phase==1 && Mode==NM_ListenServer && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local)) return Finish(false,TEXT("Host arrival panel missing."));
            Local->SetSessionMenuOpen(false);
            Checks.Add(TEXT("Host API opens retained map as listen server and presents arrival panel"));
            Write(TEXT("HostReady"),TEXT("ready")); Phase=2;
        }
        else if (Phase==2 && Exists(TEXT("ClientLeft")))
        {
            int32 Count=0; for (TActorIterator<AEWPlayerController> It(World);It;++It) ++Count;
            if (Count!=1) return true;
            Checks.Add(TEXT("Client Leave returns locally and removes remote server controller"));
            Write(TEXT("HostLeaveObserved"),TEXT("observed")); Phase=3;
        }
        else if (Phase==3 && Exists(TEXT("ClientRejoined")))
        {
            int32 Count=0; for (TActorIterator<AEWPlayerController> It(World);It;++It) ++Count;
            if (Count!=2) return true;
            if (bRecovery)
            {
                Checks.Add(TEXT("Host remains active with rejoined client before external abrupt-process shutdown"));
                Write(TEXT("HostCrashReady"),TEXT("ready")); return Finish(true);
            }
            if (!Instance->LeaveLocalGame()) return Finish(false,TEXT("Host Leave request failed.")); Phase=4;
        }
        else if (Phase==4 && Mode==NM_Standalone && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local)) return Finish(false,TEXT("Host Leave panel missing."));
            Checks.Add(TEXT("Host Leave tears down listen session and returns to local map"));
            Write(TEXT("HostFinished"),TEXT("done")); return Finish(true);
        }
    }
    else
    {
        if (Phase==0 && Mode==NM_Standalone && Exists(TEXT("HostReady")))
        {
            if (Instance->JoinLocalGame(TEXT("/Game/Other?listen")) || Instance->IsConnectionPending()) return Finish(false,TEXT("Travel URL was accepted."));
            Checks.Add(TEXT("Invalid travel URL is rejected before connection"));
            if (bRecovery)
            {
                if (!Instance->JoinLocalGame(FString::Printf(TEXT("127.0.0.1:%d"),Port+1)) || !Instance->IsConnectionPending())
                    return Finish(false,TEXT("Cancellation fixture did not start a pending connection."));
                Changed=Now; Phase=6; return true;
            }
            if (!Instance->JoinLocalGame(FString::Printf(TEXT("127.0.0.1:%d"),Port))) return Finish(false,TEXT("Join request failed.")); Phase=1;
        }
        else if (Phase==6 && Now-Changed>2.)
        {
            if (!Instance->IsConnectionPending()) return Finish(false,TEXT("Connection ceased pending before cancellation."));
            if (!Instance->LeaveLocalGame()) return Finish(false,TEXT("Pending connection cancellation failed."));
            Phase=7; Changed=0.;
        }
        else if (Phase==7 && Mode==NM_Standalone && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local) || !Instance->GetConnectionStatus().ToString().StartsWith(TEXT("Local play.")))
                return Finish(false,TEXT("Cancelled connection did not restore local play and arrival panel."));
            Local->SetSessionMenuOpen(false);
            if (Local->IsMoveInputIgnored() || Local->IsLookInputIgnored()) return Finish(false,TEXT("Cancellation left input locks behind."));
            Checks.Add(TEXT("Cancel during pending handshake returns locally; closing its arrival panel restores controls"));
            Changed=Now; Phase=8;
        }
        else if (Phase==8 && Now-Changed>25.)
        {
            if (Mode!=NM_Standalone || Instance->IsConnectionPending() || Local->IsSessionMenuOpen()
                || !Instance->GetConnectionStatus().ToString().StartsWith(TEXT("Local play.")))
                return Finish(false,TEXT("Cancelled handshake later overwrote local play or reopened its panel."));
            Checks.Add(TEXT("Cancelled handshake remains local without delayed failure/panel after twenty-five seconds"));
            if (!Instance->JoinLocalGame(FString::Printf(TEXT("127.0.0.1:%d"),Port))) return Finish(false,TEXT("Join after cancellation failed.")); Phase=1;
        }
        else if (Phase==1 && Mode==NM_Client && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local)) return Finish(false,FString::Printf(TEXT("Joined client panel missing: open=%d widget=%d move=%d look=%d"),Local->IsSessionMenuOpen(),Local->SessionWidget && Local->SessionWidget->IsInViewport(),Local->IsMoveInputIgnored(),Local->IsLookInputIgnored()));
            Local->SetSessionMenuOpen(false);
            if (Local->IsMoveInputIgnored() || Local->IsLookInputIgnored()) return Finish(false,TEXT("Joined client controls remain locked."));
            Checks.Add(TEXT("Join API connects and presents local panel; closing restores controls"));
            if (!Instance->LeaveLocalGame()) return Finish(false,TEXT("Client Leave failed.")); Phase=2;
        }
        else if (Phase==2 && Mode==NM_Standalone && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local)) return Finish(false,TEXT("Client Leave panel missing."));
            Write(TEXT("ClientLeft"),TEXT("left"));
            if (!Exists(TEXT("HostLeaveObserved"))) return true;
            if (!Instance->JoinLocalGame(FString::Printf(TEXT("127.0.0.1:%d"),Port))) return Finish(false,TEXT("Rejoin request failed.")); Phase=3;
        }
        else if (Phase==3 && Mode==NM_Client && !Instance->IsConnectionPending())
        {
            Checks.Add(TEXT("Client can rejoin after an explicit leave"));
            Write(TEXT("ClientRejoined"),TEXT("joined")); Phase=4;
        }
        else if (Phase==4 && Mode==NM_Standalone && !Instance->IsConnectionPending() && Exists(TEXT("HostFinished")))
        {
            if (bRecovery && MenuReady(Local) && !Instance->GetConnectionStatus().ToString().Contains(TEXT("lost")))
                return Finish(false,TEXT("Abrupt host recovery did not explain loss of the established session: ")+Instance->GetConnectionStatus().ToString());
            if (!MenuReady(Local) || !Instance->GetConnectionStatus().ToString().Contains(TEXT("lost"))) return true;
            Checks.Add(bRecovery ? TEXT("Abrupt host-process shutdown returns client locally with persistent lost-connection message")
                : TEXT("Host departure returns client to local play with persistent lost-connection message"));
            if (!Instance->JoinLocalGame(FString::Printf(TEXT("127.0.0.1:%d"),Port+1))) return Finish(false,TEXT("Closed-port join did not start.")); Phase=5;
        }
        else if (Phase==5 && Mode==NM_Standalone && !Instance->IsConnectionPending())
        {
            if (!MenuReady(Local) || !Instance->GetConnectionStatus().ToString().Contains(TEXT("Could not connect"))) return true;
            Local->SetSessionMenuOpen(false);
            if (Local->IsMoveInputIgnored() || Local->IsLookInputIgnored()) return Finish(false,TEXT("Failure left input locks behind."));
            Checks.Add(TEXT("Closed-port timeout returns locally with readable error and unlocked controls after closing panel"));
            return Finish(true);
        }
    }
    return true;
}
}
void StartEWSessionVerification()
{
    FString Role;
    if (!FParse::Value(FCommandLine::Get(),TEXT("EWVerifySessionRole="),Role) || (Role!=TEXT("Host") && Role!=TEXT("Client"))) return;
    EWSessionTest::bHost=Role==TEXT("Host"); EWSessionTest::Started=FPlatformTime::Seconds();
    EWSessionTest::bRecovery=FParse::Param(FCommandLine::Get(),TEXT("EWVerifyRecovery"));
    FParse::Value(FCommandLine::Get(),TEXT("EWVerifyPort="),EWSessionTest::Port);
    IFileManager::Get().MakeDirectory(*EWSessionTest::Path(TEXT("")),true);
    EWSessionTest::Handle=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&EWSessionTest::Tick),.05f);
}
void StopEWSessionVerification()
{
    if (EWSessionTest::Handle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(EWSessionTest::Handle);
}
#endif
