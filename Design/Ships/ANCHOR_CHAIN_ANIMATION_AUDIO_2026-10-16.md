# ELITEWAKE — Anchor tension, chain animation and sound
Owner request: October 16, 2026.

## Gameplay
- When a ship's anchor is down and a player attempts to move forward, retain physical movement initially as permitted by existing gameplay, then visibly take up slack in the anchor chain.
- When the chain goes taut and the anchor catches the seabed, play a clear metallic chain-rattling and heavy clank sound, with appropriate distance attenuation.
- As tension builds, resist and slow the vessel smoothly rather than abruptly freezing it. Show subtle hull/bow response, chain tension, and corresponding displaced water.
- Raising the anchor retracts chain with synchronized animation and winch/chain audio; normal sailing resumes when fully raised.
- Keep lowering, catching, dragging (if already supported), and raising states distinct. Do not invent an anchor-dragging mechanic without owner approval.
- Handle shallow/deep water, zero speed, reversing, turning, interrupted animation, and repeated helm interaction safely.

## Instructions for Claude / Codex
- Triple-check latest repo state, current ship/anchor implementation and relevant open work before editing. Reuse existing anchor mesh, constraints, animation, audio, and water systems; do not duplicate or replace existing ship controls.
- Keep the prior forward/reverse/turn water displacement and 20-meter wake compatible.
- Implement visual chain deployment/tension/retraction, realistic hull response and synchronized chain rattling, catching and retrieval sound cues in Unreal Engine 5.8.
- Validate in a playable test, including anchor down + throttle forward, catch and stop, raise and sail, and first/third person views. Distinguish documentation from completed code/assets and in-engine testing.
