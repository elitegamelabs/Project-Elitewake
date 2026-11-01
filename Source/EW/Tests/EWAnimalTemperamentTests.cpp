// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Wildlife/EWAnimalDefinition.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWElephantIsNeutralTest, "Elitewake.Wildlife.ElephantIsNeutral",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWElephantIsNeutralTest::RunTest(const FString& Parameters)
{
    // Owner, November 1: elephants never attack unprovoked, and defend themselves when attacked instead of fleeing.
    const UEWAnimalDefinition* Elephant = LoadObject<UEWAnimalDefinition>(nullptr,
        TEXT("/Game/Elitewake/Wildlife/Animals/DA_Animal_Elephant.DA_Animal_Elephant"));
    if (!TestNotNull(TEXT("The elephant's definition loads"), Elephant)) return false;
    TestFalse(TEXT("It does not go for survivors who come near"), Elephant->bAggressive);
    TestTrue(TEXT("It defends itself when struck"), Elephant->bDefendsItself);
    TestTrue(TEXT("It has an attack to defend itself with"), Elephant->AttackDamage > 0.f && Elephant->AttackReach > 0.f && Elephant->AttackInterval > 0.f);
    TestTrue(TEXT("It calms down in time"), Elephant->DefendSeconds > 0.f && Elephant->DefendGiveUpRange > 0.f);
    return true;
}
#endif
