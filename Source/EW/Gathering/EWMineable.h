#pragma once
#include "CoreMinimal.h"
#include "EWStation.h"
#include "EWItemDefinition.h"
#include "TimerManager.h"
#include "EWMineable.generated.h"

class UEWItemDefinition;

/** Finite single-resource mining node. Attack requires an equipped pickaxe. */
UCLASS(Blueprintable)
class EW_API AEWMineable : public AEWStation
{
    GENERATED_BODY()
public:
    AEWMineable();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    /** Idempotent server setup for placed and dynamically configured mineable nodes. */
    void InitializeMiningStock();
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining") TObjectPtr<UEWItemDefinition> Resource;
    // Draft defaults for opt-in fixtures; production yields remain designer-authored.
    UPROPERTY(EditAnywhere, ReplicatedUsing=OnRep_Remaining, BlueprintReadOnly, Category="Mining", meta=(ClampMin="0")) int32 Remaining = 12;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining", meta=(ClampMin="1")) int32 PerStrike = 3;
    /** Optional material requirement; None preserves unrestricted legacy/test mining nodes. */
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining") EEWPickaxeTier MinimumPickaxeTier = EEWPickaxeTier::None;
    /** Opt in for deposits that return after the authored interval instead of being removed. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mining") bool bRespawnWhenDepleted = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mining", meta=(ClampMin="0.01", Units="s")) float RespawnSeconds = 3600.f;
    /** Resource deposits use a randomized total stock, not a per-strike yield. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mining") bool bRandomizeStock = false;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mining", meta=(ClampMin="1", EditCondition="bRandomizeStock")) int32 MinimumStock = 4;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mining", meta=(ClampMin="1", EditCondition="bRandomizeStock")) int32 MaximumStock = 8;
    UFUNCTION(BlueprintPure, Category="Mining") bool CanAccessSource(AEWCharacter* Survivor) const;
    UFUNCTION(BlueprintPure, Category="Mining") bool CanMine(AEWCharacter* Survivor) const;
    /** Trusted native server entry; controller RPC supplies shared strike cadence. */
    int32 TryMine(AEWCharacter* Survivor);
    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override { return false; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override { return false; }
private:
    UFUNCTION() void OnRep_Remaining();
    void RefreshNodeAvailability();
    void Respawn();
    bool bMining = false;
    bool bStockInitialized = false;
    int32 InitialStock = 0;
    FTimerHandle RespawnTimer;
};
