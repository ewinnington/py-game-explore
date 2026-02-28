"""Level definitions for DemoBlade.

Each level is a dict with:
    name        - display name
    map_csv     - dict of CSV paths for tile layers
    floor       - background image path (None = procedural via theme)
    theme       - visual theme: 'meadow', 'darkwoods', 'swarm', 'demonsgate'
    player_pos  - starting position
    enemies     - list of (type_str, pos) tuples
    pickups     - list of (type_str, pos) tuples
    spawners    - list of spawner configs
    objective   - dict describing the win condition
    next_level  - index of next level (None = victory)
    portal_pos  - position of exit portal (appears when objective complete)
"""

import os

_MAP1 = {
    'boundary': os.path.join('maps', 'boundary_1.csv'),
    'rocks':    os.path.join('maps', 'boundary_1.csv'),
    'grass':    os.path.join('maps', 'grass_1.csv'),
    'object':   os.path.join('maps', 'object_1.csv'),
}

_MAP2 = {
    'boundary': os.path.join('maps', 'boundary_2.csv'),
    'rocks':    os.path.join('maps', 'boundary_2.csv'),
    'grass':    os.path.join('maps', 'grass_2.csv'),
    'object':   os.path.join('maps', 'object_2.csv'),
}

_MAP3 = {
    'boundary': os.path.join('maps', 'boundary_3.csv'),
    'rocks':    os.path.join('maps', 'boundary_3.csv'),
    'grass':    os.path.join('maps', 'grass_3.csv'),
    'object':   os.path.join('maps', 'object_3.csv'),
}

_MAP4 = {
    'boundary': os.path.join('maps', 'boundary_4.csv'),
    'rocks':    os.path.join('maps', 'boundary_4.csv'),
    'grass':    os.path.join('maps', 'grass_4.csv'),
    'object':   os.path.join('maps', 'object_4.csv'),
}

LEVELS = [
    # ── Level 1: The Meadow ──────────────────────────────────────────
    {
        'name': 'The Meadow',
        'map_csv': _MAP1,
        'floor': None,
        'theme': 'meadow',
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
            ('chainmail',    (350, 280)),
        ],
        'spawners': [],
        'objective': {'type': 'kill_all', 'desc': 'Defeat all monsters'},
        'next_level': 1,
        'portal_pos': (700, 180),
    },

    # ── Level 2: Dark Woods ──────────────────────────────────────────
    {
        'name': 'Dark Woods',
        'map_csv': _MAP2,
        'floor': None,
        'theme': 'darkwoods',
        'player_pos': (130, 200),
        'enemies': [
            ('demon', (500, 350)),
            ('demon', (800, 400)),
            ('bat',   (350, 500)),
            ('bat',   (700, 250)),
            ('centipede', (600, 650)),
        ],
        'pickups': [
            ('rune_ice',     (900, 600)),
            ('health',       (250, 700)),
            ('health',       (750, 350)),
        ],
        'spawners': [
            {'pos_col': 10, 'pos_row': 17, 'interval': 5000, 'max': 3},
        ],
        'objective': {'type': 'kill_count', 'count': 8, 'desc': 'Defeat 8 monsters'},
        'next_level': 2,
        'portal_pos': (640, 180),
    },

    # ── Level 3: The Swarm ───────────────────────────────────────────
    {
        'name': 'The Swarm',
        'map_csv': _MAP3,
        'floor': None,
        'theme': 'swarm',
        'player_pos': (130, 200),
        'enemies': [
            ('bat',       (400, 300)),
            ('bat',       (600, 350)),
            ('bat',       (800, 300)),
            ('centipede', (350, 550)),
            ('centipede', (700, 700)),
            ('demon',     (250, 650)),
            ('demon',     (850, 500)),
        ],
        'pickups': [
            ('rune_shadow', (200, 800)),
            ('health',      (600, 500)),
            ('health',      (400, 700)),
        ],
        'spawners': [
            {'pos_col': 10, 'pos_row': 17, 'interval': 3500, 'max': 4},
        ],
        'objective': {'type': 'kill_count', 'count': 12, 'desc': 'Defeat 12 monsters'},
        'next_level': 3,
        'portal_pos': (640, 200),
    },

    # ── Level 4: Demon's Gate (final) ────────────────────────────────
    {
        'name': "Demon's Gate",
        'map_csv': _MAP4,
        'floor': None,
        'theme': 'demonsgate',
        'player_pos': (130, 250),
        'enemies': [
            ('demon',     (400, 300)),
            ('demon',     (700, 300)),
            ('demon',     (550, 650)),
            ('demon',     (300, 500)),
            ('bat',       (650, 200)),
            ('bat',       (200, 450)),
            ('centipede', (600, 750)),
            ('centipede', (400, 800)),
        ],
        'pickups': [
            ('health', (550, 580)),
            ('health', (750, 700)),
            ('health', (250, 750)),
        ],
        'spawners': [
            {'pos_col': 5,  'pos_row': 17, 'interval': 3000, 'max': 3},
            {'pos_col': 15, 'pos_row': 17, 'interval': 3000, 'max': 3},
        ],
        'objective': {'type': 'kill_count', 'count': 15, 'desc': 'Exterminate 15 monsters!'},
        'next_level': None,  # victory!
        'portal_pos': (640, 180),
    },
]
