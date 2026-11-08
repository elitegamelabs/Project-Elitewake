#if WITH_DEV_AUTOMATION_TESTS
#include "Ships/EWShip.h"
#include "Misc/AutomationTest.h"

// Ship names (FUTURE_IMPLEMENTATIONS Part 8, 12): the rules a proposed name must pass before the harbour registers it.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipNameRulesTest, "Elitewake.Ships.NameRules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWShipNameRulesTest::RunTest(const FString& Parameters)
{
    FString Name;
    FText Reason;
    TestTrue(TEXT("a plain name passes"), AEWShip::CleanShipName(TEXT("Good Hope"), Name, Reason));
    TestEqual(TEXT("unchanged"), Name, FString(TEXT("Good Hope")));
    TestTrue(TEXT("spaces tidied"), AEWShip::CleanShipName(TEXT("   Swift    Return  "), Name, Reason));
    TestEqual(TEXT("one space between words"), Name, FString(TEXT("Swift Return")));
    TestTrue(TEXT("period punctuation and digits pass"), AEWShip::CleanShipName(TEXT("St. Anne's Hope-2"), Name, Reason));
    TestFalse(TEXT("one letter is too short"), AEWShip::CleanShipName(TEXT("A"), Name, Reason));
    TestFalse(TEXT("empty refused"), AEWShip::CleanShipName(TEXT("    "), Name, Reason));
    TestFalse(TEXT("too long refused"), AEWShip::CleanShipName(FString::ChrN(AEWShip::MaxNameLength + 1, TEXT('a')), Name, Reason));
    TestTrue(TEXT("exactly the longest passes"), AEWShip::CleanShipName(FString::ChrN(AEWShip::MaxNameLength, TEXT('a')), Name, Reason));
    TestFalse(TEXT("symbols refused"), AEWShip::CleanShipName(TEXT("Hope <b>"), Name, Reason));
    TestFalse(TEXT("digits alone refused"), AEWShip::CleanShipName(TEXT("1234"), Name, Reason));
    // Moderation reads [/Script/EW.EWShip] BlockedNameWords from the game config, ignoring case, spaces and punctuation.
    TestFalse(TEXT("blocked word refused"), AEWShip::CleanShipName(TEXT("Hitler"), Name, Reason));
    TestFalse(TEXT("blocked word hidden by spacing refused"), AEWShip::CleanShipName(TEXT("Na. Zi"), Name, Reason));
    TestTrue(TEXT("a period word that only resembles one passes"), AEWShip::CleanShipName(TEXT("Grapeshot"), Name, Reason));
    // Suggestions are names that pass.
    for (int32 Seed = 0; Seed < 20; ++Seed)
        TestTrue(TEXT("a suggested name passes"), AEWShip::CleanShipName(AEWShip::SuggestName(nullptr, Seed), Name, Reason));
    return true;
}
#endif
