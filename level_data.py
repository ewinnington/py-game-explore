"""Level definitions for DemoBlade.

Each level is a dict with:
    name        - display name
    map_csv     - dict of CSV paths for tile layers
    floor       - background image path
    player_pos  - starting position
    enemies     - list of (type_str, pos) tuples
    pickups     - list of (type_str, pos, extra) tuples
    spawners    - list of spawner configs
    objective   - dict describing the win condition
    next_level  - index of next level (None = victory)
    portal_pos  - position of exit portal (appears when objective complete)
"""

import os

# Map paths reused across levels (we only have one set of CSVs currently,
# but levels can override enemy/pickup placement for variety)
_MAP1 = {
    'boundary': os.path.join('maps', 'boundary_1.csv'),
    'rocks':    os.path.join('maps', 'boundary_1.csv'),
    'grass':    os.path.join('maps', 'grass_1.csv'),
    'object':   os.path.join('maps', 'object_1.csv'),
}

LEVELS = [
    # ── Level 1: The Meadow ──────────────────────────────────────────
    {
        'name': 'The Meadow',
        'map_csv': _MAP1,
        'floor': os.path.join('sprites', 'landscape_grass.png'),
        'player_pos': (100, 200),
        'enemies': [
            ('demon', (400, 350)),
            ('demon', (700, 300)),
            ('bat',   (550, 200)),
        ],
        'pickups': [
            ('rune_spear',   (250, 400)),
            ('rune_fire',    (500, 150)),
            ('health',       (450, 500)),
        ],
        'spawners': [],
        'objective': {'type': 'kill_all', 'desc': 'Defeat all monsters'},
        'next_level': 1,
        'portal_pos': (700, 180),
    },

    # ── Level 2: Dark Woods ──────────────────────────────────────────
    {
        'name': 'Dark Woods',
        'map_csv': _MAP1,
        'floor': os.path.join('sprites', 'landscape_grass.png'),
        'player_pos': (100, 200),
        'enemies': [
            ('demon', (350, 350)),
            ('demon', (600, 400)),
            ('bat',   (400, 200)),
            ('bat',   (750, 350)),
            ('centipede', (500, 600)),
        ],
        'pickups': [
            ('rune_ice',     (750, 600)),
            ('health',       (300, 700)),
            ('health',       (650, 250)),
        ],
        'spawners': [
            {'pos_col': 10, 'pos_row': 17, 'interval': 5000, 'max': 3},
        ],
        'objective': {'type': 'kill_count', 'count': 8, 'desc': 'Defeat 8 monsters'},
        'next_level': 2,
        'portal_pos': (700, 180),
    },

    # ── Level 3: The Swarm ───────────────────────────────────────────
    {
        'name': 'The Swarm',
        'map_csv': _MAP1,
        'floor': os.path.join('sprites', 'landscape_grass.png'),
        'player_pos': (100, 200),
        'enemies': [
            ('bat',       (300, 250)),
            ('bat',       (500, 300)),
            ('bat',       (700, 250)),
            ('centipede', (400, 500)),
            ('centipede', (600, 700)),
            ('demon',     (350, 650)),
            ('demon',     (700, 500)),
        ],
        'pickups': [
            ('rune_shadow', (200, 800)),
            ('health',      (500, 400)),
            ('health',      (300, 600)),
        ],
        'spawners': [
            {'pos_col': 10, 'pos_row': 17, 'interval': 3500, 'max': 4},
        ],
        'objective': {'type': 'kill_count', 'count': 12, 'desc': 'Defeat 12 monsters'},
        'next_level': 3,
        'portal_pos': (700, 180),
    },

    # ── Level 4: Demon's Gate (final) ────────────────────────────────
    {
        'name': "Demon's Gate",
        'map_csv': _MAP1,
        'floor': os.path.join('sprites', 'landscape_grass.png'),
        'player_pos': (100, 200),
        'enemies': [
            ('demon',     (300, 300)),
            ('demon',     (500, 300)),
            ('demon',     (700, 300)),
            ('demon',     (400, 500)),
            ('bat',       (600, 200)),
            ('bat',       (200, 400)),
            ('centipede', (500, 700)),
            ('centipede', (300, 600)),
        ],
        'pickups': [
            ('health', (400, 400)),
            ('health', (600, 600)),
            ('health', (200, 700)),
        ],
        'spawners': [
            {'pos_col': 5,  'pos_row': 17, 'interval': 3000, 'max': 3},
            {'pos_col': 15, 'pos_row': 17, 'interval': 3000, 'max': 3},
        ],
        'objective': {'type': 'kill_all', 'desc': 'Exterminate all demons!'},
        'next_level': None,  # victory!
        'portal_pos': (640, 180),
    },
]
