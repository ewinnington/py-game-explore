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

### Phase 4: Pickup System [IN PROGRESS]
- [ ] Rune pickups in world (spear, fire, ice, shadow) with glow effect
- [ ] Collecting rune adds item to appropriate ring menu
- [ ] Health pickup (heart/potion) restores HP
- [ ] Pickups can be placed in level data or dropped by enemies

### Phase 5: Game State & Level System [NOT STARTED]
- [ ] Game state manager (title, gameplay, level_transition, game_over)
- [ ] Title screen
- [ ] 3-4 levels with different maps, enemy compositions, objectives
- [ ] Level transition portals/exits
- [ ] Level objectives (kill X enemies, reach exit, find item, defeat boss)

### Phase 6: Kill Tracking & Objectives UI [NOT STARTED]
- [ ] Kill counter per enemy type
- [ ] On-screen objective display
- [ ] Level completion screen with stats

## Current Session State
- **Working on:** Phase 4
- **Last completed step:** Phase 3 - bat + centipede integrated and tested
- **Notes:** All 3 enemy types working. Next: pickup system, then levels.
