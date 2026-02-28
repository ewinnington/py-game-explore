# DemoBlade - Game Transformation Progress

## Overview
Transforming the mini-POC into a full game with levels, enemy types, hero mechanics, and objectives.

## Phases

### Phase 1: Hero Stats & HUD [DONE]
- [x] Add HP, MP, XP, Level stats to Player
- [x] MP costs: fire=2, ice=4, shadow=5. MP regenerates over time
- [x] Enemies deal damage to player (reduce HP, not just knockback)
- [x] XP from kills, leveling up grants more HP/MP
- [x] Bottom-of-screen HUD: HP bar, MP bar, XP bar, level, equipped weapon/spell icons
- [x] Player death state (game over or respawn)

### Phase 2: Dual Ring Menu (Secret of Mana style) [DONE]
- [x] Split circular menu into two rings: weapons + magic
- [x] UP/DOWN switches between weapon ring and magic ring
- [x] LEFT/RIGHT navigates within current ring
- [x] Start with only sword; spear & spells found as runes
- [x] Magic ring only appears once first magic rune is found
- [x] Show currently selected weapon/spell on HUD
- [x] Remove old add/remove (UP/DOWN) from menu

### Phase 3: New Enemy Types [DONE]
- [x] Bat: flying, erratic swooping, low HP (enemy_bat.py)
- [x] Centipede: multi-segment, each hit removes a segment (enemy_centipede.py)
- [x] Give enemies HP values (demon=2, bat=1, centipede segments=5)
- [x] Different XP values per enemy type (demon=5, bat=3, centipede=8)

### Phase 4: Pickup System [DONE]
- [x] Rune pickups in world (spear, fire, ice, shadow) with glow effect
- [x] Collecting rune adds item to appropriate ring menu
- [x] Health pickup (heart/potion) restores HP
- [x] Pickups placed in level with actual weapon/spell icons

### Phase 5: Game State & Level System [DONE]
- [x] Game state manager (title, gameplay, level_transition, game_over, victory)
- [x] Title screen with controls hint
- [x] 4 levels: The Meadow, Dark Woods, The Swarm, Demon's Gate
- [x] Level transition portals (appear when objective complete)
- [x] Level objectives: kill_all and kill_count types
- [x] Player carries stats/inventory between levels
- [x] Victory screen with full kill stats breakdown

### Phase 6: Kill Tracking & Objectives UI [DONE]
- [x] Kill counter per enemy type (player.kill_counts dict)
- [x] On-screen objective display with progress counter
- [x] Level name display (fades after 3s)
- [x] Game over screen with stats
- [x] Victory screen with per-type kill breakdown

## Known Bugs (to fix)
- [ ] Enemies can leave the play area (need boundary clamping)
- [ ] Knockback can push player through walls (need post-knockback collision)

### Phase 7: Sound Effects [DONE]
- [x] Procedural chiptune SFX (sword_hit, spell_cast, pickup, enemy_hit, enemy_death,
      player_hurt, level_up, portal, menu_open, menu_select)
- [x] Looping chiptune BGM (square+triangle+noise channels)
- [x] SoundManager singleton with init/play/start_bgm/stop_bgm
- [x] All sounds generated via numpy — no external audio files
- [x] Wired into: combat, pickups, portal, level transitions, menus

### Phase 8: Update Player/Game Sprites [NOT STARTED]
- [ ] Modernize player sprite to match procedural enemy quality
- [ ] Update tile/object sprites

### Phase 9: Gamepad Support [NOT STARTED]
- [ ] Logitech USB gamepad input alongside keyboard

## Current Session State
- **Working on:** Phase 8 (sprites) and Phase 9 (gamepad)
- **Last completed step:** Phase 7 - sound system complete
- **Notes:** Game fully playable with sound. Next: sprite refresh + gamepad input.
