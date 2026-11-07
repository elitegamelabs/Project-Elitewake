#if WITH_DEV_AUTOMATION_TESTS
#include "EWArrivalComponent.h"
#include "EWArrivalPromptWidget.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWArrivalTownStepsTest, "Elitewake.Arrival.TownStepsFinishByDoingThem",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWArrivalTownStepsTest::RunTest(const FString& Parameters)
{
    auto* Owner = NewObject<AActor>();
    auto* Arrival = NewObject<UEWArrivalComponent>(Owner);
    TestEqual(TEXT("A new survivor has done none of the town"), Arrival->GetTownStepsDone(), 0);
    TestEqual(TEXT("Selling comes first"), Arrival->GetTownStep(), EEWTownStep::Sell);
    TestFalse(TEXT("Nothing in town is shown before the arrival prompts finish"), Arrival->IsTownPromptDue());

    Arrival->NoteTownStep(EEWTownStep::Shipyard);
    TestTrue(TEXT("A step done out of order counts"), Arrival->IsTownStepDone(EEWTownStep::Shipyard));
    TestEqual(TEXT("The first step not done is still the one shown"), Arrival->GetTownStep(), EEWTownStep::Sell);
    Arrival->NoteTownStep(EEWTownStep::Sell);
    TestEqual(TEXT("Then storing"), Arrival->GetTownStep(), EEWTownStep::Store);
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Store));
    TestFalse(TEXT("The client cannot claim storing"), Arrival->IsTownStepDone(EEWTownStep::Store));
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Sell) + 99);
    TestEqual(TEXT("Nonsense from the client changes nothing"), Arrival->GetTownStepsDone(), 0b0101);
    Arrival->NoteTownStep(EEWTownStep::Store);
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Company));
    TestTrue(TEXT("The client reports the Company page itself"), Arrival->IsTownStepDone(EEWTownStep::Company));
    TestEqual(TEXT("Then buying a boat"), Arrival->GetTownStep(), EEWTownStep::Boat);
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Boat));
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Provision));
    Arrival->ServerCompleteTownStep_Implementation(int32(EEWTownStep::Voyage));
    TestEqual(TEXT("The client cannot claim a boat, provisions or an arrival it has not made"), Arrival->GetTownStepsDone(), 0b1111);
    Arrival->NoteTownStep(EEWTownStep::Boat);
    Arrival->NoteTownStep(EEWTownStep::Provision);
    TestEqual(TEXT("Then the voyage"), Arrival->GetTownStep(), EEWTownStep::Voyage);
    Arrival->NoteTownStep(EEWTownStep::Voyage);
    TestTrue(TEXT("Arriving finishes the town and the voyage's readiness"), Arrival->IsTownComplete());
    TestEqual(TEXT("All done shows nothing"), Arrival->GetTownStep(), EEWTownStep::Done);

    Arrival->SetTownStepsDone(0xFF);
    TestEqual(TEXT("A restored mask keeps only real steps"), Arrival->GetTownStepsDone(), UEWArrivalComponent::AllTownSteps);
    Arrival->SetTownStepsDone(0);
    Owner->SetRole(ROLE_SimulatedProxy);
    Arrival->NoteTownStep(EEWTownStep::Sell);
    Arrival->SetTownStepsDone(UEWArrivalComponent::AllTownSteps);
    TestEqual(TEXT("Only the server marks town steps"), Arrival->GetTownStepsDone(), 0);
    FVector Place;
    TestFalse(TEXT("No place on the compass outside the town"), Arrival->GetTownTarget(Place));

    for (int32 Step = 0; Step < UEWArrivalComponent::TownStepCount; ++Step)
    {
        TestFalse(TEXT("Every town step has keyboard words"), UEWArrivalComponent::TownPromptFor(EEWTownStep(Step), false).IsEmpty());
        TestFalse(TEXT("Every town step has controller words"), UEWArrivalComponent::TownPromptFor(EEWTownStep(Step), true).IsEmpty());
        TestTrue(TEXT("Town prompts are one line, under 80 characters"), UEWArrivalComponent::TownPromptFor(EEWTownStep(Step), false).ToString().Len() < 80);
    }
    TestEqual(TEXT("The first voyage goes to the Swamp island"), Arrival->VoyageRegion, EEWRegion::Swamp);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWVoyageProvisionsTest, "Elitewake.Arrival.VoyageProvisionsCountTheHold",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWVoyageProvisionsTest::RunTest(const FString& Parameters)
{
    auto Load = [](const TCHAR* Path) { return LoadObject<UEWItemDefinition>(nullptr, Path); };
    UEWItemDefinition* Meat = Load(TEXT("/Game/Elitewake/Items/Food/DA_CookedMeat.DA_CookedMeat"));
    UEWItemDefinition* Herb = Load(TEXT("/Game/Elitewake/Items/Food/DA_MedicinalHerb.DA_MedicinalHerb"));
    UEWItemDefinition* Full = Load(TEXT("/Game/Elitewake/Items/Testing/DA_TestWaterskinFull.DA_TestWaterskinFull"));
    UEWItemDefinition* Empty = Load(TEXT("/Game/Elitewake/Items/Testing/DA_TestHideWaterFlask.DA_TestHideWaterFlask"));
    UEWItemDefinition* Wood = Load(TEXT("/Game/Elitewake/Items/Testing/DA_TestWood.DA_TestWood"));
    UEWItemDefinition* Kit = Load(TEXT("/Game/Elitewake/Items/Testing/DA_TestRepairKit.DA_TestRepairKit"));
    if (!TestTrue(TEXT("The provisions' items exist"), Meat && Herb && Full && Empty && Wood && Kit)) return false;
    TestEqual(TEXT("Wood patches 1"), Wood->PatchValue, 1);
    TestEqual(TEXT("A repair kit patches 20"), Kit->PatchValue, 20);

    auto* Owner = NewObject<AActor>();
    auto* Hold = NewObject<UEWInventoryComponent>(Owner);
    TestFalse(TEXT("An empty hold is not ready"), FEWVoyageProvisions::Count(Hold).IsReady());
    TArray<FEWInventoryEntry>& Entries = Hold->Entries;
    auto Add = [&Entries](UEWItemDefinition* Item, int32 Quantity) { FEWInventoryEntry Entry; Entry.ItemDefinition = Item; Entry.Quantity = Quantity; Entries.Add(Entry); };
    Add(Meat, 2); Add(Herb, 5); Add(Empty, 1); Add(Wood, 19);
    FEWVoyageProvisions Counted = FEWVoyageProvisions::Count(Hold);
    TestEqual(TEXT("Cooked meat is food; a herb is medicine, not food"), Counted.Food, 2);
    TestEqual(TEXT("An empty waterskin is no water"), Counted.Water, 0);
    TestEqual(TEXT("Nineteen wood patch nineteen"), Counted.Patch, 19);
    TestFalse(TEXT("Not ready without water and with too little wood"), Counted.IsReady());
    Add(Full, 1); Add(Wood, 1);
    TestTrue(TEXT("Two food, a full waterskin and twenty wood are ready"), FEWVoyageProvisions::Count(Hold).IsReady());
    Entries.Reset();
    Add(Meat, 2); Add(Full, 1); Add(Kit, 1);
    TestTrue(TEXT("A repair kit stands in for the wood"), FEWVoyageProvisions::Count(Hold).IsReady());
    return true;
}
#endif
