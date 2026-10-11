#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalFiniteInputTest,"Elitewake.Survival.InvalidNumericInput",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalFiniteInputTest::RunTest(const FString& Parameters)
{
    auto* Owner=NewObject<AActor>();
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    Survival->ApplyDamage(40.f);
    Survival->UpdateStamina(true,2.f);
    Survival->SetHunger(42.f);
    Survival->SetHydration(31.f);
    Survival->SetBodyTemperature(36.f);
    Survival->SetCarriedWeight(12.f);
    const float InvalidValues[]={std::numeric_limits<float>::quiet_NaN(),
        std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity()};
    for (float Value : InvalidValues)
    {
        Survival->ApplyDamage(Value);
        Survival->RestoreHealth(Value);
        Survival->UpdateStamina(true,Value);
        Survival->UpdateStamina(false,Value);
        Survival->SetHunger(Value);
        Survival->SetHydration(Value);
        Survival->SetBodyTemperature(Value);
        Survival->SetCarriedWeight(Value);
        TestEqual(TEXT("Invalid damage/healing preserves health"),Survival->GetHealth(),60.f);
        TestEqual(TEXT("Invalid elapsed time preserves stamina"),Survival->GetStamina(),70.f);
        TestEqual(TEXT("Invalid needs preserve hunger"),Survival->GetHunger(),42.f);
        TestEqual(TEXT("Invalid needs preserve hydration"),Survival->GetHydration(),31.f);
        TestEqual(TEXT("Invalid temperature preserves temperature"),Survival->GetBodyTemperature(),36.f);
        TestEqual(TEXT("Invalid weight preserves weight"),Survival->GetCarriedWeight(),12.f);
        TestEqual(TEXT("Invalid elapsed time cannot emit exhaustion"),Survival->GetStaminaExhaustionCount(),0);
    }
    Owner->SetRole(ROLE_SimulatedProxy);
    Survival->ApplyDamage(10.f);
    Survival->RestoreHealth(10.f);
    Survival->UpdateStamina(true,1.f);
    Survival->SetHunger(5.f);
    Survival->SetHydration(5.f);
    Survival->SetBodyTemperature(5.f);
    Survival->SetCarriedWeight(5.f);
    TestEqual(TEXT("Client health calls remain unauthorized"),Survival->GetHealth(),60.f);
    TestEqual(TEXT("Client stamina call remains unauthorized"),Survival->GetStamina(),70.f);
    TestEqual(TEXT("Client hunger call remains unauthorized"),Survival->GetHunger(),42.f);
    TestEqual(TEXT("Client hydration call remains unauthorized"),Survival->GetHydration(),31.f);
    TestEqual(TEXT("Client temperature call remains unauthorized"),Survival->GetBodyTemperature(),36.f);
    TestEqual(TEXT("Client weight call remains unauthorized"),Survival->GetCarriedWeight(),12.f);
    Owner->SetRole(ROLE_Authority);
    Survival->RestoreHealth(10.f);
    TestEqual(TEXT("Finite healing still applies"),Survival->GetHealth(),70.f);
    Survival->ApplyDamage(1000.f);
    TestEqual(TEXT("Finite damage still clamps to zero"),Survival->GetHealth(),0.f);
    Survival->SetHunger(120.f);
    Survival->SetHydration(-10.f);
    Survival->SetCarriedWeight(-10.f);
    TestEqual(TEXT("Finite hunger still clamps to full"),Survival->GetHunger(),100.f);
    TestEqual(TEXT("Finite hydration still clamps to empty"),Survival->GetHydration(),0.f);
    TestEqual(TEXT("Finite negative weight still clamps to zero"),Survival->GetCarriedWeight(),0.f);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Finite elapsed time still emits exhaustion"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(false,1.f);
    TestEqual(TEXT("Finite recovery still applies"),Survival->GetStamina(),10.f);
    return true;
}
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
    Survival->SetDebuffNotice(TEXT("Injury"),FText::FromString(TEXT("Injured")),-1.f);
    TestEqual(TEXT("Condition notice added"),Survival->GetDebuffNotices().Num(),1);
    Survival->SetDebuffNotice(TEXT("Injury"),FText::FromString(TEXT("Bandaged")),-1.f);
    TestEqual(TEXT("Same effect updates rather than duplicates"),Survival->GetDebuffNotices().Num(),1);
    Owner->SetRole(ROLE_SimulatedProxy);
    Survival->ClearDebuffNotice(TEXT("Injury"));
    Survival->SetDebuffNotice(TEXT("Poison"),FText::FromString(TEXT("Poisoned")),-1.f);
    TestEqual(TEXT("Client cannot add or clear effects"),Survival->GetDebuffNotices().Num(),1);
    Owner->SetRole(ROLE_Authority);
    Survival->SetDebuffNotice(TEXT("Injury"),FText::GetEmpty(),0.f);
    TestEqual(TEXT("Authority can clear a condition"),Survival->GetDebuffNotices().Num(),0);
    return true;
}
#endif
