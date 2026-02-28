"""Procedural chiptune sound effects and background music for DemoBlade.

All sounds are generated at runtime using numpy — no external audio files.
Uses simple waveforms (square, triangle, noise) reminiscent of 8-bit consoles.
"""

import pygame
import numpy as np
import math

# Initialize mixer early with specific settings for chiptune
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)

SAMPLE_RATE = 22050


def _make_sound(samples):
    """Convert a numpy float array (-1..1) to a pygame Sound."""
    # Clip and convert to 16-bit signed int
    samples = np.clip(samples, -1.0, 1.0)
    data = (samples * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=data.tobytes())


def _square_wave(freq, duration, duty=0.5, volume=0.3):
    """Generate a square wave (classic NES sound)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = np.where((t * freq) % 1.0 < duty, volume, -volume)
    return wave


def _triangle_wave(freq, duration, volume=0.4):
    """Generate a triangle wave (smoother NES bass/melody)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = 2.0 * np.abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0
    return wave * volume


def _noise(duration, volume=0.15):
    """Generate white noise (NES noise channel style)."""
    n = int(SAMPLE_RATE * duration)
    return np.random.uniform(-volume, volume, n)


def _envelope(samples, attack=0.01, decay=0.0, sustain=1.0, release=0.05):
    """Apply a simple ADSR envelope."""
    n = len(samples)
    env = np.ones(n)
    attack_samples = int(attack * SAMPLE_RATE)
    release_samples = int(release * SAMPLE_RATE)

    # Attack
    if attack_samples > 0:
        env[:attack_samples] = np.linspace(0, 1, attack_samples)
    # Release
    if release_samples > 0:
        env[-release_samples:] = np.linspace(sustain, 0, release_samples)

    return samples * env


