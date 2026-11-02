#if WITH_DEV_AUTOMATION_TESTS
#include "EWControllerIcons.h"
#include "EWArrivalComponent.h"
#include "EWHotbarWidget.h"
#include "Engine/Texture2D.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWControllerFamilyTest,
    "Elitewake.Input.ControllerFamilyAndButtonNames",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWControllerFamilyTest::RunTest(const FString& Parameters)
{
    using F = EEWGamepadFamily;
    // Owner, November 1: an Xbox or PlayStation pad shows its own buttons.
    TestTrue(TEXT("A Sony pad is PlayStation"), FEWControllerIcons::FamilyForVendor(0x054C, false) == F::PlayStation);
    TestTrue(TEXT("A Microsoft pad is Xbox"), FEWControllerIcons::FamilyForVendor(0x045E, false) == F::Xbox);
    TestTrue(TEXT("Any XInput pad is the Xbox layout"), FEWControllerIcons::FamilyForVendor(0x24C6, true) == F::Xbox);
    TestTrue(TEXT("Another maker's non-XInput pad is unknown"), FEWControllerIcons::FamilyForVendor(0x057E, false) == F::Unknown);
    TestTrue(TEXT("Nothing connected is unknown"), FEWControllerIcons::FamilyOfPads({}) == F::Unknown);
    TestTrue(TEXT("A PlayStation pad seen beside its virtual Xbox twin (DS4Windows, Steam) is PlayStation"), FEWControllerIcons::FamilyOfPads({F::Xbox, F::PlayStation}) == F::PlayStation);
    TestTrue(TEXT("Xbox beside an unknown pad is Xbox"), FEWControllerIcons::FamilyOfPads({F::Unknown, F::Xbox}) == F::Xbox);
    TestTrue(TEXT("Automatic follows the pad"), FEWControllerIcons::Resolve(EEWButtonIconsChoice::Automatic, F::PlayStation) == F::PlayStation);
    TestTrue(TEXT("The Options choice wins"), FEWControllerIcons::Resolve(EEWButtonIconsChoice::Xbox, F::PlayStation) == F::Xbox);
    TestTrue(TEXT("PlayStation can be chosen with nothing connected"), FEWControllerIcons::Resolve(EEWButtonIconsChoice::PlayStation, F::Unknown) == F::PlayStation);

    // Buttons are by position: the same key is X on one pad and Square on the other, never mixed.
    const FKey Face[] = {EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_FaceButton_Top};
    const TCHAR* Xbox[] = {TEXT("A"), TEXT("B"), TEXT("X"), TEXT("Y")};
    const TCHAR* PlayStation[] = {TEXT("Cross"), TEXT("Circle"), TEXT("Square"), TEXT("Triangle")};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        TestEqual(TEXT("Xbox face name"), FEWControllerIcons::ButtonName(Face[Index], F::Xbox), FString(Xbox[Index]));
        TestEqual(TEXT("PlayStation face name"), FEWControllerIcons::ButtonName(Face[Index], F::PlayStation), FString(PlayStation[Index]));
        TestEqual(TEXT("Xbox face icon"), FEWControllerIcons::IconName(Face[Index], F::Xbox), FString::Printf(TEXT("T_Icon_Xbox_%s"), Xbox[Index]));
        TestEqual(TEXT("PlayStation face icon"), FEWControllerIcons::IconName(Face[Index], F::PlayStation),
            FString::Printf(TEXT("T_Icon_PlayStation_%s"), PlayStation[Index]));
    }
    TestEqual(TEXT("LB is L1"), FEWControllerIcons::ButtonName(EKeys::Gamepad_LeftShoulder, F::PlayStation), FString(TEXT("L1")));
    TestEqual(TEXT("R3 is RS on Xbox"), FEWControllerIcons::ButtonName(EKeys::Gamepad_RightThumbstick, F::Xbox), FString(TEXT("RS")));
    TestEqual(TEXT("An unknown pad gets words"), FEWControllerIcons::ButtonName(EKeys::Gamepad_FaceButton_Left, F::Unknown), FString(TEXT("Left button")));
    TestTrue(TEXT("An unknown pad has no icon"), FEWControllerIcons::IconName(EKeys::Gamepad_FaceButton_Left, F::Unknown).IsEmpty());

    // Tokens in prompt text.
    const FString Words = TEXT("[Gamepad_FaceButton_Left]: drink");
    TestEqual(TEXT("Xbox words"), FEWControllerIcons::Expand(Words, F::Xbox, false), FString(TEXT("X: drink")));
    TestEqual(TEXT("PlayStation words"), FEWControllerIcons::Expand(Words, F::PlayStation, false), FString(TEXT("Square: drink")));
    TestEqual(TEXT("Unknown words"), FEWControllerIcons::Expand(Words, F::Unknown, false), FString(TEXT("Left button: drink")));
    TestEqual(TEXT("Text without tokens is untouched"), FEWControllerIcons::Expand(FString(TEXT("E: [drink]")), F::Xbox, true), FString(TEXT("E: [drink]")));
    TestEqual(TEXT("The build hint on a PlayStation pad"), FEWControllerIcons::Expand(UEWHotbarWidget::BuildHintText(true), F::PlayStation, false),
        FString(TEXT("Build: hold L1 + D-pad Right")));
    TestEqual(TEXT("The build hint on an Xbox pad"), FEWControllerIcons::Expand(UEWHotbarWidget::BuildHintText(true), F::Xbox, false),
        FString(TEXT("Build: hold LB + D-pad Right")));
    TestEqual(TEXT("The build hint on the keyboard"), UEWHotbarWidget::BuildHintText(false), FString(TEXT("Build: B")));
    for (int32 Step = 0; Step < int32(EEWArrivalStep::Done); ++Step)
    {
        const FString Pad = UEWArrivalComponent::PromptFor(EEWArrivalStep(Step), true).ToString();
        TestFalse(TEXT("No arrival prompt names an Xbox letter outright"), Pad.StartsWith(TEXT("A:")) || Pad.StartsWith(TEXT("B:")) || Pad.StartsWith(TEXT("X:")));
        TestFalse(TEXT("Every token is a known button"), FEWControllerIcons::Expand(Pad, F::PlayStation, false).Contains(TEXT("[Gamepad_")));
    }

    // The icons themselves (imported by Scripts/Setup/import_controller_icons.py): every button the game names has both.
    const FKey Named[] = {EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_FaceButton_Top,
        EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Down, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_LeftShoulder,
        EKeys::Gamepad_RightShoulder, EKeys::Gamepad_LeftTrigger, EKeys::Gamepad_RightTrigger, EKeys::Gamepad_LeftThumbstick, EKeys::Gamepad_RightThumbstick,
        EKeys::Gamepad_Left2D, EKeys::Gamepad_Right2D, EKeys::Gamepad_Special_Left, EKeys::Gamepad_Special_Right};
    for (const FKey& Key : Named)
        for (const F Family : {F::Xbox, F::PlayStation})
            TestNotNull(*FString::Printf(TEXT("%s icon for %s"), FEWControllerIcons::FamilyName(Family), *Key.ToString()), FEWControllerIcons::IconFor(Key, Family));
    return true;
}
#endif
