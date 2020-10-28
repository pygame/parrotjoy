"""Draws a track wave.
"""
import numpy as np
import pygame as pg
from ...draw_sound import draw_wave
from ...tracks import Track

IMAGE_HEIGHT = 130
WAVE_WIDTH = 320
BACKGROUND_COLOR = (0, 0, 0)


class RecordingWave(pg.sprite.DirtySprite):
    """Shows a wave for the given track."""

    def __init__(self, track: Track, track_idx: int):
        pg.sprite.DirtySprite.__init__(self)
        self.track = track
        self.track_idx = track_idx

        # how many pixels wide for how many seconds?
        self.full_width_seconds = 5
        self.image = pg.Surface((WAVE_WIDTH, IMAGE_HEIGHT)).convert()
        self.image.fill(BACKGROUND_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 70 + (self.track_idx * IMAGE_HEIGHT)
        self.state = None
        self.dirty = True

    def draw_wave(self):
        """Draws the sound wave for the given track.

        How big should the image be?
        Depends on how much sound is recorded.
        """
        sound_length = self.track.sounds[0].get_length()
        image_width = WAVE_WIDTH / self.full_width_seconds * sound_length
        self.image = pg.Surface((image_width, IMAGE_HEIGHT)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 70 + (self.track_idx * IMAGE_HEIGHT)

        float32_data = np.frombuffer(self.track.audios[0], dtype=np.float32)
        int16_data = ((float32_data / 1.414) * pow(2, 16) // 2).astype(np.int16)
        samples = int16_data

        draw_wave(
            self.image,
            samples,
            background_color=BACKGROUND_COLOR,
            wave_color=(255, 255, 255),
        )

    def update(self):
        """Handles the different states for the track."""
        # print(
        #     "RecordingWave: self.track.recording, self.state,"
        #     + " self.track.recording, self.track.add_to_mode"
        # )
        # print(
        #     self.track.recording,
        #     self.state,
        #     self.track.recording,
        #     self.track.add_to_mode,
        # )
        if (
            self.track.recording == 2
            and (not self.track.add_to_mode)
            and self.state != "recording"
        ):
            print("WAVE: recording")
            self.image.fill((0, 0, 0))
            self.dirty = True
            self.state = "recording"
        elif self.track.add_to_mode and self.state != "add_to_mode":
            print("WAVE: add_to_mode")
            self.state = "add_to_mode"
        elif (not (self.track.recording or self.track.add_to_mode)) and self.state in [
            "add_to_mode",
            "recording",
        ]:
            print("WAVE: update wave")
            if self.track.sounds and self.track.sounds[0]:
                self.draw_wave()
            self.dirty = True
            self.state = None
        elif self.track.erased:
            print("WAVE: erased")
            self.image.fill((0, 0, 0))
            self.dirty = True
        elif self.track.trimmed:
            print("WAVE: trimmed")
            if self.track.sounds and self.track.sounds[0]:
                self.draw_wave()
            self.dirty = True
            self.state = None
