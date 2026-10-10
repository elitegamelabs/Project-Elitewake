#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "Engine/EngineBaseTypes.h"
#include "Containers/Ticker.h"
#include "EWGameInstance.generated.h"

class AEWPlayerController;
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
    /** Accept only local/private IPv4 addresses, optional port, or localhost. Never arbitrary travel URLs. */
    static bool NormalizePrivateAddress(const FString& Input, FString& Output);
private:
    void NetworkFailed(UWorld* World, UNetDriver* Driver, ENetworkFailure::Type Type, const FString& Error);
    void TravelFailed(UWorld* World, ETravelFailure::Type Type, const FString& Error);
    void ReturnAfterFailure();
    void CompleteArrival(AEWPlayerController* Controller);
    bool CanStart();
    FText Status;
    FText PrivateBuildLabel;
    bool bPending = false;
    bool bHasConnectionError = false;
    bool bShowMenuOnArrival = false;
    FDelegateHandle NetworkFailureHandle, TravelFailureHandle;
    FTSTicker::FDelegateHandle RecoveryHandle, ArrivalHandle;
};
