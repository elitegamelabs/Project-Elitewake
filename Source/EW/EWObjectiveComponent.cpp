#include "EWObjectiveComponent.h"
#include "GameFramework/Actor.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWCraftingRecipe.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"

UEWObjectiveComponent::UEWObjectiveComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UEWObjectiveComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWObjectiveComponent, State, COND_OwnerOnly);
}

bool UEWObjectiveComponent::StartSequence(FName SequenceId, const TArray<FEWObjectiveStep>& Steps)
{
    return StartRecipeSequence(SequenceId, Steps, {});
}

bool UEWObjectiveComponent::StartRecipeSequence(FName SequenceId, const TArray<FEWObjectiveStep>& Steps,
    const TArray<UEWCraftingRecipe*>& CompletionRecipes)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || bUpdating || !State.SequenceId.IsNone()
        || SequenceId.IsNone() || Steps.IsEmpty()) return false;
    TSet<FName> Ids;
    for (const auto& Step : Steps)
    {
        if (Step.Id.IsNone() || Step.RequiredCount <= 0 || Ids.Contains(Step.Id)) return false;
        Ids.Add(Step.Id);
    }
    for (const auto* Recipe : CompletionRecipes)
        if (!Recipe || !Recipe->Output) return false;
    TGuardValue<bool> Guard(bUpdating, true);
    for (auto* Recipe : CompletionRecipes) RecipeRewards.AddUnique(Recipe);
    State.SequenceId = SequenceId;
    State.Steps = Steps;
    NotifyChanged();
    return true;
}

bool UEWObjectiveComponent::RecordProgress(FName ExpectedStepId, int32 Amount)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || bUpdating || Amount <= 0
        || !State.Steps.IsValidIndex(State.StepIndex)) return false;
    const auto& Step = State.Steps[State.StepIndex];
    if (ExpectedStepId != Step.Id) return false;
    TGuardValue<bool> Guard(bUpdating, true);
    // Clamp before adding to avoid overflow. Excess cannot spill into the next objective.
    State.Progress += FMath::Min(Amount, Step.RequiredCount - State.Progress);
    if (State.Progress == Step.RequiredCount)
    {
        ++State.StepIndex;
        State.Progress = 0;
    }
    if (IsComplete()) ApplyCompletionRecipes();
    NotifyChanged();
    return true;
}

bool UEWObjectiveComponent::IsComplete() const
{
    return !State.Steps.IsEmpty() && State.StepIndex == State.Steps.Num();
}

void UEWObjectiveComponent::NotifyChanged()
{
    GetOwner()->ForceNetUpdate();
    OnObjectivesChanged.Broadcast();
}

void UEWObjectiveComponent::OnRep_State()
{
    OnObjectivesChanged.Broadcast();
}

void UEWObjectiveComponent::ApplyCompletionRecipes()
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || !IsComplete() || bApplyingRecipes) return;
    const auto* PC = Cast<APlayerController>(GetOwner());
    auto* Character = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Character || Character->GetController() != PC) return;
    TGuardValue<bool> Guard(bApplyingRecipes, true);
    for (const auto& Recipe : RecipeRewards) Character->GetInventoryComponent()->UnlockRecipe(Recipe.Get());
}
