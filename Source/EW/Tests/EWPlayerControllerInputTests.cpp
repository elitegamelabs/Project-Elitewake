#if WITH_DEV_AUTOMATION_TESTS
#include "EWPlayerController.h"
#include "Misc/AutomationTest.h"

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

    const FKey FaceKeys[] = { EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Left,
        EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Top };
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
    return true;
}
#endif
