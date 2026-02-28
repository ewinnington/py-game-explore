# DemoBlade - Game Transformation Progress

## Overview
Transforming the mini-POC into a full game with levels, enemy types, hero mechanics, and objectives.

## Phases

### Phase 1: Hero Stats & HUD [NOT STARTED]
- [ ] Add HP, MP, XP, Level stats to Player
- [ ] MP costs: fire=2, ice=4, shadow=5. MP regenerates over time
- [ ] Enemies deal damage to player (reduce HP, not just knockback)
- [ ] XP from kills, leveling up grants more HP/MP
- [ ] Bottom-of-screen HUD: HP bar, MP bar, XP bar, level, equipped weapon/spell icons
- [ ] Player death state (game over or respawn)

### Phase 2: Dual Ring Menu (Secret of Mana style) [NOT STARTED]
- [ ] Split circular menu into two rings: weapons + magic
- [ ] UP/DOWN switches between weapon ring and magic ring
- [ ] LEFT/RIGHT navigates within current ring
- [ ] Start with only sword; spear & spells found as runes
- [ ] Magic ring only appears once first magic rune is found
- [ ] Show currently selected weapon/spell on HUD
- [ ] Remove old add/remove (UP/DOWN) from menu

### Phase 3: New Enemy Types [NOT STARTED]
- [ ] Bat: flying, erratic swooping, low HP
- [ ] Centipede: multi-segment, each hit removes a segment, gets shorter
- [ ] Give enemies HP values (demon=2, bat=1, centipede segments=1 each)
- [ ] Different XP values per enemy type

### Phase 4: Pickup System [NOT STARTED]
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
- **Working on:** Phase 1
- **Last completed step:** None
- **Notes:** Starting fresh
