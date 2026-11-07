#if WITH_DEV_AUTOMATION_TESTS
#include "EWObjectiveComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWObjectiveTest, "Elitewake.Objectives.OrderedAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWObjectiveTest::RunTest(const FString& Parameters)
{
    auto* Owner = NewObject<AActor>();
    auto* Objectives = NewObject<UEWObjectiveComponent>(Owner);
    FEWObjectiveStep First; First.Id = TEXT("Test.First"); First.RequiredCount = 2;
    FEWObjectiveStep Last; Last.Id = TEXT("Test.Last");
    TestFalse(TEXT("Empty state is not completion"), Objectives->IsComplete());
    TestFalse(TEXT("Cannot advance before sequence starts"), Objectives->RecordProgress(First.Id));
    TestFalse(TEXT("Duplicate step IDs reject whole definition"), Objectives->StartSequence(TEXT("Test"), {First, First}));
    TestFalse(TEXT("Null recipe reward rejects start"), Objectives->StartRecipeSequence(TEXT("Bad"), {Last}, {nullptr}));
    TestTrue(TEXT("Valid ordered definition accepted"), Objectives->StartSequence(TEXT("Test"), {First, Last}));
    First.RequiredCount = 100;
    TestEqual(TEXT("Runtime definition snapshots authored counts"), Objectives->GetState().Steps[0].RequiredCount, 2);
    TestFalse(TEXT("Cannot skip to a later step"), Objectives->RecordProgress(Last.Id));
    TestFalse(TEXT("Negative count rejected"), Objectives->RecordProgress(TEXT("Test.First"), -1));
    Objectives->RecordProgress(TEXT("Test.First"));
    TestEqual(TEXT("Partial progress retained"), Objectives->GetState().Progress, 1);
    Objectives->RecordProgress(TEXT("Test.First"), MAX_int32);
    TestEqual(TEXT("Large report advances only one step"), Objectives->GetState().StepIndex, 1);
    TestEqual(TEXT("Excess does not advance next step"), Objectives->GetState().Progress, 0);
    TestFalse(TEXT("Repeated prior-step report rejected"), Objectives->RecordProgress(TEXT("Test.First")));
    Owner->SetRole(ROLE_SimulatedProxy);
    TestFalse(TEXT("Client cannot complete"), Objectives->RecordProgress(Last.Id));
    auto* ClientObjectives = NewObject<UEWObjectiveComponent>(Owner);
    TestFalse(TEXT("Client cannot author reward sequence"), ClientObjectives->StartRecipeSequence(TEXT("Client"), {Last}, {}));
    TestFalse(TEXT("Client cannot start"), ClientObjectives->StartSequence(TEXT("Client"), {Last}));
    Owner->SetRole(ROLE_Authority);
    TestTrue(TEXT("Final step accepted"), Objectives->RecordProgress(Last.Id));
    TestTrue(TEXT("Sequence complete"), Objectives->IsComplete());
    TestFalse(TEXT("Repeated completion rejected"), Objectives->RecordProgress(Last.Id));
    TestFalse(TEXT("Completed sequence cannot be restarted for rewards"), Objectives->StartSequence(TEXT("Test"), {Last}));
    return true;
}
#endif
