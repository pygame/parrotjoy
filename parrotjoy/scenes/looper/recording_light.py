import pygame as pg
from ...tracks import Track

class RecordingLight(pg.sprite.DirtySprite):
    """Shows a red 'light' representing each beat."""

    def __init__(self, track: Track, track_idx: int):
        pg.sprite.DirtySprite.__init__(self)
        self.dirty = 1
        self.track = track
        self.track_idx = track_idx

        self.image = pg.Surface((20, 20))
        self.image.fill((25, 25, 25))
        self.rect = self.image.get_rect().copy()
        self.rect.x = 50 + (track_idx * 30)
        self.rect.y = 30
        self.state = None

    def update(self):
        """Update the recording light state"""

        if (
            self.track.recording == 1
            and (not self.track.add_to_mode)
            and self.state != "preparing"
        ):
            self.image.fill((0, 0, 255))
            self.dirty = 1
            self.state = "preparing"
        elif (
            self.track.recording == 2
            and (not self.track.add_to_mode)
            and self.state != "recording"
        ):
            self.image.fill((0, 255, 255))
            self.dirty = 1
            self.state = "recording"
        elif self.track.add_to_mode and self.state != "add_to_mode":
            self.image.fill((0, 255, 0))
            self.dirty = 1
            self.state = "add_to_mode"
        elif (not (self.track.recording or self.track.add_to_mode)) and self.state in [
            "add_to_mode",
            "recording",
        ]:
            self.image.fill((25, 25, 25))
            self.dirty = 1
            self.state = None
        # print (self.state, self.track.recording, self.track.add_to_mode)
