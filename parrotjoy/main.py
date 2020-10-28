"""Main loop and entry point.
"""
import time

import pygame as pg

from .audiorecord import AudioRecord
from .scenes.looper.looper import Looper
from .scenes.strawberries import Strawberries
from .scenes.videosynth import VideoSynth


DEVICENAME_INPUT = None
DEVICENAME_OUTPUT = None
# DEVICENAME_INPUT = b'Scarlett 2i4 USB'
# DEVICENAME_OUTPUT = b'Scarlett 2i4 USB'


class App:
    """App class, initializes and then coordinates all the scenes."""

    # flags = pg.FULLSCREEN
    flags = 0
    # flags = pg.SCALED | pg.FULLSCREEN
    width = 1024
    height = 768
    # fps = 30
    fps = 240

    def __init__(self, argv):
        self.argv = argv

        # pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT)
        pg.mixer.pre_init(
            44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT, allowedchanges=0
        )
        pg.init()
        pg.font.init()

        self.audio_thread = AudioRecord(inputdevice=DEVICENAME_INPUT)
        self.audio_thread.start()

        joys = {}
        for joy_id in range(pg.joystick.get_count()):
            j = pg.joystick.Joystick(joy_id)
            joys[joy_id] = j
            j.init()

        self.screen = pg.display.set_mode((self.width, self.height), self.flags)
        self.clock = pg.time.Clock()

        self.running = True

        self.scenes = {
            "videosynth": VideoSynth(self),
            "strawberries": Strawberries(self),
            "looper": Looper(self),
        }
        self.scenes["videosynth"].active = False
        self.scenes["strawberries"].active = False

    def activate_scene(self, scene, fps=30):
        """Activate the given scene."""
        for scn in self.scenes.values():
            scn.active = False
        scene.active = True
        self.fps = fps
        if hasattr(scene, "redraw"):
            scene.redraw()

    def events(self, events):
        """Process all the events, pass the events down to the scenes."""
        for event in events:
            if (
                event.type == pg.QUIT
                or event.type == pg.KEYDOWN
                and event.key in [pg.K_ESCAPE, pg.K_q]
            ):
                self.running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_0:
                self.activate_scene(self.scenes["looper"], fps=240)
            elif event.type == pg.KEYDOWN and event.key == pg.K_9:
                self.activate_scene(self.scenes["videosynth"])
            elif event.type == pg.KEYDOWN and event.key == pg.K_8:
                self.activate_scene(self.scenes["strawberries"])

        if not self.running:
            return
        # print(self.scenes[::-1], events)
        for scene in list(self.scenes.values())[::-1]:
            if scene.active:
                scene.events(events)

    def update(self, elapsed_time):
        """Update all the scenes until one returns False."""
        self.audio_thread.update()

        for scene in list(self.scenes.values())[::-1]:
            if scene.active:
                if not scene.update(elapsed_time):
                    break

        self.clock.tick(self.fps)

    def render(self):
        """Render the highest active scene.

        If scene.propagate_render is True, the render will
            continue to be propagated.
        """

        all_rects = []
        for scene in list(self.scenes.values())[::-1]:
            if scene.active:
                rects = scene.render()
                if rects is not None:
                    all_rects.extend(rects)
                if not getattr(scene, "propagate_render", False):
                    break
        # print(all_rects)
        pg.display.update(all_rects)

    def main(self):
        """Our mainloop."""

        elapsed_time = 0
        while self.running:
            start_time = time.time()
            self.events(pg.event.get())
            self.update(elapsed_time)
            self.render()
            elapsed_time = (time.time() - start_time) * 1000

        self.audio_thread.audio_going = False

        pg.quit()


def main(argv):
    """Main loop."""
    App(argv).main()


if __name__ == "__main__":
    import sys

    main(sys.argv)
