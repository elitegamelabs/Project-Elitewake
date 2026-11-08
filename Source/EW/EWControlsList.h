#pragma once

#include "CoreMinimal.h"

/**
 * Every control, for the Options' Controls page (owner, November 7: all the controls, shown for the input in use).
 * Read from the game's real bindings: IMC_Default (move, look, jump, sprint, stance, camera), AEWPlayerController's runtime
 * mappings and key handling (attack, punches, interact, inventory, map, pause, hotbar, ladders, sails, cannon marks, F9, F10,
 * Shift teleports) and UEWBuildComponent::ResolveKey (Build Mode). Controller text uses [Key] tokens that
 * FEWControllerIcons::Expand names for the connected pad (Xbox or PlayStation). Change this list with the bindings.
 */
namespace EWControls
{
struct FControl
{
    const TCHAR* Section;       // set on the first row of a section
    const TCHAR* Action;
    const TCHAR* Keyboard;
    const TCHAR* Controller;
};

inline const FControl List[] = {
    {TEXT("ON FOOT"), TEXT("Move"), TEXT("W A S D (or the arrow keys)"), TEXT("[Gamepad_Left2D]")},
    {nullptr, TEXT("Look around"), TEXT("Mouse"), TEXT("[Gamepad_Right2D]")},
    {nullptr, TEXT("Jump / swim up"), TEXT("Space"), TEXT("[Gamepad_FaceButton_Bottom]")},
    {nullptr, TEXT("Sprint"), TEXT("Hold Left Shift"), TEXT("Hold or click [Gamepad_LeftThumbstick]")},
    {nullptr, TEXT("Crouch (hold to lie prone)"), TEXT("C"), TEXT("[Gamepad_FaceButton_Right]")},
    {nullptr, TEXT("First / third person"), TEXT("Z"), TEXT("Keyboard Z")},
    {nullptr, TEXT("Use what is in hand"), TEXT("Left mouse"), TEXT("[Gamepad_RightTrigger]")},
    {nullptr, TEXT("Punch left / right (bare hands)"), TEXT("Left mouse / Right mouse"), TEXT("[Gamepad_LeftTrigger] / [Gamepad_RightTrigger]")},
    {nullptr, TEXT("Interact (hold for fittings and the anchor)"), TEXT("E"), TEXT("[Gamepad_FaceButton_Left]")},
    {nullptr, TEXT("Climb a ladder up / down"), TEXT("Up / Down arrows"), TEXT("[Gamepad_DPad_Up] / [Gamepad_DPad_Down]")},

    {TEXT("ITEMS AND MENUS"), TEXT("Hotbar slots 1-4"), TEXT("1 2 3 4"), TEXT("[Gamepad_DPad_Left] [Gamepad_DPad_Up] [Gamepad_DPad_Right] [Gamepad_DPad_Down]")},
    {nullptr, TEXT("Hotbar slots 5-8"), TEXT("5 6 7 8"), TEXT("[Gamepad_LeftShoulder] + [Gamepad_FaceButton_Left] [Gamepad_FaceButton_Top] [Gamepad_FaceButton_Right] [Gamepad_FaceButton_Bottom]")},
    {nullptr, TEXT("Inventory, crafting, skills and journal"), TEXT("I"), TEXT("[Gamepad_FaceButton_Top]")},
    {nullptr, TEXT("Next / previous menu tab"), TEXT("Tab / Shift + Tab"), TEXT("[Gamepad_RightShoulder] / [Gamepad_LeftShoulder]")},
    {nullptr, TEXT("Map (open / close)"), TEXT("M"), TEXT("[Gamepad_Special_Left]")},
    {nullptr, TEXT("Map: move / zoom"), TEXT("Drag / mouse wheel"), TEXT("[Gamepad_Right2D] / [Gamepad_LeftTrigger] [Gamepad_RightTrigger]")},
    {nullptr, TEXT("Pause and Options"), TEXT("Escape"), TEXT("[Gamepad_Special_Right]")},
    {nullptr, TEXT("Menus: choose / confirm / back"), TEXT("Arrows / Enter / Escape"), TEXT("[Gamepad_DPad_Up] [Gamepad_DPad_Down] / [Gamepad_FaceButton_Bottom] / [Gamepad_FaceButton_Right]")},

    {TEXT("SHIPS"), TEXT("Take the helm, work a station"), TEXT("E"), TEXT("[Gamepad_FaceButton_Left]")},
    {nullptr, TEXT("Steer"), TEXT("A / D"), TEXT("[Gamepad_Left2D]")},
    {nullptr, TEXT("Raise / lower crewed sails (hold)"), TEXT("Up / Down arrows"), TEXT("[Gamepad_DPad_Up] / [Gamepad_DPad_Down]")},
    {nullptr, TEXT("Swing the sails"), TEXT("Left / Right arrows"), TEXT("[Gamepad_LeftShoulder] / [Gamepad_RightShoulder]")},
    {nullptr, TEXT("Cannon: aim / fire"), TEXT("Mouse / Left mouse"), TEXT("[Gamepad_Right2D] / [Gamepad_RightTrigger]")},
    {nullptr, TEXT("Cannon: mark a ship for the gunners"), TEXT("Right mouse"), TEXT("[Gamepad_LeftShoulder]")},

    {TEXT("BUILD MODE"), TEXT("Enter / leave Build Mode"), TEXT("B"), TEXT("[Gamepad_LeftShoulder] + [Gamepad_DPad_Right]")},
    {nullptr, TEXT("Piece wheel"), TEXT("Tab"), TEXT("[Gamepad_FaceButton_Top]")},
    {nullptr, TEXT("Doors and windows wheel"), TEXT("F"), TEXT("[Gamepad_FaceButton_Left]")},
    {nullptr, TEXT("Place"), TEXT("Left mouse"), TEXT("[Gamepad_RightTrigger] or [Gamepad_FaceButton_Bottom]")},
    {nullptr, TEXT("Turn the piece"), TEXT("Q / E"), TEXT("[Gamepad_DPad_Left] / [Gamepad_DPad_Right]")},
    {nullptr, TEXT("Next / previous material"), TEXT("C / Z"), TEXT("[Gamepad_RightShoulder] / [Gamepad_LeftShoulder] + [Gamepad_RightShoulder]")},
    {nullptr, TEXT("Next / previous design"), TEXT("R"), TEXT("[Gamepad_DPad_Up] / [Gamepad_DPad_Down]")},
    {nullptr, TEXT("Demolish"), TEXT("X"), TEXT("[Gamepad_RightThumbstick]")},
    {nullptr, TEXT("Close a wheel"), TEXT("Escape"), TEXT("[Gamepad_FaceButton_Right]")},

    {TEXT("PLAYTEST KEYS"), TEXT("Host or join a game"), TEXT("F10"), TEXT("Keyboard F10")},
    {nullptr, TEXT("Item spawner (testing only)"), TEXT("F9"), TEXT("Keyboard F9")},
    {nullptr, TEXT("Jump to a region / nearest Port (testing only)"), TEXT("Shift + 1-5 / Shift + 6"), TEXT("Keyboard only")},
};
inline constexpr int32 Count = UE_ARRAY_COUNT(List);
}
