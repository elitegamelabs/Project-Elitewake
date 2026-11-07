// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "EWGraphicsSettings.h"
#include "HAL/IConsoleManager.h"
#include "Scalability.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWGraphicsTiersAreFairTest, "Elitewake.Graphics.TiersAreFair",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWGraphicsTiersAreFairTest::RunTest(const FString& Parameters)
{
    // CLAUDE.md 9.6 (owner, November 1): a better graphics card shows better visuals, never more of the world. What can hide a
    // survivor reads the same at every level: grass and plant density and the distance things are drawn to.
    const Scalability::FQualityLevels Before = Scalability::GetQualityLevels();
    for (int32 Level = 0; Level < FEWGraphicsSettings::Levels; ++Level)
    {
        Scalability::FQualityLevels Tier;
        Tier.SetFromSingleQualityLevel(Level);
        Scalability::SetQualityLevels(Tier, true);
        for (const TCHAR* Name : {TEXT("r.ViewDistanceScale"), TEXT("foliage.DensityScale"), TEXT("grass.DensityScale")})
        {
            const IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name);
            if (!Variable) continue;      // a variable this build does not have cannot differ between tiers
            TestEqual(FString::Printf(TEXT("%s at %s"), Name, *FEWGraphicsSettings::LevelName(Level).ToString()), Variable->GetFloat(), 1.f, .001f);
        }
    }
    Scalability::SetQualityLevels(Before, true);

    TestEqual(TEXT("Levels are named Low to Epic"), FEWGraphicsSettings::LevelName(0).ToString(), FString(TEXT("Low")));
    TestEqual(TEXT("...Epic"), FEWGraphicsSettings::LevelName(3).ToString(), FString(TEXT("Epic")));
    TestEqual(TEXT("A mix is Custom"), FEWGraphicsSettings::LevelName(INDEX_NONE).ToString(), FString(TEXT("Custom")));
    return true;
}
#endif
