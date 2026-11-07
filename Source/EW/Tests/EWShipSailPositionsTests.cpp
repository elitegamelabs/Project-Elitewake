#if WITH_DEV_AUTOMATION_TESTS
#include "Ships/EWShip.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipSailPositionsTest, "Elitewake.Ships.SailPositions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipSailPositionsTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Furled sail sets no area"), AEWShip::SailFractionForState(EEWSailState::Furled), 0.f);
    TestEqual(TEXT("Quarter sail sets one quarter"), AEWShip::SailFractionForState(EEWSailState::Quarter), .25f);
    TestEqual(TEXT("Half sail sets one half"), AEWShip::SailFractionForState(EEWSailState::Half), .5f);
    TestEqual(TEXT("Three-quarter sail sets three quarters"), AEWShip::SailFractionForState(EEWSailState::ThreeQuarter), .75f);
    TestEqual(TEXT("Full sail sets all sail"), AEWShip::SailFractionForState(EEWSailState::Full), 1.f);
    return true;
}
#endif