def _pitch_sweep(freq_start, freq_end, duration, volume=0.3):
    """Square wave with pitch sweep (good for power-up sounds)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(freq_start, freq_end, len(t))
    phase = np.cumsum(freq / SAMPLE_RATE)
    wave = np.where(phase % 1.0 < 0.5, volume, -volume)
    return wave


# ======================================================================
# Sound effect generators
# ======================================================================

def make_sword_hit():
    """Short percussive slash sound."""
    noise_part = _noise(0.08, 0.35)
    tone = _square_wave(200, 0.08, 0.5, 0.2)
    mix = noise_part + tone[:len(noise_part)]
    return _make_sound(_envelope(mix, attack=0.005, release=0.03))


def make_spell_cast():
    """Magical casting whoosh."""
    sweep = _pitch_sweep(300, 800, 0.2, 0.25)
    shimmer = _triangle_wave(1200, 0.2, 0.1)
    mix = sweep + shimmer[:len(sweep)]
    return _make_sound(_envelope(mix, attack=0.01, release=0.08))


def make_pickup():
    """Classic "item get" ascending arpeggio."""
    notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
    parts = []
    for note in notes:
        part = _square_wave(note, 0.08, 0.5, 0.25)
        parts.append(_envelope(part, attack=0.005, release=0.02))
    return _make_sound(np.concatenate(parts))


def make_enemy_hit():
    """Enemy takes damage - short thud."""
    noise_part = _noise(0.06, 0.3)
    tone = _square_wave(150, 0.06, 0.5, 0.2)
    mix = noise_part + tone[:len(noise_part)]
    return _make_sound(_envelope(mix, attack=0.002, release=0.02))


def make_enemy_death():
    """Enemy dies - descending pitch."""
    sweep = _pitch_sweep(400, 80, 0.25, 0.3)
    noise_part = _noise(0.25, 0.15)
    mix = sweep + noise_part[:len(sweep)]
    return _make_sound(_envelope(mix, attack=0.005, release=0.1))


def make_player_hurt():
    """Player takes damage."""
    sweep = _pitch_sweep(300, 100, 0.15, 0.3)
    return _make_sound(_envelope(sweep, attack=0.005, release=0.05))


def make_level_up():
    """Triumphant level-up fanfare."""
    notes = [523, 659, 784, 1047, 784, 1047, 1319]
    dur = [0.1, 0.1, 0.1, 0.15, 0.1, 0.15, 0.3]
    parts = []
    for note, d in zip(notes, dur):
        part = _triangle_wave(note, d, 0.3)
        parts.append(_envelope(part, attack=0.01, release=0.03))
    return _make_sound(np.concatenate(parts))


def make_portal():
    """Mystical portal hum."""
    sweep = _pitch_sweep(200, 600, 0.3, 0.2)
    shimmer = _triangle_wave(800, 0.3, 0.15)
    mix = sweep + shimmer[:len(sweep)]
    return _make_sound(_envelope(mix, attack=0.05, release=0.1))


def make_menu_open():
    """Menu open sound - quick ascending blip."""
    sweep = _pitch_sweep(400, 800, 0.08, 0.2)
    return _make_sound(_envelope(sweep, attack=0.005, release=0.02))


def make_menu_select():
    """Menu selection confirm."""
    notes = [660, 880]
    parts = []
    for note in notes:
        part = _square_wave(note, 0.06, 0.5, 0.2)
        parts.append(_envelope(part, attack=0.005, release=0.015))
    return _make_sound(np.concatenate(parts))


# ======================================================================
# Background music generator (simple looping chiptune)
# ======================================================================

def make_bgm():
    """Generate a short loopable chiptune BGM track.

    Simple melody + bass + percussion in the style of 8-bit RPG overworld.
    """
    bpm = 120
    beat = 60.0 / bpm  # seconds per beat

    # Melody (square wave, higher octave)
    melody_notes = [
        (392, 1), (440, 1), (494, 1), (523, 1),    # G4 A4 B4 C5
        (494, 1), (440, 0.5), (392, 0.5), (440, 2), # B4 A4 G4 A4
        (523, 1), (587, 1), (523, 1), (494, 1),     # C5 D5 C5 B4
        (440, 1), (392, 0.5), (349, 0.5), (392, 2), # A4 G4 F4 G4
    ]

    # Bass (triangle wave, lower octave)
    bass_notes = [
        (196, 2), (220, 2),   # G3 A3
        (247, 2), (220, 2),   # B3 A3
        (262, 2), (294, 2),   # C4 D4
        (220, 2), (196, 2),   # A3 G3
    ]

    # Build melody
    melody = []
    for freq, beats in melody_notes:
        dur = beat * beats
        wave = _square_wave(freq, dur, 0.5, 0.15)
        melody.append(_envelope(wave, attack=0.01, release=0.03))
    melody = np.concatenate(melody)

    # Build bass
    bass = []
    for freq, beats in bass_notes:
        dur = beat * beats
        wave = _triangle_wave(freq, dur, 0.12)
        bass.append(_envelope(wave, attack=0.02, release=0.05))
    bass = np.concatenate(bass)

    # Make same length
    max_len = max(len(melody), len(bass))
    if len(melody) < max_len:
        melody = np.pad(melody, (0, max_len - len(melody)))
    if len(bass) < max_len:
        bass = np.pad(bass, (0, max_len - len(bass)))

    # Light percussion (noise hits on beats)
    perc = np.zeros(max_len)
    samples_per_beat = int(beat * SAMPLE_RATE)
    for i in range(0, max_len, samples_per_beat):
        hit_len = min(int(0.04 * SAMPLE_RATE), max_len - i)
        hit = _noise(0.04, 0.08)[:hit_len]
        hit = _envelope(hit, attack=0.002, release=0.015)
        perc[i:i + hit_len] += hit

    mix = melody + bass + perc
    return _make_sound(mix)


# ======================================================================
# Sound manager singleton
# ======================================================================

class SoundManager:
    """Centralized sound playback. Call init() after pygame.init()."""

    _instance = None

    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self.bgm_sound = None
        self.bgm_channel = None
        self._initialized = False

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init(self):
        """Generate all sounds. Call once after pygame.mixer is ready."""
        if self._initialized:
            return
        try:
            self.sounds['sword_hit'] = make_sword_hit()
            self.sounds['spell_cast'] = make_spell_cast()
            self.sounds['pickup'] = make_pickup()
            self.sounds['enemy_hit'] = make_enemy_hit()
            self.sounds['enemy_death'] = make_enemy_death()
            self.sounds['player_hurt'] = make_player_hurt()
            self.sounds['level_up'] = make_level_up()
            self.sounds['portal'] = make_portal()
            self.sounds['menu_open'] = make_menu_open()
            self.sounds['menu_select'] = make_menu_select()
            self.bgm_sound = make_bgm()
            self._initialized = True
        except Exception as e:
            print(f"Sound init failed: {e}")
            self.enabled = False

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return
        self.sounds[name].play()

    def start_bgm(self):
        if not self.enabled or not self.bgm_sound:
            return
        # Use a dedicated channel for looping BGM
        if self.bgm_channel is None or not self.bgm_channel.get_busy():
            self.bgm_channel = self.bgm_sound.play(loops=-1)

    def stop_bgm(self):
        if self.bgm_channel:
            self.bgm_channel.stop()
            self.bgm_channel = None
