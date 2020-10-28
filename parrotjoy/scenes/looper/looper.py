"""A visualization and tool for recording and looping samples.
"""
import pygame as pg

from ...metronome import BpmCounter, BpmLight, BpmLine
from ...resources import gfx

from .camera import Camera
from .recording_light import RecordingLight
from .recording_wave import RecordingWave
from .track_recorder import TrackRecorder

# from gif_saver import GifSaver


class Parrot(pg.sprite.DirtySprite):
    """Our evil little parrot; plotting evil, but looking cute."""

    def __init__(self):
        pg.sprite.DirtySprite.__init__(self)
        self.image = gfx("parrotjoy-logo.png")
        self.rect = self.image.get_rect().copy()
        self.rect.x = pg.display.get_surface().get_width() - self.rect.width
        self.rect.y = 20


class Looper:
    """The whole looper scene.

    Combines all these things:
    - RecordingLight, RecordingWave, TrackRecorder
    - BpmCounter, BpmLight, BpmLine, Camera
    """

    def __init__(self, app):
        self.active = True
        self.rects = []

        self.screen = app.screen
        self._app = app

        # We loop quickly so timing can be more accurate with the sounds.
        self.fps = 240

        self.camera = Camera()
        self.track_recorder = TrackRecorder(app.audio_thread)
        self.recording_lights = [
            RecordingLight(track, idx)
            for idx, track in enumerate(self.track_recorder.tracks)
        ]
        self.recording_waves = [
            RecordingWave(track, idx)
            for idx, track in enumerate(self.track_recorder.tracks)
        ]
        self.bpm_counter = BpmCounter(self.track_recorder.bpm)
        self.bpm_light = BpmLight(self.track_recorder.bpm)
        self.bpm_line = BpmLine(self.track_recorder.bpm)
        self.parrot = Parrot()

        pg.display.set_caption("press space 4 times to adjust BPM timing")
        screen = app.screen

        self.background = pg.Surface(screen.get_size()).convert()
        self.background.fill((0, 0, 0))

        sprite_list = (
            [self.bpm_counter, self.bpm_light, self.bpm_line]
            + self.recording_lights
            + self.recording_waves
            + [self.parrot]
        )
        allsprites = pg.sprite.LayeredDirty(sprite_list, _time_threshold=1000 / 10.0)
        allsprites.clear(screen, self.background)
        self.allsprites = allsprites

    def redraw(self):
        """Redraw the whole screen, and display.update"""
        screen = self.screen
        allsprites = self.allsprites
        background = self.background

        rects = []
        rects.append(screen.blit(background, (0, 0)))
        allsprites.clear(screen, background)
        for spr in allsprites:
            spr.dirty = 1
        allsprites.draw(screen)
        pg.display.update(rects)

    def events(self, events):
        """Process our events."""
        for event in events:
            if event.type == pg.KEYDOWN and event.key in [pg.K_c]:
                self.redraw()
                self.camera.start()

            if event.type == pg.KEYDOWN and event.key in [pg.K_v]:
                self.screen.blit(self.background, (0, 0))
                self.allsprites.clear(self.screen, self.background)
                self.camera.start()

        self.track_recorder.events(events)
        self.bpm_counter.events(events)

        self.rects = []

    def update(self, elapsed_time):
        """return True to let other scenes update. False to only us update."""

    def render(self):
        """return rects.

        If scene.propagate_render is True, the render will
            continue to be propagated.
        """
        # the line changes color depending on when we are recording.
        for track in self.track_recorder.tracks:
            if track.recording == 1:
                self.bpm_line.color = self.bpm_line.preparing_color
                break
            if track.recording == 2:
                self.bpm_line.color = self.bpm_line.recording_color
                break

            self.bpm_line.color = self.bpm_line.not_recording_color

        if self.camera.video_thread.size[0] != 1920:
            self.allsprites.update()
            self.rects.extend(self.allsprites.draw(self.screen))

        self.rects.extend(self.camera.draw(self.screen))
        return self.rects
