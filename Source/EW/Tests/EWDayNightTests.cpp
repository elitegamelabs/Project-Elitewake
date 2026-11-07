// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "World/EWDayNight.h"
#include "World/EWNorth.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWDayNightClockTest, "Elitewake.World.DayNightClock",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWDayNightClockTest::RunTest(const FString& Parameters)
{
    // Owner: 90 real minutes of day and 90 of night.
    TestEqual(TEXT("Day (06:00 to 18:00) lasts 90 real minutes"), FEWSkyClock::HourAfter(6.f, 90.0 * 60.0), 18.f, .001f);
    TestEqual(TEXT("Night (18:00 to 06:00) lasts 90 real minutes"), FEWSkyClock::HourAfter(18.f, 90.0 * 60.0), 6.f, .001f);
    TestEqual(TEXT("The clock wraps past midnight"), FEWSkyClock::HourAfter(23.5f, 450.0), .5f, .001f);
    TestEqual(TEXT("A whole day and night is three real hours"), FEWSkyClock::HourAfter(8.f, 3.0 * 3600.0), 8.f, .001f);
    TestTrue(TEXT("Noon is day"), FEWSkyClock::IsDay(12.f));
    TestFalse(TEXT("Midnight is night"), FEWSkyClock::IsDay(0.f));
    TestFalse(TEXT("18:00 begins the night"), FEWSkyClock::IsDay(18.f));

    TestEqual(TEXT("The sun is on the horizon at 06:00"), FEWSkyClock::SunElevation(6.f), 0.f, .01f);
    TestEqual(TEXT("...and at 18:00"), FEWSkyClock::SunElevation(18.f), 0.f, .01f);
    TestEqual(TEXT("The sun stands highest at noon"), FEWSkyClock::SunElevation(12.f), FEWSkyClock::HighestSun, .01f);
    TestTrue(TEXT("The sun is below the horizon at midnight"), FEWSkyClock::SunElevation(0.f) < -60.f);
    TestEqual(TEXT("It rises in the east"), EWNorth::BearingOfYaw(FEWSkyClock::SunAzimuth(6.f)), 90.f, .01f);
    TestEqual(TEXT("It stands in the south at noon"), EWNorth::BearingOfYaw(FEWSkyClock::SunAzimuth(12.f)), 180.f, .01f);
    TestEqual(TEXT("It sets in the west"), EWNorth::BearingOfYaw(FEWSkyClock::SunAzimuth(18.f)), 270.f, .01f);

    // A light from the noon sun points down and toward the north (+Y); the rising sun's from the east (-X) toward +X.
    const FVector Noon = FEWSkyClock::LightRotation(FEWSkyClock::SunElevation(12.f), FEWSkyClock::SunAzimuth(12.f)).Vector();
    TestTrue(TEXT("Noon light shines downward"), Noon.Z < -.85f);
    TestTrue(TEXT("Noon light shines from the south toward the north"), Noon.Y > .3f);
    const FVector Dawn = FEWSkyClock::LightRotation(1.f, FEWSkyClock::SunAzimuth(6.f)).Vector();
    TestTrue(TEXT("Dawn light shines from the east toward the west (+X)"), Dawn.X > .9f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWNorthTest, "Elitewake.World.NorthIsPlusY",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWNorthTest::RunTest(const FString& Parameters)
{
    // Owner, November 1: Winter north (+Y), Swamp south (-Y), Desert east (-X), Jungle west (+X).
    TestEqual(TEXT("Facing +Y is north"), EWNorth::BearingOfYaw(90.f), 0.f, .01f);
    TestEqual(TEXT("Facing -X is east"), EWNorth::BearingOfYaw(180.f), 90.f, .01f);
    TestEqual(TEXT("Facing -Y is south"), EWNorth::BearingOfYaw(-90.f), 180.f, .01f);
    TestEqual(TEXT("Facing +X is west"), EWNorth::BearingOfYaw(0.f), 270.f, .01f);
    TestEqual(TEXT("A place toward -X lies east"), EWNorth::BearingOf(FVector(-1000.f, 0.f, 0.f)), 90.f, .01f);
    TestEqual(TEXT("Bearings turn back into yaw"), FMath::Abs(EWNorth::YawOfBearing(90.f)), 180.f, .01f);
    const FVector2D EN = EWNorth::EastNorth(FVector(-300.f, 200.f, 0.f));
    TestTrue(TEXT("East and north of a location"), EN.Equals(FVector2D(300.f, 200.f)));
    return true;
}
#endif
