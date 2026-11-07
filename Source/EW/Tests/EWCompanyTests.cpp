#include "EWCompanyComponent.h"
#include "Misc/AutomationTest.h"
#include <limits>
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCompanyNameTest,"Elitewake.Company.NameValidation",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWCompanyNameTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Pirate names allow apostrophes and hyphens"),UEWCompanyComponent::IsValidCompanyName(TEXT("Captain's Sea-Wolves")));
    TestFalse(TEXT("Whitespace-only rejected"),UEWCompanyComponent::IsValidCompanyName(TEXT("   ")));
    TestFalse(TEXT("Newline rejected"),UEWCompanyComponent::IsValidCompanyName(TEXT("Sea\nWolves")));
    TestFalse(TEXT("Markup rejected"),UEWCompanyComponent::IsValidCompanyName(TEXT("<Owner>")));
    TestFalse(TEXT("Oversized name rejected"),UEWCompanyComponent::IsValidCompanyName(FString::ChrN(33,'A')));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCompanyCapTest,"Elitewake.Company.TameCapBoundaries",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWCompanyCapTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Exact personal/company limits allowed"),UEWCompanyComponent::FitsTameCaps(24,74,1));
    TestFalse(TEXT("Personal overflow rejected"),UEWCompanyComponent::FitsTameCaps(25,74,1));
    TestFalse(TEXT("Company overflow rejected even with personal room"),UEWCompanyComponent::FitsTameCaps(1,75,1));
    TestFalse(TEXT("Overflow-sized addition rejected"),UEWCompanyComponent::FitsTameCaps(0,0,std::numeric_limits<int32>::max()));
    TestFalse(TEXT("Negative counts rejected"),UEWCompanyComponent::FitsTameCaps(-1,1,1));
    TestFalse(TEXT("Nonpositive addition rejected"),UEWCompanyComponent::FitsTameCaps(0,0,0));
    return true;
}
#endif
