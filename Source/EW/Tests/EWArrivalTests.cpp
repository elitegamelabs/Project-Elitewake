#if WITH_DEV_AUTOMATION_TESTS
#include "EWArrivalComponent.h"
#include "EWArrivalPromptWidget.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWArrivalTrackerTest, "Elitewake.Arrival.StepsFinishByDoingThem",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWArrivalTrackerTest::RunTest(const FString& Parameters)
{
    FEWArrivalSnapshot Here;
    FEWArrivalTracker Tracker;

    Tracker.Begin(EEWArrivalStep::Look, Here);
    FEWArrivalSnapshot Turned = Here; Turned.Yaw = 20.f;
    TestFalse(TEXT("A small turn is not yet looking around"), Tracker.Update(Turned));
    Turned.Yaw = -10.f; Turned.Pitch = 5.f;
    TestTrue(TEXT("Turns add up to looking around"), Tracker.Update(Turned));
    FEWArrivalSnapshot Wrapped = Here; Wrapped.Yaw = 179.f;
    Tracker.Begin(EEWArrivalStep::Look, Wrapped);
    Wrapped.Yaw = -179.f;
    TestFalse(TEXT("Crossing 180 degrees counts as 2, not 358"), Tracker.Update(Wrapped));

    Tracker.Begin(EEWArrivalStep::Move, Here);
    FEWArrivalSnapshot Walked = Here; Walked.Location = FVector(200.f, 0.f, 0.f);
    TestFalse(TEXT("Two metres is not yet walking"), Tracker.Update(Walked));
    Walked.Location = FVector(200.f, 250.f, 900.f);
    TestTrue(TEXT("Three metres across the ground is walking"), Tracker.Update(Walked));
    Tracker.Begin(EEWArrivalStep::Move, Here);
    FEWArrivalSnapshot Lifted = Here; Lifted.Location = FVector(0.f, 0.f, 1000.f);
    TestFalse(TEXT("Rising straight up is not walking"), Tracker.Update(Lifted));

    Tracker.Begin(EEWArrivalStep::Jump, Here);
    TestFalse(TEXT("Standing is not jumping"), Tracker.Update(Here));
    FEWArrivalSnapshot Jumped = Here; Jumped.bJumping = true;
    TestTrue(TEXT("A jump finishes the jump step"), Tracker.Update(Jumped));

    Tracker.Begin(EEWArrivalStep::Crouch, Here);
    FEWArrivalSnapshot Low = Here; Low.bLow = true;
    TestTrue(TEXT("Crouching finishes the crouch step"), Tracker.Update(Low));

    Tracker.Begin(EEWArrivalStep::Interact, Here);
    TestFalse(TEXT("The client never finishes the interact step"), Tracker.Update(Jumped));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWArrivalAuthorityTest, "Elitewake.Arrival.ServerOwnsTheSteps",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWArrivalAuthorityTest::RunTest(const FString& Parameters)
{
    auto* Owner = NewObject<AActor>();
    auto* Arrival = NewObject<UEWArrivalComponent>(Owner);
    TestEqual(TEXT("A new survivor starts at the first step"), Arrival->GetStep(), EEWArrivalStep::Look);
    Arrival->ServerCompleteStep_Implementation(1);
    TestEqual(TEXT("A later step cannot be claimed first"), Arrival->GetStepIndex(), 0);
    Arrival->NoteInteracted();
    TestEqual(TEXT("Using something early does not skip ahead"), Arrival->GetStepIndex(), 0);
    for (int32 Step = 0; Step < int32(EEWArrivalStep::Interact); ++Step) Arrival->ServerCompleteStep_Implementation(Step);
    TestEqual(TEXT("The first four steps finish in order"), Arrival->GetStep(), EEWArrivalStep::Interact);
    Arrival->ServerCompleteStep_Implementation(int32(EEWArrivalStep::Interact));
    TestEqual(TEXT("The client cannot claim the interact step"), Arrival->GetStep(), EEWArrivalStep::Interact);
    Arrival->NoteInteracted();
    TestTrue(TEXT("A real interaction finishes the arrival"), Arrival->IsComplete());
    Arrival->NoteInteracted();
    TestEqual(TEXT("Finished stays finished"), Arrival->GetStepIndex(), UEWArrivalComponent::StepCount);

    Arrival->SetStepIndex(-4);
    TestEqual(TEXT("A restored step is clamped low"), Arrival->GetStepIndex(), 0);
    Arrival->SetStepIndex(99);
    TestTrue(TEXT("A restored step is clamped high"), Arrival->IsComplete());
    Owner->SetRole(ROLE_SimulatedProxy);
    Arrival->SetStepIndex(1);
    TestTrue(TEXT("Only the server sets the step"), Arrival->IsComplete());

    for (int32 Step = 0; Step < UEWArrivalComponent::StepCount; ++Step)
    {
        TestFalse(TEXT("Every step has keyboard words"), UEWArrivalComponent::PromptFor(EEWArrivalStep(Step), false).IsEmpty());
        TestFalse(TEXT("Every step has controller words"), UEWArrivalComponent::PromptFor(EEWArrivalStep(Step), true).IsEmpty());
    }
    TestTrue(TEXT("The finished arrival shows nothing"), UEWArrivalComponent::PromptFor(EEWArrivalStep::Done, false).IsEmpty());
    TestTrue(TEXT("Prompt text is at least 24 px at 1080p"), UEWArrivalPromptWidget::FontSize >= 24);
    return true;
}
#endif
