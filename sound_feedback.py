from __future__ import annotations

import math
from array import array

import pygame


class SoundFeedback:
    """Small generated tones that keep the game free of external audio assets."""

    def __init__(self) -> None:
        self.enabled = True
        self.available = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self._sounds = {
                "move": self._tone(330, 80, 0.14),
                "mill": self._tone(660, 150, 0.18),
                "capture": self._tone(190, 120, 0.17),
                "complete": self._tone(520, 240, 0.16),
            }
            self.available = True
        except pygame.error:
            self.available = False

    @staticmethod
    def _tone(frequency: int, duration_ms: int, volume: float) -> pygame.mixer.Sound:
        sample_rate = 22050
        sample_count = round(sample_rate * duration_ms / 1000)
        samples = array("h")
        for index in range(sample_count):
            fade = 1 - index / sample_count
            value = math.sin(2 * math.pi * frequency * index / sample_rate)
            samples.append(round(32767 * volume * fade * value))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def play(self, name: str) -> None:
        if self.enabled and self.available and name in self._sounds:
            self._sounds[name].play()
