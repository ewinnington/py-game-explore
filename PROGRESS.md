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
- [x] Enemies can leave the play area → added world boundary clamping to all enemy types
- [x] Knockback can push player through walls → multi-step knockback + world boundary clamp

### Phase 7: Sound Effects [DONE]
- [x] Procedural chiptune SFX (sword_hit, spell_cast, pickup, enemy_hit, enemy_death,
      player_hurt, level_up, portal, menu_open, menu_select)
- [x] Looping chiptune BGM (square+triangle+noise channels)
- [x] SoundManager singleton with init/play/start_bgm/stop_bgm
- [x] All sounds generated via numpy — no external audio files
- [x] Wired into: combat, pickups, portal, level transitions, menus

### Phase 8: Update Player/Game Sprites [DONE]
- [x] Created player_sprite.py with procedural hero sprite generation (64x64)
- [x] 4 walk frames per direction, idle, and attack animations with sword slash
- [x] Heroic warrior design: blue tunic, red cape, brown hair, boots, belt
- [x] Integrated into player.py (replaces disk-based sprite loading)

### Phase 9: Gamepad Support [DONE]
- [x] Auto-detect first USB gamepad
- [x] Left stick + D-pad for movement
- [x] Button A: attack, B: magic, X: menu, Y: select
- [x] L1/R1: navigate ring menu left/right
- [x] Stick up/down: switch weapon/magic ring in menu
- [x] Gamepad confirm on title/game over/victory screens

### Phase 10: Title Screen Story Crawl [DONE]
- [x] Story crawl auto-triggers after 5 seconds idle on title screen
- [x] Scrolling lore text about Veyrun and Ingnal worlds colliding
- [x] 5 decorative mini bats flying erratically around the screen
- [x] 3 decorative mini demons walking/charging across the bottom
- [x] Semi-transparent overlay keeps title text readable over crawl
- [x] Crawl loops endlessly, resets when returning to title from game over/victory

### Phase 11: Major Game Polish [DONE]
- [x] Fix gamepad ring menu navigation (L1/R1/Y edge detection)
- [x] Runes don't spawn inside obstacles (spiral search for clear position)
- [x] Fix last level victory condition (kill_count=15 instead of impossible kill_all)
- [x] Make centipedes larger and scarier (SEG_SIZE=16, 7 segments, mandibles, red palette)
- [x] Procedural sword & spear sprites (weapon_sprites.py, no disk loading)
- [x] Procedural tile graphics + themed floors (tile_graphics.py)
  - Meadow: bright green with flowers
  - Dark Woods: dark green with mossy patches
  - The Swarm: yellow-brown with sandy patches
  - Demon's Gate: charred earth with ember spots
- [x] Unique map layouts for levels 2-4 (new CSV files, _MAP2/_MAP3/_MAP4)
  - Level 2: corridors with symmetrical walls (Dark Woods)
  - Level 3: open arena with central rock formation (The Swarm)
  - Level 4: fortress with central walled chamber (Demon's Gate)
- [x] Chainmail armour pickup (level 1 only, reduces all damage by 1)
- [x] Move equipped weapon/spell icons to HUD center
- [x] Hero portrait card with golden border on HUD left side
- [x] Fade title screen text during story crawl (to ~40% over 2 seconds)
- [x] Sword arc vs spear line attack differentiation
  - Sword: wide arc hitbox (good for crowd control)
  - Spear: narrow thrust hitbox with longer reach

## Current Session State
- **Working on:** All phases complete through Phase 11
- **Last completed step:** Phase 11 - major game polish (12 items)
- **Notes:** Game fully playable with sound, gamepad, 4 unique levels,
  3 enemy types, all procedural sprites and tiles, story crawl, themed floors,
  chainmail armour, differentiated sword/spear attacks, hero portrait HUD.
