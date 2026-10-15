#pragma once
#include "CoreMinimal.h"
#include "EWStation.h"
#include "EWMineable.generated.h"

class UEWItemDefinition;

/** Finite single-resource mining node. Attack requires an equipped pickaxe. */
UCLASS(Blueprintable)
class EW_API AEWMineable : public AEWStation
{
    GENERATED_BODY()
public:
    AEWMineable();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining") TObjectPtr<UEWItemDefinition> Resource;
    // Draft defaults for opt-in fixtures; production yields remain designer-authored.
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining", meta=(ClampMin="0")) int32 Remaining = 12;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Mining", meta=(ClampMin="1")) int32 PerStrike = 3;
    UFUNCTION(BlueprintPure, Category="Mining") bool CanAccessSource(AEWCharacter* Survivor) const;
    UFUNCTION(BlueprintPure, Category="Mining") bool CanMine(AEWCharacter* Survivor) const;
    /** Trusted native server entry; controller RPC supplies shared strike cadence. */
    int32 TryMine(AEWCharacter* Survivor);
    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override { return false; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override { return false; }
private:
    bool bMining = false;
};
