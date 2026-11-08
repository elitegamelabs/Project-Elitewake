#include "EWGameInstance.h"
#include "Misc/SecureHash.h"
#include "EWPlayerController.h"
#include "Characters/EWAppearanceSave.h"
#include "EWCharacter.h"
#include "EWSurvivorSave.h"
#include "Title/EWFreeports.h"
#include "Title/EWLoadingWidget.h"
#include "Engine/Texture2D.h"
#include "MoviePlayer.h"
#include "AudioDevice.h"
#include "AudioDeviceManager.h"
#include "WorldPartition/WorldPartitionSubsystem.h"
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
    const int32 GamePort=Port.IsEmpty()?7777:FCString::Atoi(*Port);
    // Owner, October 30 (friends over the Internet): a host name (a dynamic-DNS name) is accepted too: letters, digits and hyphens in
    // dot-separated labels, with at least one letter, never a URL, an option or a path.
    bool bHasLetter=false, bNameChars=!Host.IsEmpty() && Host.Len()<=63;
    for (TCHAR C:Host)
    {
        if (FChar::IsAlpha(C)) bHasLetter=true;
        else if (!FChar::IsDigit(C) && C!=TEXT('.') && C!=TEXT('-')) bNameChars=false;
    }
    if (bHasLetter)
    {
        TArray<FString> Labels; Host.ParseIntoArray(Labels,TEXT("."),false);
        if (!bNameChars || Labels.Num()<1) return false;
        for (const FString& Label:Labels)
            if (Label.IsEmpty() || Label.StartsWith(TEXT("-")) || Label.EndsWith(TEXT("-"))) return false;
        Output=FString::Printf(TEXT("%s:%d"),*Host.ToLower(),GamePort);
        return true;
    }
    TArray<FString> Parts; Host.ParseIntoArray(Parts,TEXT("."),false);
    if (Parts.Num()!=4) return false;
    int32 Values[4];
    for (int32 I=0;I<4;++I)
    {
        if (Parts[I].IsEmpty() || Parts[I].Len()>3) return false;
        for (TCHAR C:Parts[I]) if (C<TEXT('0') || C>TEXT('9')) return false;
        Values[I]=FCString::Atoi(*Parts[I]); if (Values[I]>255) return false;
    }
    // Any host a friend can reach: this PC, the LAN or the Internet (a public address); never 0.x, multicast or reserved.
    if (Values[0]==0 || Values[0]>=224) return false;
    Output=FString::Printf(TEXT("%d.%d.%d.%d:%d"),Values[0],Values[1],Values[2],Values[3],GamePort);
    return true;
}
FString UEWGameInstance::StablePlayerId()
{
    return FMD5::HashAnsiString(*(FPlatformMisc::GetLoginId() + TEXT("|") + FPlatformProcess::UserName()));
}

void UEWGameInstance::SetChosenAppearance(const FEWAppearance& Appearance)
{
    ChosenAppearance = Appearance;
    bHasChosenAppearance = true;
    if (auto* Save = Cast<UEWAppearanceSave>(UGameplayStatics::CreateSaveGameObject(UEWAppearanceSave::StaticClass())))
    {
        Save->Appearance = Appearance;
        UGameplayStatics::SaveGameToSlot(Save, UEWAppearanceSave::Slot, 0);
    }
}

