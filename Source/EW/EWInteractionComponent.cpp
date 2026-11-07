#include "EWInteractionComponent.h"
#include "EWInteractable.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWArrivalComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameStateBase.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Net/UnrealNetwork.h"

UEWInteractionComponent::UEWInteractionComponent()
{
    SetIsReplicatedByDefault(true);
    PrimaryComponentTick.bCanEverTick = false;
}
void UEWInteractionComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWInteractionComponent, Hold, COND_OwnerOnly);
}
AEWCharacter* UEWInteractionComponent::GetSurvivor() const
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    AEWCharacter* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    return IsValid(Survivor) && Survivor->GetController() == PC ? Survivor : nullptr;
}
bool UEWInteractionComponent::IsEligible(AActor* Target, AEWCharacter* Survivor) const
{
    return !bMenuBlocked && IsValid(Survivor) && !Survivor->IsActorBeingDestroyed()
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0
        && IsValid(Target) && !Target->IsActorBeingDestroyed() && Target->GetWorld() == GetWorld()
        && Target->Implements<UEWInteractable>() && FEWInteractionTargeting::FindTarget(Survivor) == Target
        && IEWInteractable::Execute_CanInteract(Target, Survivor);
}
void UEWInteractionComponent::Request(AActor* Target)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || bDispatching) return;
    // Reliable requests on the same owned controller remain ordered. Repeats cannot reset a hold.
    if (Hold.Target) return;
    const double Now = GetWorld()->GetTimeSeconds();
    if (Now - LastRequestTime < .1) return;
    LastRequestTime = Now;
    AEWCharacter* Survivor = GetSurvivor();
    if (!IsEligible(Target, Survivor)) return;
    if (IEWInteractable::Execute_GetInteractionModeFor(Target, Survivor) == EEWInteractionMode::Press)
    {
        TGuardValue<bool> Guard(bDispatching, true);
        if (IEWInteractable::Execute_Interact(Target, Survivor) && IsValid(Survivor)) Survivor->GetArrivalComponent()->NoteInteracted();
        return;
    }
    const float Duration = IEWInteractable::Execute_GetHoldDurationFor(Target, Survivor);
    if (!FMath::IsFinite(Duration) || Duration <= 0) return;
    Hold.Target = Target;
    Hold.Duration = Duration;
    Hold.StartTime = GetWorld()->GetGameState() ? GetWorld()->GetGameState()->GetServerWorldTimeSeconds() : Now;
    Hold.Revision = Hold.Revision == MAX_int32 ? 0 : Hold.Revision + 1;
    StartingPawn = Survivor;
    GetWorld()->GetTimerManager().SetTimer(ValidationTimer, this, &UEWInteractionComponent::ValidateHold, .05f, true);
    GetOwner()->ForceNetUpdate();
    IEWInteractable::Execute_HoldChanged(Target, Survivor, true);
}
void UEWInteractionComponent::Cancel()
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    GetWorld()->GetTimerManager().ClearTimer(ValidationTimer);
    AActor* Ended = Hold.Target;
    AEWCharacter* Holder = StartingPawn.Get();
    StartingPawn.Reset();
    if (Hold.Target || Hold.Duration > 0)
    {
        Hold.Target = nullptr; Hold.Duration = 0; Hold.StartTime = 0;
        Hold.Revision = Hold.Revision == MAX_int32 ? 0 : Hold.Revision + 1;
        GetOwner()->ForceNetUpdate();
    }
    if (IsValid(Ended) && Ended->Implements<UEWInteractable>()) IEWInteractable::Execute_HoldChanged(Ended, Holder, false);
}
void UEWInteractionComponent::SetMenuBlocked(bool bBlocked)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    bMenuBlocked = bBlocked;
    if (bBlocked) Cancel();
}
void UEWInteractionComponent::ValidateHold()
{
    AEWCharacter* Survivor = GetSurvivor();
    AActor* Target = Hold.Target;
    if (Survivor != StartingPawn.Get() || !IsEligible(Target, Survivor)
        || IEWInteractable::Execute_GetInteractionModeFor(Target, Survivor) != EEWInteractionMode::Hold
        || IEWInteractable::Execute_GetHoldDurationFor(Target, Survivor) != Hold.Duration)
    {
        Cancel(); return;
    }
    const double Now = GetWorld()->GetGameState() ? GetWorld()->GetGameState()->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    if (Now - Hold.StartTime < Hold.Duration) return;
    // Clear before dispatch: a target may destroy itself or change possession during completion.
    Cancel();
    TGuardValue<bool> Guard(bDispatching, true);
    if (IEWInteractable::Execute_Interact(Target, Survivor) && IsValid(Survivor)) Survivor->GetArrivalComponent()->NoteInteracted();
}
void UEWInteractionComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Hold.Target) Cancel();
    if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(ValidationTimer);
    Super::EndPlay(Reason);
}
