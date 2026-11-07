#include "Ships/EWShip.h"
#include "Misc/AutomationTest.h"

// CLAUDE.md 7.4 (November 7): hired gunners lead a moving target. A ball laid on AEWShip::LeadMark and launched at the muzzle
// speed plus the firing ship's own way meets the target where she is when it arrives.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCannonLeadTest, "Elitewake.Ships.CannonLead",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWCannonLeadTest::RunTest(const FString& Parameters)
{
    const float Muzzle = AEWShip::CannonMuzzleSpeed;
    struct FCase { FVector Mark, TargetVelocity, OwnVelocity; };
    const FCase Cases[] = {
        {FVector(4000, 0, 100), FVector(0, 600, 0), FVector::ZeroVector},          // crossing at 6 m/s, 40 m off
        {FVector(12000, 3000, 100), FVector(-400, 500, 0), FVector(500, 0, 0)},    // both under way
        {FVector(8000, 0, 100), FVector::ZeroVector, FVector::ZeroVector},         // at rest: no lead
    };
    for (const FCase& Case : Cases)
    {
        const FVector From = FVector::ZeroVector;
        const FVector Lead = AEWShip::LeadMark(Case.Mark, From, Case.TargetVelocity, Case.OwnVelocity, Muzzle);
        const FVector Launch = (Lead - From).GetSafeNormal() * Muzzle + Case.OwnVelocity;
        // Closest approach of ball and target over the flight.
        float Best = TNumericLimits<float>::Max();
        for (float T = 0.f; T < 5.f; T += .001f)
            Best = FMath::Min(Best, FVector::Dist(From + Launch * T, Case.Mark + Case.TargetVelocity * T));
        TestTrue(FString::Printf(TEXT("the ball meets the target (miss %.1f cm)"), Best), Best < 25.f);
        if (Case.TargetVelocity.IsNearlyZero() && Case.OwnVelocity.IsNearlyZero())
            TestTrue(TEXT("a target at rest needs no lead"), Lead.Equals(Case.Mark, .01f));
        else
            TestTrue(TEXT("a moving target is led"), !Lead.Equals(Case.Mark, 10.f));
    }
    return true;
}
