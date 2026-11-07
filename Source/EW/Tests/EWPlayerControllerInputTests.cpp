#if WITH_DEV_AUTOMATION_TESTS
#include "EWPlayerController.h"
#include "Misc/AutomationTest.h"
#include "World/EWBuildComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWPlayerControllerHotbarInputTest,
    "Elitewake.Input.HotbarKeyboardAndControllerBindings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWPlayerControllerHotbarInputTest::RunTest(const FString& Parameters)
{
    const FKey KeyboardKeys[] = { EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four,
        EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight };
    for (int32 Slot = 0; Slot < UEWHotbarComponent::SlotCount; ++Slot)
    {
        TestEqual(FString::Printf(TEXT("Number key %d selects its matching slot"), Slot + 1),
            AEWPlayerController::HotbarSlotForKey(KeyboardKeys[Slot], false), Slot);
    }

    const FKey DPadKeys[] = { EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Up,
        EKeys::Gamepad_DPad_Right, EKeys::Gamepad_DPad_Down };
    for (int32 Slot = 0; Slot < UEWHotbarComponent::SlotCount / 2; ++Slot)
    {
        TestEqual(FString::Printf(TEXT("D-pad direction selects slot %d"), Slot + 1),
            AEWPlayerController::HotbarSlotForKey(DPadKeys[Slot], false), Slot);
    }

    // Owner, November 1: LB with X, Y, B, A selects slots 5, 6, 7, 8.
    const FKey FaceKeys[] = { EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_FaceButton_Top,
        EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Bottom };
    for (int32 Index = 0; Index < UEWHotbarComponent::SlotCount / 2; ++Index)
    {
        const int32 Slot = Index + UEWHotbarComponent::SlotCount / 2;
        TestEqual(FString::Printf(TEXT("LB plus face button selects slot %d"), Slot + 1),
            AEWPlayerController::HotbarSlotForKey(FaceKeys[Index], true), Slot);
        TestEqual(FString::Printf(TEXT("Face button alone does not select slot %d"), Slot + 1),
            AEWPlayerController::HotbarSlotForKey(FaceKeys[Index], false), INDEX_NONE);
    }

    TestEqual(TEXT("Unassigned key does not select a slot"),
        AEWPlayerController::HotbarSlotForKey(EKeys::M, true), INDEX_NONE);
    TestEqual(TEXT("LB with d-pad right is still slot 3 to the hotbar (Build Mode takes the chord first, on foot)"),
        AEWPlayerController::HotbarSlotForKey(EKeys::Gamepad_DPad_Right, true), 2);
    TestEqual(TEXT("The left trigger selects no slot"),
        AEWPlayerController::HotbarSlotForKey(EKeys::Gamepad_LeftTrigger, true), INDEX_NONE);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWBuildModeKeysTest,
    "Elitewake.Input.BuildModeKeys",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWBuildModeKeysTest::RunTest(const FString& Parameters)
{
    // Owner, November 1 (CLAUDE.md 6.5).
    using A = EEWBuildKeyAction;
    const auto Off = EEWBuildMode::Off, Place = EEWBuildMode::Place, Demolish = EEWBuildMode::Demolish;
    auto Is = [this](const TCHAR* What, A Got, A Want) { TestEqual(What, static_cast<int32>(Got), static_cast<int32>(Want)); };
    auto R = [](const FKey& Key, bool bLB, EEWBuildMode Mode, bool bDial, bool bPressed = true)
        { return UEWBuildComponent::ResolveKey(Key, bPressed, bLB, Mode, bDial); };

    // Entering.
    Is(TEXT("B enters"), R(EKeys::B, false, Off, false), A::Enter);
    Is(TEXT("LB + d-pad right enters"), R(EKeys::Gamepad_DPad_Right, true, Off, false), A::Enter);
    Is(TEXT("D-pad right alone is left to the hotbar"), R(EKeys::Gamepad_DPad_Right, false, Off, false), A::None);
    Is(TEXT("The right-stick click no longer enters"), R(EKeys::Gamepad_RightThumbstick, false, Off, false), A::None);
    Is(TEXT("LB alone is left to the hotbar and stations"), R(EKeys::Gamepad_LeftShoulder, false, Off, false), A::None);
    Is(TEXT("A release does not enter"), R(EKeys::B, false, Off, false, false), A::None);

    // Closing the dial and leaving.
    Is(TEXT("The B button closes the open dial"), R(EKeys::Gamepad_FaceButton_Right, false, Place, true), A::CloseDial);
    Is(TEXT("The B button again leaves"), R(EKeys::Gamepad_FaceButton_Right, false, Place, false), A::Leave);
    Is(TEXT("Escape closes the open dial"), R(EKeys::Escape, false, Place, true), A::CloseDial);
    Is(TEXT("Escape again leaves"), R(EKeys::Escape, false, Place, false), A::Leave);
    Is(TEXT("The B key leaves"), R(EKeys::B, false, Place, true), A::Leave);
    Is(TEXT("LB + d-pad right leaves"), R(EKeys::Gamepad_DPad_Right, true, Place, false), A::Leave);
    Is(TEXT("The B button leaves demolish too"), R(EKeys::Gamepad_FaceButton_Right, false, Demolish, false), A::Leave);

    // Working.
    Is(TEXT("D-pad right alone rotates"), R(EKeys::Gamepad_DPad_Right, false, Place, false), A::RotateRight);
    Is(TEXT("D-pad left rotates back"), R(EKeys::Gamepad_DPad_Left, false, Place, false), A::RotateLeft);
    Is(TEXT("LB alone does nothing here"), R(EKeys::Gamepad_LeftShoulder, false, Place, false), A::None);
    Is(TEXT("RB is the next material"), R(EKeys::Gamepad_RightShoulder, false, Place, false), A::MaterialNext);
    Is(TEXT("LB + RB is the previous material"), R(EKeys::Gamepad_RightShoulder, true, Place, false), A::MaterialPrevious);
    Is(TEXT("C is the next material"), R(EKeys::C, false, Place, false), A::MaterialNext);
    Is(TEXT("Z is the previous material"), R(EKeys::Z, false, Place, false), A::MaterialPrevious);
    Is(TEXT("R3 toggles demolish"), R(EKeys::Gamepad_RightThumbstick, false, Place, false), A::ToggleDemolish);
    Is(TEXT("X (keyboard) toggles demolish"), R(EKeys::X, false, Place, false), A::ToggleDemolish);
    Is(TEXT("Y reopens the dial"), R(EKeys::Gamepad_FaceButton_Top, false, Place, false), A::ToggleDial);
    Is(TEXT("A confirms"), R(EKeys::Gamepad_FaceButton_Bottom, false, Place, true), A::Confirm);
    Is(TEXT("A used key's release is consumed"), R(EKeys::Gamepad_FaceButton_Bottom, false, Place, true, false), A::Consume);
    return true;
}
#endif