void UEWGameInstance::Init()
{
    Super::Init();
    if (const auto* Saved = Cast<UEWAppearanceSave>(UGameplayStatics::LoadGameFromSlot(UEWAppearanceSave::Slot, 0)))
    {
        ChosenAppearance = Saved->Appearance;
        bHasChosenAppearance = true;
    }
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
    ApplyMasterVolume(GetSavedMasterVolume());
    // Brightness too, so the title and the creator show it before any survivor's controller loads (the same formula as
    // AEWPlayerController::ApplyBrightness: 50 on the slider is the engine's 2.2 gamma).
    float Brightness=0.f;
    if (GConfig) GConfig->GetFloat(TEXT("Elitewake.UserControls"),TEXT("BrightnessGamma"),Brightness,GGameUserSettingsIni);
    if (GEngine && FMath::IsFinite(Brightness)) GEngine->DisplayGamma=2.2f*FMath::Exp2(FMath::Clamp(Brightness,-.5f,.5f)*2.f);
    PreLoadHandle=FCoreUObjectDelegates::PreLoadMap.AddUObject(this,&UEWGameInstance::PreLoadMap);
    PostLoadHandle=FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this,&UEWGameInstance::PostLoadMap);
}
void UEWGameInstance::Shutdown()
{
    if (GEngine) { GEngine->OnNetworkFailure().Remove(NetworkFailureHandle); GEngine->OnTravelFailure().Remove(TravelFailureHandle); }
    if (RecoveryHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(RecoveryHandle);
    if (ArrivalHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(ArrivalHandle);
    if (LoadingHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(LoadingHandle);
    FCoreUObjectDelegates::PreLoadMap.Remove(PreLoadHandle);
    FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadHandle);
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
    bJoinedHost=false;
    bHasConnectionError=false; bPending=true; bShowMenuOnArrival=true;
    Status=NSLOCTEXT("Elitewake","SessionHosting","Starting a local host...");
    UGameplayStatics::OpenLevel(this,LocalMap,true,TEXT("listen")); return true;
}
bool UEWGameInstance::JoinLocalGame(const FString& Address)
{
    FString Target;
    if (!NormalizePrivateAddress(Address,Target))
    { Status=NSLOCTEXT("Elitewake","SessionInvalidAddress","Enter the host's address: 127.0.0.1 on this PC, their LAN address, or over the Internet their public IP (or host name), port 7777."); return false; }
    if (!CanStart()) return false;
    auto* Controller=UGameplayStatics::GetPlayerController(this,0);
    if (!Controller || !Controller->IsLocalController()) return false;
    bJoinedHost=false;
    bHasConnectionError=false; bPending=true; bShowMenuOnArrival=true;
    Status=NSLOCTEXT("Elitewake","SessionJoining","Connecting... Use Leave / Cancel to return to local play.");
    // Who this is, so the host gives back this player's survivor when they come again.
    Controller->ClientTravel(Target+TEXT("?EWId=")+StablePlayerId(),TRAVEL_Absolute); return true;
}
bool UEWGameInstance::LeaveLocalGame()
{
    if (!GetWorld() || GetWorld()->WorldType!=EWorldType::Game)
    { Status=NSLOCTEXT("Elitewake","SessionLeavePIE","Stop Play to leave an in-editor test session."); return false; }
    // Reloading local play alone does not dispose a pending connection attempt.
    // Cancel its driver before travel so its later timeout cannot overwrite recovery.
    if (GEngine) GEngine->CancelPending(GetWorld());
    if (RecoveryHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(RecoveryHandle);
    if (ArrivalHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(ArrivalHandle);
    bJoinedHost=false;
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
    bJoinedHost=Mode==NM_Client;
    if (bResumeSurvivor && Mode==NM_Standalone)
    {
        bResumeSurvivor=false;
        if (const UEWSurvivorSave* Save=UEWSurvivorSave::LoadSave())
            if (Save->ApplyTo(Cast<AEWCharacter>(Controller->GetPawn())))
                UE_LOG(LogEW,Log,TEXT("Resumed the survivor saved %s"),*Save->SavedAt.ToString());
    }
    if (bStartAtFreeport && Mode==NM_Standalone)
    {
        // A new survivor stands on the chosen Freeport's plaza, before its merchant.
        bStartAtFreeport=false;
        FVector Spot; FRotator Facing;
        APawn* Survivor=Controller->GetPawn();
        if (Survivor && EWFreeports::FindSpawn(Controller->GetWorld(),EWFreeports::IndexOf(ChosenFreeport),Spot,Facing))
        {
            Survivor->TeleportTo(Spot,Facing,false,true);
            Controller->SetControlRotation(Facing);
            UE_LOG(LogEW,Log,TEXT("New survivor set down at the %s Freeport"),*ChosenFreeport.ToString());
        }
        else UE_LOG(LogEW,Warning,TEXT("No merchant found at the %s Freeport; the survivor starts at the usual arrival"),*ChosenFreeport.ToString());
    }
    if (bVoyageLoading) FinishLoadingWhenReady();
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
    const bool bLostJoinedHost=bJoinedHost;
    bJoinedHost=false;
    Status=(bLostJoinedHost || Type==ENetworkFailure::ConnectionLost) ? NSLOCTEXT("Elitewake","SessionLost","Connection to the host was lost. You are back in local play.")
        : NSLOCTEXT("Elitewake","SessionConnectFailed","Could not connect. Check the address, matching build and that the host is running, then try again.");
    ReturnAfterFailure();
}
void UEWGameInstance::TravelFailed(UWorld* World, ETravelFailure::Type Type, const FString& Error)
{
    if (!World || World->GetGameInstance()!=this) return;
    UE_LOG(LogEW,Warning,TEXT("Private-test travel failure (%d): %s"),static_cast<int32>(Type),*Error);
    Status=NSLOCTEXT("Elitewake","SessionTravelFailed","Could not open the session map. Return to local play and check that both builds include the same map.");
    bJoinedHost=false;
    // Avoid a retry loop if the retained local map itself is missing.
    bHasConnectionError=true; bPending=false; bShowMenuOnArrival=true;
    if (auto* PC=Cast<AEWPlayerController>(UGameplayStatics::GetPlayerController(this,0))) PC->SetSessionMenuOpen(true);
}

void UEWGameInstance::PrepareVoyage(bool bResume, FName Freeport)
{
    bResumeSurvivor=bResume;
    bStartAtFreeport=!bResume && EWFreeports::IndexOf(Freeport)!=INDEX_NONE;
    ChosenFreeport=Freeport;
    bVoyageLoading=true;
}
void UEWGameInstance::ShowLoadingScreen()
{
    if (!Loading)
    {
        Loading=CreateWidget<UEWLoadingWidget>(this,UEWLoadingWidget::StaticClass());
        if (!Loading) return;
        Loading->VoyageArt=Cast<UTexture2D>(FSoftObjectPath(VoyageArt).TryLoad());
    }
    Loading->Restart();
    ReadyAt=0.0;
    if (!Loading->IsInViewport()) Loading->AddToViewport(1000);
}
bool UEWGameInstance::IsLoadingScreenShown() const { return Loading && Loading->IsInViewport(); }
void UEWGameInstance::PreLoadMap(const FString& MapName)
{
    if (!bVoyageLoading || !Loading || IsRunningDedicatedServer()) return;
    // While the map loads the game thread is held; the movie player keeps the same screen drawn and moving.
    if (IsMoviePlayerEnabled())
    {
        FLoadingScreenAttributes Screen;
        Screen.bAutoCompleteWhenLoadingCompletes=true;
        Screen.bMoviesAreSkippable=false;
        Screen.WidgetLoadingScreen=Loading->TakeWidget();
        GetMoviePlayer()->SetupLoadingScreen(Screen);
    }
}
void UEWGameInstance::PostLoadMap(UWorld* World)
{
    // The new map removed every widget; the screen stays up until the survivor has arrived and the world round them is in.
    // A new map can bring a new audio device (each editor Play world has its own): give it the player's volume too.
    if (World && World->GetGameInstance()==this) ApplyMasterVolume(GetSavedMasterVolume());
    if (bVoyageLoading && World && World->GetGameInstance()==this) ShowLoadingScreen();
}
void UEWGameInstance::FinishLoadingWhenReady()
{
    if (LoadingHandle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(LoadingHandle);
    if (!Loading) { bVoyageLoading=false; return; }
    if (!Loading->IsInViewport()) ShowLoadingScreen();
    const double Arrived=FPlatformTime::Seconds();
    TWeakObjectPtr<UEWGameInstance> WeakThis(this);
    LoadingHandle=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WeakThis,Arrived](float)
    {
        UEWGameInstance* Instance=WeakThis.Get();
        if (!Instance || !Instance->Loading) return false;
        UWorld* World=Instance->GetWorld();
        const double Now=FPlatformTime::Seconds();
        const UWorldPartitionSubsystem* Partition=World ? World->GetSubsystem<UWorldPartitionSubsystem>() : nullptr;
        // At least a moment on the screen; then until the cells round the survivor are in (at most half a minute).
        const bool bStreamed=!Partition || Partition->IsStreamingCompleted();
        if (!Instance->Loading->IsReady())
        {
            if (Now-Arrived<1.5 || (!bStreamed && Now-Arrived<30.0)) return true;
            Instance->Loading->SetReady();
            Instance->ReadyAt=Now;
            return true;
        }
        // The bar shows full for half a second, then the screen fades over half a second.
        const double Since=Now-Instance->ReadyAt;
        Instance->Loading->SetFade(1.f-float(FMath::Clamp((Since-.5)/.5,0.0,1.0)));
        if (Since<1.0) return true;
        Instance->Loading->RemoveFromParent();
        Instance->bVoyageLoading=false;
        Instance->LoadingHandle.Reset();
        return false;
    }),0.f);
}

float UEWGameInstance::GetSavedMasterVolume()
{
    float Volume=1.f;
    if (GConfig) GConfig->GetFloat(TEXT("Elitewake.UserControls"),TEXT("MasterVolume"),Volume,GGameUserSettingsIni);
    return FMath::IsFinite(Volume) ? FMath::Clamp(Volume,0.f,1.f) : 1.f;
}
void UEWGameInstance::ApplyMasterVolume(float Volume)
{
    const float Clamped=FMath::Clamp(Volume,0.f,1.f);
    AppliedMasterVolume=Clamped;
    if (GEngine)
        if (FAudioDeviceManager* Devices=GEngine->GetAudioDeviceManager())
            Devices->IterateOverAllDevices([Clamped](Audio::FDeviceId, FAudioDevice* Device) { if (Device) Device->SetTransientPrimaryVolume(Clamped); });
}
