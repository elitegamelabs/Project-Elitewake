#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalExhaustionTest,"Elitewake.Survival.ExhaustionNotification",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalExhaustionTest::RunTest(const FString& Parameters)
{
    auto* Unowned=NewObject<UEWSurvivalComponent>();
    Unowned->UpdateStamina(true,10.f);
    TestEqual(TEXT("No owner cannot drain stamina"),Unowned->GetStamina(),100.f);
    TestEqual(TEXT("No owner cannot emit exhaustion"),Unowned->GetStaminaExhaustionCount(),0);
    auto* Owner=NewObject<AActor>();
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    Survival->UpdateStamina(true,1.f);
    TestEqual(TEXT("Partial drain does not emit exhaustion"),Survival->GetStaminaExhaustionCount(),0);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Empty transition emits one retained event"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Persistent empty does not replay event"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(false,.5f);
    TestTrue(TEXT("Recovery restores positive stamina"),Survival->GetStamina()>0.f);
    TestEqual(TEXT("Event survives recovery before replication"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Next exhaustion emits a new event"),Survival->GetStaminaExhaustionCount(),2);
    return true;
}
#endif
