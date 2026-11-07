#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWInteractionComponent.generated.h"

class AEWCharacter;

USTRUCT(BlueprintType)
struct FEWHoldState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) TObjectPtr<AActor> Target;
    UPROPERTY(BlueprintReadOnly) double StartTime = 0;
    UPROPERTY(BlueprintReadOnly) float Duration = 0;
    UPROPERTY(BlueprintReadOnly) int32 Revision = 0;
};

/** Owned-controller server state. Clients supply intent, never elapsed time or completion. */
UCLASS(ClassGroup=(Elitewake), BlueprintType)
class EW_API UEWInteractionComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWInteractionComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    void Request(AActor* Target);
    void Cancel();
    void SetMenuBlocked(bool bBlocked);
    UFUNCTION(BlueprintPure, Category="Interaction") FEWHoldState GetHoldState() const { return Hold; }
    UFUNCTION(BlueprintPure, Category="Interaction") bool IsMenuBlocked() const { return bMenuBlocked; }
private:
    UPROPERTY(Replicated) FEWHoldState Hold;
    TWeakObjectPtr<AEWCharacter> StartingPawn;
    FTimerHandle ValidationTimer;
    bool bMenuBlocked = false;
    bool bDispatching = false;
    double LastRequestTime = -100;
    AEWCharacter* GetSurvivor() const;
    bool IsEligible(AActor* Target, AEWCharacter* Survivor) const;
    void ValidateHold();
};
