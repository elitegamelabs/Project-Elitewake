#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "Engine/EngineBaseTypes.h"
#include "Containers/Ticker.h"
#include "Characters/EWAppearance.h"
#include "EWGameInstance.generated.h"

class AEWPlayerController;
class UEWLoadingWidget;
class UNetDriver;

/** Private-test direct connection lifecycle; no account/session-service integration. */
UCLASS()
class EW_API UEWGameInstance : public UGameInstance
{
    GENERATED_BODY()
public:
    virtual void Init() override;
    virtual void Shutdown() override;
    UFUNCTION(BlueprintCallable, Category="Multiplayer") bool HostLocalGame();
    UFUNCTION(BlueprintCallable, Category="Multiplayer") bool JoinLocalGame(const FString& Address);
    UFUNCTION(BlueprintCallable, Category="Multiplayer") bool LeaveLocalGame();
    UFUNCTION(BlueprintPure, Category="Multiplayer") FText GetConnectionStatus() const { return Status; }
    UFUNCTION(BlueprintPure, Category="Multiplayer") bool IsConnectionPending() const { return bPending; }
    UFUNCTION(BlueprintPure, Category="Multiplayer") FText GetPrivateBuildLabel() const { return PrivateBuildLabel; }
    void LocalControllerReady(AEWPlayerController* Controller);
    /** The look chosen in the character creator, kept for this run and saved for the next. */
    UFUNCTION(BlueprintCallable, Category="Appearance") void SetChosenAppearance(const FEWAppearance& Appearance);
    UFUNCTION(BlueprintPure, Category="Appearance") FEWAppearance GetChosenAppearance() const { return ChosenAppearance; }
    UFUNCTION(BlueprintPure, Category="Appearance") bool HasChosenAppearance() const { return bHasChosenAppearance; }
    /** Single Player from the title: the next survivor to arrive in local play picks up from the save, if any. */
    UFUNCTION(BlueprintCallable, Category="Save") void ResumeSavedSurvivorOnArrival() { bResumeSurvivor = true; }
    UFUNCTION(BlueprintPure, Category="Save") bool WillResumeSavedSurvivor() const { return bResumeSurvivor; }
    /** Set Sail from the front end (owner, November 7): resume the saved survivor, or start a new one at this Freeport
     *  (EWFreeports id: Plains, Winter, Swamp, Desert, Jungle). The next arrival in local play carries it out. */
    UFUNCTION(BlueprintCallable, Category="Front end") void PrepareVoyage(bool bResume, FName Freeport);
    UFUNCTION(BlueprintPure, Category="Front end") FName GetChosenFreeport() const { return ChosenFreeport; }
    UFUNCTION(BlueprintPure, Category="Front end") bool WillStartAtFreeport() const { return bStartAtFreeport; }
    /** The loading screen over everything until the world is ready (also held by the movie player while a map loads). */
    UFUNCTION(BlueprintCallable, Category="Front end") void ShowLoadingScreen();
    UFUNCTION(BlueprintPure, Category="Front end") bool IsLoadingScreenShown() const;
    UFUNCTION(BlueprintPure, Category="Front end") UEWLoadingWidget* GetLoadingWidget() const { return Loading; }
    /** The player's master volume (0-1, Options), saved in the user settings. Applied to every audio device's primary
     *  volume, so it scales every sound: world, ambience, interface, music. Unreal resets FApp's volume multiplier itself
     *  when the window gains or loses focus, so that is not used. */
    static float GetSavedMasterVolume();
    /** Sound effects (owner, November 7): every one-shot through UEWSoundLibrary (work, steps, ships, cannons, animals) and
     *  the campfire. Ambience: the background loops (sea, wind, insects, caves, regions, a ship's creak and rigging, the town).
     *  Each 0-1, under the master volume, applied live. */
    UFUNCTION(BlueprintPure, Category="Options") static float GetSoundEffectsVolume() { return SoundEffectsVolume; }
    UFUNCTION(BlueprintPure, Category="Options") static float GetAmbienceVolume() { return AmbienceVolume; }
    UFUNCTION(BlueprintCallable, Category="Options") static void SetSoundEffectsVolume(float Volume);
    UFUNCTION(BlueprintCallable, Category="Options") static void SetAmbienceVolume(float Volume);
    static inline float SoundEffectsVolume = 1.f;
    static inline float AmbienceVolume = 1.f;
    /** Interface size (FUTURE_IMPLEMENTATIONS Part 8, 62; November 8): every HUD, menu and screen drawn larger or smaller,
     *  MinInterfaceScale to MaxInterfaceScale (1 = as designed at 1080p). Saved with the other settings, applied live. */
    UFUNCTION(BlueprintPure, Category="Options") static float GetInterfaceScale() { return InterfaceScale; }
    UFUNCTION(BlueprintCallable, Category="Options") static void SetInterfaceScale(float Scale);
    /** The scale the interface is drawn at now (for checks). */
    UFUNCTION(BlueprintPure, Category="Options") static float GetAppliedInterfaceScale();
    static inline float InterfaceScale = 1.f;
    static constexpr float MinInterfaceScale = .8f;
    static constexpr float MaxInterfaceScale = 1.5f;
    static void ApplyMasterVolume(float Volume);
    /** The volume last given to the audio devices (for checks). */
    UFUNCTION(BlueprintPure, Category="Options") static float GetAppliedMasterVolume() { return AppliedMasterVolume; }
    static inline float AppliedMasterVolume = 1.f;
    static inline const TCHAR* VoyageArt = TEXT("/Game/Elitewake/UI/FrontEnd/T_LoadingVoyage.T_LoadingVoyage");
    /** Accept only local/private IPv4 addresses, optional port, or localhost. Never arbitrary travel URLs. */
    static bool NormalizePrivateAddress(const FString& Input, FString& Output);
    /** This PC's player, the same every time the game starts (a hash of the Windows login): a host keeps a joining player's survivor
     *  under it (the online identity of a direct-IP game changes every launch). Sent with Join as the EWId option. */
    static FString StablePlayerId();
private:
    void NetworkFailed(UWorld* World, UNetDriver* Driver, ENetworkFailure::Type Type, const FString& Error);
    void TravelFailed(UWorld* World, ETravelFailure::Type Type, const FString& Error);
    void ReturnAfterFailure();
    void CompleteArrival(AEWPlayerController* Controller);
    void PreLoadMap(const FString& MapName);
    void PostLoadMap(UWorld* World);
    /** Waits for the world round the survivor to stream in, then lets the loading screen go. */
    void FinishLoadingWhenReady();
    UPROPERTY(Transient) TObjectPtr<UEWLoadingWidget> Loading;
    FName ChosenFreeport;
    bool bStartAtFreeport = false;
    bool bVoyageLoading = false;
    double ReadyAt = 0.0;
    bool CanStart();
    FText Status;
    FText PrivateBuildLabel;
    FEWAppearance ChosenAppearance;
    bool bHasChosenAppearance = false;
    bool bPending = false;
    bool bJoinedHost = false;
    bool bHasConnectionError = false;
    bool bShowMenuOnArrival = false;
    bool bResumeSurvivor = false;
    FDelegateHandle NetworkFailureHandle, TravelFailureHandle, PreLoadHandle, PostLoadHandle;
    FTSTicker::FDelegateHandle RecoveryHandle, ArrivalHandle, LoadingHandle;
};
