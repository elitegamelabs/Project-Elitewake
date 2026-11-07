#include "Misc/AutomationTest.h"
#include "Characters/EWAppearance.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWAppearanceTest, "Elitewake.Characters.Appearance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FEWAppearanceTest::RunTest(const FString& Parameters)
{
    UEWBodyRoster* Roster = NewObject<UEWBodyRoster>();
    Roster->Bodies.SetNum(2);
    Roster->Tones = {FLinearColor(.7f, .5f, .4f), FLinearColor(.5f, .3f, .2f), FLinearColor(.1f, .05f, .03f)};

    // A look saved before the sliders comes back with every slider, in the colouring it chose.
    FEWAppearance Old;
    Old.Body = 1;
    Old.Tone = 2;
    Old.Height = 1.04f;
    const FEWAppearance Upgraded = Old.Clamped(Roster);
    TestEqual(TEXT("every slider but height is stored"), Upgraded.Features.Num(), FEWAppearance::Sliders().Num() - 1);
    TestEqual(TEXT("every list has a pick"), Upgraded.Picks.Num(), FEWAppearance::Choices().Num());
    TestTrue(TEXT("the old colouring becomes the skin tone"), FMath::IsNearlyEqual(Upgraded.GetSlider(FEWAppearance::SliderIndex(TEXT("SkinTone"))), 1.f, .01f));
    TestTrue(TEXT("the old height is kept"), FMath::IsNearlyEqual(Upgraded.Height, 1.04f));
    TestTrue(TEXT("the skin colour is the roster's deepest"), Upgraded.SkinColour(Roster).Equals(Roster->Tones[2] * FLinearColor(1, 1, 1, 1), .02f));

    // A bad request is brought within what is offered.
    FEWAppearance Bad;
    Bad.Body = 9;
    Bad.Height = 7.f;
    Bad.Features.Init(255, 3);
    Bad.Picks.Init(250, FEWAppearance::Choices().Num() + 4);
    for (int32 I = 0; I < 9; ++I) Bad.Tattoos.Add(FEWTattoo{static_cast<uint8>(1 + I % 3), 200, 128, 128, 99});
    const FEWAppearance Fixed = Bad.Clamped(Roster);
    TestEqual(TEXT("body within the roster"), int32(Fixed.Body), 1);
    TestTrue(TEXT("height within its range"), FMath::IsNearlyEqual(Fixed.Height, FEWAppearance::MaxHeight));
    TestEqual(TEXT("sliders padded to the full set"), Fixed.Features.Num(), FEWAppearance::Sliders().Num() - 1);
    TestEqual(TEXT("picks trimmed to the lists"), Fixed.Picks.Num(), FEWAppearance::Choices().Num());
    bool bPicksValid = true;
    for (int32 C = 0; C < Fixed.Picks.Num(); ++C) bPicksValid &= Fixed.Picks[C] < FEWAppearance::Choices()[C].Options.Num();
    TestTrue(TEXT("every pick is an offered option"), bPicksValid);
    TestEqual(TEXT("at most six tattoos"), Fixed.Tattoos.Num(), FEWAppearance::MaxTattoos);
    TestTrue(TEXT("tattoo place and ink within the lists"), Fixed.Tattoos[0].Place < FEWAppearance::TattooPlaces().Num() && Fixed.Tattoos[0].Ink < FEWAppearance::TattooInks().Num());

    // Sliders round-trip; presets repeat exactly.
    FEWAppearance Look;
    Look.SetSlider(0, 1.f);
    TestTrue(TEXT("height slider at its top is the tallest"), FMath::IsNearlyEqual(Look.Height, FEWAppearance::MaxHeight));
    const int32 Nose = FEWAppearance::SliderIndex(TEXT("NoseWidth"));
    Look.SetSlider(Nose, .25f);
    TestTrue(TEXT("a face slider keeps its value"), FMath::IsNearlyEqual(Look.GetSlider(Nose), .25f, .005f));
    FEWAppearance A, B;
    A.Body = B.Body = 1;
    A.ApplyPreset(3);
    B.ApplyPreset(3);
    TestTrue(TEXT("a preset gives the same look every time"), A == B);
    TestEqual(TEXT("a woman's preset has no beard"), A.GetPick(FEWAppearance::ChoiceIndex(TEXT("FacialHair"))), 0);
    TestTrue(TEXT("more than seventy features are offered"), FEWAppearance::Sliders().Num() + FEWAppearance::Choices().Num() > 70);
    return true;
}

#endif
