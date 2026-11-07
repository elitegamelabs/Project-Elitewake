#pragma once
#include "CoreMinimal.h"
#include "EWPickup.h"
#include "EWInnTorchPickup.generated.h"
class APlayerState;

/** Introductory wall item: one unit per PlayerState during the current session. */
UCLASS(Blueprintable)
class EW_API AEWInnTorchPickup : public AEWPickup
{
    GENERATED_BODY()
public:
    AEWInnTorchPickup();
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UFUNCTION(BlueprintPure, Category="Inn") bool HasCollected(const AEWCharacter* Character) const;
    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual int32 TryPickup(AEWCharacter* Character) override;
private:
    UPROPERTY(Replicated) TArray<TObjectPtr<APlayerState>> CollectedPlayers;
    bool bGrantInProgress = false;
};
