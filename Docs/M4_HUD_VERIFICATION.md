# M4 survival HUD return slice

Reviewed 2026-10-06, active `C:\UnrealProjects\EW`, Unreal 5.8.3.

## Scope

The local controller creates a read-only survival HUD above the existing hotbar. Five labeled gauges show health/current maximum, stamina/current maximum, normalized food and hydration percentages, and inventory-plus-equipment carried weight/current prototype capacity. The widget reads only its possessed character's survival component, clears stale information while unpossessed, and resumes with current values on possession. It does not intercept gameplay input or mutate stats. Inventory still overlays the HUD and the world stays live.

Bible §§5.6 and 30.15 supply the presentation requirements. Empty food blinks red, hydration yellow and stamina white. Their top-center messages are “You are hungry!”, “You are thirsty!” and “You are out of stamina!” for 1.5 seconds on a new empty transition. Independent warnings can coexist. Warning duration continues during replenishment/recovery; persistent empty values keep blinking without repeating the notice every frame. Blink period is draft presentation tuning.

This slice displays existing gameplay truth. It does not implement 15-minute needs drain, starvation/dehydration damage, food/drinking, jump/climb costs, five-second stamina tuning, natural health regeneration, fall damage or condition/ship HUD systems. Food is currently a normalized 0–100 percentage, not the Bible's upgradeable 75-point base capacity. The displayed 50 kg carry capacity remains a prototype value and does not imply an enforced hard cap or encumbrance penalty.

Direct owner clarification on October 6: stamina recovery should also occur while walking. This supersedes the stationary-only recovery description for the next gameplay pass; the existing walking recovery already behaves that way. Capacity scaling and needs-damage tuning remain separate decisions.

## Verification

- Final EWEditor Win64 Development build succeeds. `Saved/Logs/M4HUDFinalRegression.log` records nine successful automation tests: the eight existing animation/stance/inventory/pickup/equipment/hotbar checks and new `Elitewake.Survival.ExhaustionNotification`.
- ExhaustionNotification proves that partial drain emits no exhaustion, the first empty transition emits once, remaining empty does not replay it, the marker survives recovery before replication and a later exhaustion emits a new marker. The marker is authority-produced, owner-only replicated and does not alter survival rates. It prevents the owning HUD from missing an intermediate zero stamina value when replication arrives after recovery begins.
- `Scripts/verify_survival_hud_play.py` passes 20 standalone and 20 owning-client checkpoints on the final build. These read the rendered widget labels after authority changes, including damage/restore, food/hydration values, independent and simultaneous warnings, warning expiry/retrigger, inventory-plus-equipment weight, inventory overlay/input lock, above-capacity display and same-pawn unpossession/repossession. The other survivor stays unchanged.
- Real Shift input drains stamina through the existing gameplay loop and produces the exhaustion warning. Measured notice duration is approximately 1.50 seconds standalone and 1.51 seconds on the client, continuing through automatic recovery. This verifies presentation at the existing rates, not the future five-second rate tuning.
- Network Play uses a local listen server and client with 100 ms outgoing packet lag and 1% loss on both drivers. `Saved/M4HUDPlayResult.json` and `Saved/M4HUDNetworkResult.json` retain results. The possession probe can emit movement saved-move/timestamp warnings during the temporary detach under packet emulation; it is not full respawn or moving-deck validation.
- All 42 existing network hotbar checkpoints pass with the survival HUD visible, including keyboard/controller chords, ordinary gameplay roles, inventory assignment and focus reset. Final standalone and client screenshots confirm readable gauges above the hotbar; simultaneous red food/yellow hydration notices appear at top center without overlap.

The verification script restores packet/throttle/input/panel settings and removes its callback. Saved Wood/Hat fixtures remain opt-in and no production assets/default grants are changed. Logs, reports and screenshots are local evidence rather than tracked assets.

## Remaining gates

Final HUD art, controller hardware, packaged/dedicated-server checks, complete survival gameplay and condition/interaction/ship displays remain open. M4 is partially implemented; this presentation slice does not mark the whole milestone complete.
