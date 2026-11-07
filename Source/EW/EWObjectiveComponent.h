#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWObjectiveComponent.generated.h"

class UEWCraftingRecipe;

USTRUCT(BlueprintType)
struct FEWObjectiveStep
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName Id;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FText Description;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1")) int32 RequiredCount = 1;
};

USTRUCT(BlueprintType)
struct FEWObjectiveState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FName SequenceId;
    UPROPERTY(BlueprintReadOnly) TArray<FEWObjectiveStep> Steps;
    UPROPERTY(BlueprintReadOnly) int32 StepIndex = 0;
    UPROPERTY(BlueprintReadOnly) int32 Progress = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWObjectivesChanged);

/** Session-only ordered objectives. Trusted server gameplay reports validated events;
 * there is deliberately no client completion RPC or automatic production sequence. */
UCLASS(ClassGroup=(Elitewake), meta=(BlueprintSpawnableComponent))
class EW_API UEWObjectiveComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWObjectiveComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Objectives")
    bool StartSequence(FName SequenceId, const TArray<FEWObjectiveStep>& Steps);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Objectives")
    bool StartRecipeSequence(FName SequenceId, const TArray<FEWObjectiveStep>& Steps,
        const TArray<UEWCraftingRecipe*>& CompletionRecipes);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Objectives")
    bool RecordProgress(FName ExpectedStepId, int32 Amount = 1);
    UFUNCTION(BlueprintPure, Category="Objectives") FEWObjectiveState GetState() const { return State; }
    UFUNCTION(BlueprintPure, Category="Objectives") bool IsComplete() const;
    UPROPERTY(BlueprintAssignable, Category="Objectives") FEWObjectivesChanged OnObjectivesChanged;
private:
    friend class AEWPlayerController;
    UPROPERTY(ReplicatedUsing=OnRep_State) FEWObjectiveState State;
    UPROPERTY() TArray<TObjectPtr<UEWCraftingRecipe>> RecipeRewards;
    UFUNCTION() void OnRep_State();
    bool bUpdating = false;
    bool bApplyingRecipes = false;
    void ApplyCompletionRecipes();
    void NotifyChanged();
};
