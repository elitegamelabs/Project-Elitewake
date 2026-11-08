// Copyright Elite Game Labs. All Rights Reserved.

#include "EWLessonComponent.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"
#include "Ships/EWShip.h"

namespace
{
enum ESailingStep : int32 { Board, AnchorUp, UnderWay, Steer, Hold, AnchorDown, Damage, SailingCount };
/** Seconds the last step stays up before the lesson ends by itself; seconds under way that count as sailing (tuning). */
constexpr float ReadSeconds = 12.f;
constexpr float SailingSeconds = 3.f;
constexpr float SailingSpeed = 150.f;   // cm/s
}

UEWLessonComponent::UEWLessonComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .25f;
    SetIsReplicatedByDefault(true);
}

void UEWLessonComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWLessonComponent, Lesson, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWLessonComponent, Step, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWLessonComponent, Finished, COND_OwnerOnly);
}

int32 UEWLessonComponent::StepCount(EEWLesson Of)
{
    return Of == EEWLesson::Sailing ? SailingCount : 0;
}

void UEWLessonComponent::StartLesson(EEWLesson NewLesson)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Lesson = NewLesson;
    Step = 0;
    StepSeconds = UnderWaySeconds = 0.f;
    bHoldOpened = false;
    GetOwner()->ForceNetUpdate();
}

void UEWLessonComponent::StopLesson()
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Lesson = EEWLesson::None;
    Step = 0;
    GetOwner()->ForceNetUpdate();
}

bool UEWLessonComponent::StepDone(int32 Index) const
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const AEWCharacter* Me = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Me || Me->IsDead()) return false;
    const AEWShip* Ship = Me->GetHelmShip() ? Me->GetHelmShip() : AEWShip::FindShipCarrying(Me);
    switch (Index)
    {
    case Board: return Ship != nullptr;
    case AnchorUp: return Ship && !Ship->IsAnchored();
    case UnderWay: return UnderWaySeconds >= SailingSeconds;
    case Steer: return Me->GetHelmShip() && FMath::Abs(Me->GetHelmShip()->GetRudder()) > .3f;
    case Hold: return bHoldOpened;
    case AnchorDown: return Ship && Ship->IsAnchored();
    case Damage: return StepSeconds >= ReadSeconds;
    default: return false;
    }
}

void UEWLessonComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!GetOwner() || !GetOwner()->HasAuthority() || Lesson == EEWLesson::None) return;
    StepSeconds += DeltaTime;
    // Under way: her own speed, kept up a few seconds (a ship pushed by a wave does not count).
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const AEWCharacter* Me = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    const AEWShip* Ship = Me ? (Me->GetHelmShip() ? Me->GetHelmShip() : AEWShip::FindShipCarrying(Me)) : nullptr;
    UnderWaySeconds = Ship && Ship->GetSpeed() > SailingSpeed ? UnderWaySeconds + DeltaTime : 0.f;
    if (!StepDone(Step)) return;
    ++Step;
    StepSeconds = 0.f;
    if (Step == Hold) bHoldOpened = false;    // opened before this step does not count
    if (Step >= StepCount(Lesson))
    {
        Lesson = EEWLesson::None;
        Step = 0;
        ++Finished;
    }
    GetOwner()->ForceNetUpdate();
}

FText UEWLessonComponent::GetPrompt(bool bPad) const
{
    if (Lesson != EEWLesson::Sailing) return FText::GetEmpty();
    switch (Step)
    {
    case Board: return bPad ? NSLOCTEXT("Elitewake", "LessonBoardPad", "Sailing 1/7: swim to her stern ladder, [Gamepad_FaceButton_Left] to take hold, [Gamepad_DPad_Up] to climb aboard")
                            : NSLOCTEXT("Elitewake", "LessonBoardKeys", "Sailing 1/7: swim to her stern ladder, E to take hold, the Up arrow to climb aboard");
    case AnchorUp: return bPad ? NSLOCTEXT("Elitewake", "LessonAnchorPad", "Sailing 2/7: at the capstan, hold [Gamepad_FaceButton_Left] to raise the anchor")
                               : NSLOCTEXT("Elitewake", "LessonAnchorKeys", "Sailing 2/7: at the capstan, hold E to raise the anchor");
    case UnderWay: return bPad ? NSLOCTEXT("Elitewake", "LessonSailPad", "Sailing 3/7: work a sail's lines ([Gamepad_FaceButton_Left]) and raise it with [Gamepad_DPad_Up]; swing it to the wind with [Gamepad_LeftShoulder] / [Gamepad_RightShoulder] until she moves")
                               : NSLOCTEXT("Elitewake", "LessonSailKeys", "Sailing 3/7: work a sail's lines (E) and raise it with the Up arrow; swing it to the wind with the Left / Right arrows until she moves");
    case Steer: return bPad ? NSLOCTEXT("Elitewake", "LessonSteerPad", "Sailing 4/7: hold [Gamepad_FaceButton_Left] at the wheel to take the helm, and steer with [Gamepad_Left2D]. The compass shows the wind")
                            : NSLOCTEXT("Elitewake", "LessonSteerKeys", "Sailing 4/7: hold E at the wheel to take the helm, and steer with A / D. The compass shows the wind");
    case Hold: return bPad ? NSLOCTEXT("Elitewake", "LessonHoldPad", "Sailing 5/7: leave the helm and open the hold at the hatch ([Gamepad_FaceButton_Left]) to stow cargo")
                           : NSLOCTEXT("Elitewake", "LessonHoldKeys", "Sailing 5/7: leave the helm and open the hold at the hatch (E) to stow cargo");
    case AnchorDown: return bPad ? NSLOCTEXT("Elitewake", "LessonDropPad", "Sailing 6/7: at the capstan, hold [Gamepad_FaceButton_Left] to drop the anchor and stop her")
                                 : NSLOCTEXT("Elitewake", "LessonDropKeys", "Sailing 6/7: at the capstan, hold E to drop the anchor and stop her");
    case Damage: return NSLOCTEXT("Elitewake", "LessonDamage", "Sailing 7/7: shot holes let the sea in. Bail with the bucket by the hatch, and have a shipwright repair her in port");
    default: return FText::GetEmpty();
    }
}
