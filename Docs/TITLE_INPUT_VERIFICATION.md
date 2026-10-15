# Title-screen input correction

The October 13 demo could display its title art without accepting input. The native title widget configured keyboard focusability in `NativeConstruct`, after Slate construction, and had no explicit full-screen mouse hit target. The correction configures focusability and visible hit testing in `RebuildWidget`, adds a transparent root, and establishes player focus after viewport insertion.

`Elitewake.Title.RoutedKeyboardMouseAndWheel` passed in a rendering offscreen Unreal editor. It routes events through Slate focus and mouse hit testing rather than calling the transition functions. Seven fresh splash scenarios cover a keyboard key, left/right/middle/side mouse buttons, and wheel movement in both directions. Each reaches the menu without starting gameplay. In the menu, keyboard, wheel, middle-click and clicks on Multiplayer do not start gameplay; left/right clicks inside Single Player invoke its start delegate.

Evidence: `Saved/Logs/TitleInputRegression.log` and `Saved/TitleInputRegression/index.json`. The existing title-to-coast check invokes transitions directly and verifies map travel; it is not evidence of input routing.

The replacement demo uses the previously released `demo-20261013-surf-menu` source snapshot plus the input correction. Unfinished local ship and gameplay edits are excluded. Broader development remains paused in this workflow.

The encrypted Shipping build and single-EXE archive integrity passed. The isolated snapshot's title-to-coast Play check also passed. The maintained project check, `Scripts/Verification/verify_title_play.py`, passed 3 of 3 in Standalone at 1280×720 on October 15: title art and prompt loaded, Enter opened the menu, the Single Player panel occupied its expected bounds, and Single Player opened the coastal map with the regular survivor. This Play check invokes the Single Player start delegate for map travel; the separate Slate input automation verifies routed pointer clicks. No saved survivor existed during the run. Release evidence is under `Saved/PrivateBuilds/demo-20261013-title-input-fix/`.
