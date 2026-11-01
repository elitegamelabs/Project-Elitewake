#include "EWArrivalComponent.h"
#include "EWCharacter.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerStart.h"
#include "Net/UnrealNetwork.h"

void FEWArrivalTracker::Begin(EEWArrivalStep InStep, const FEWArrivalSnapshot& Now)
{
    Step = InStep;
    Start = Last = Now;
    Looked = 0.f;
}

bool FEWArrivalTracker::Update(const FEWArrivalSnapshot& Now)
{
    bool bDone = false;
    switch (Step)
    {
    case EEWArrivalStep::Look:
        Looked += FMath::Abs(FRotator::NormalizeAxis(Now.Yaw - Last.Yaw)) + FMath::Abs(FRotator::NormalizeAxis(Now.Pitch - Last.Pitch));
        bDone = Looked >= LookDegrees;
        break;
    case EEWArrivalStep::Move: bDone = FVector::Dist2D(Now.Location, Start.Location) >= WalkDistance; break;
    case EEWArrivalStep::Jump: bDone = Now.bJumping; break;
    case EEWArrivalStep::Crouch: bDone = Now.bLow; break;
    default: break;   // the interact step is the server's to judge
    }
    Last = Now;
    return bDone;
}

UEWArrivalComponent::UEWArrivalComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .05f;
    SetIsReplicatedByDefault(true);
}

void UEWArrivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWArrivalComponent, Step, COND_OwnerOnly);
}

void UEWArrivalComponent::BeginPlay()
{
    Super::BeginPlay();
    ShowAt = GetWorld()->GetTimeSeconds() + FirstPromptDelay;
    if (!GetOwner()->HasAuthority()) return;
    // Only a map built for arriving teaches it (build_arrival.py tags its PlayerStart); test maps start finished.
    bool bArrivalMap = false;
    for (TActorIterator<APlayerStart> It(GetWorld()); It && !bArrivalMap; ++It) bArrivalMap = It->PlayerStartTag == ArrivalStartTag;
    if (!bArrivalMap) Step = StepCount;
}

bool UEWArrivalComponent::ReadSnapshot(FEWArrivalSnapshot& Out) const
{
    const auto* Survivor = Cast<AEWCharacter>(GetOwner());
    if (!Survivor || !Survivor->IsLocallyControlled() || !Survivor->GetController()) return false;
    const FRotator View = Survivor->GetControlRotation();
    const auto* Movement = Survivor->GetCharacterMovement();
    Out.Location = Survivor->GetActorLocation();
    Out.Yaw = View.Yaw;
    Out.Pitch = View.Pitch;
    Out.bJumping = Movement && Movement->IsFalling() && Movement->Velocity.Z > 50.f && Survivor->JumpCurrentCount > 0;
    Out.bLow = Survivor->bIsCrouched || Survivor->IsProne();
    return true;
}

void UEWArrivalComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (IsComplete()) return;
    FEWArrivalSnapshot Now;
    if (!ReadSnapshot(Now)) return;
    const double Time = GetWorld()->GetTimeSeconds();
    if (Time < ShowAt) return;
    if (Tracker.Step != GetStep())
    {
        Tracker.Begin(GetStep(), Now);
        return;
    }
    if (!Tracker.Update(Now)) return;
    // Told once a second at most until the server's answer arrives (it may be on its way).
    if (SentFor == Step && Time - SentAt < 1.) return;
    SentFor = Step;
    SentAt = Time;
    ServerCompleteStep(Step);
}

bool UEWArrivalComponent::IsPromptDue() const
{
    return !IsComplete() && GetWorld() && GetWorld()->GetTimeSeconds() >= ShowAt && Tracker.Step == GetStep();
}

void UEWArrivalComponent::ServerCompleteStep_Implementation(int32 Completed)
{
    if (Completed == Step && Step < int32(EEWArrivalStep::Interact)) Advance();
}

void UEWArrivalComponent::NoteInteracted()
{
    if (GetOwner() && GetOwner()->HasAuthority() && GetStep() == EEWArrivalStep::Interact) Advance();
}

void UEWArrivalComponent::SetStepIndex(int32 NewStep)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Step = FMath::Clamp(NewStep, 0, StepCount);
    GetOwner()->ForceNetUpdate();
    OnRep_Step();
}

void UEWArrivalComponent::Advance()
{
    Step = FMath::Min(Step + 1, StepCount);
    GetOwner()->ForceNetUpdate();
    OnRep_Step();   // the host's own survivor has no replication to wait for
}

void UEWArrivalComponent::OnRep_Step()
{
    if (GetWorld()) ShowAt = FMath::Max(ShowAt, GetWorld()->GetTimeSeconds() + StepGap);
    Tracker.Step = EEWArrivalStep::Done;
}

FText UEWArrivalComponent::PromptFor(EEWArrivalStep Step, bool bController)
{
    switch (Step)
    {
    case EEWArrivalStep::Look: return bController ? NSLOCTEXT("Elitewake", "ArrivalLookPad", "Right stick: look around")
                                                   : NSLOCTEXT("Elitewake", "ArrivalLookKeys", "Mouse: look around");
    case EEWArrivalStep::Move: return bController ? NSLOCTEXT("Elitewake", "ArrivalMovePad", "Left stick: walk")
                                                   : NSLOCTEXT("Elitewake", "ArrivalMoveKeys", "W A S D: walk");
    case EEWArrivalStep::Jump: return bController ? NSLOCTEXT("Elitewake", "ArrivalJumpPad", "A: jump")
                                                   : NSLOCTEXT("Elitewake", "ArrivalJumpKeys", "Space: jump");
    case EEWArrivalStep::Crouch: return bController ? NSLOCTEXT("Elitewake", "ArrivalCrouchPad", "B: crouch (hold to lie flat)")
                                                     : NSLOCTEXT("Elitewake", "ArrivalCrouchKeys", "C: crouch (hold to lie flat)");
    case EEWArrivalStep::Interact: return bController ? NSLOCTEXT("Elitewake", "ArrivalUsePad", "X: drink at the spring ahead, or use what you face")
                                                       : NSLOCTEXT("Elitewake", "ArrivalUseKeys", "E: drink at the spring ahead, or use what you face");
    default: return FText::GetEmpty();
    }
}
