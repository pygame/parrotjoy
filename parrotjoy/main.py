import sys
import io
import random
import math
import time


import numpy as np
import pygame as pg
pygame = pg
from pygame.midi import frequency_to_midi, midi_to_frequency, midi_to_ansi_note

from tracks import Track
from audiorecord import AudioRecord, PITCHES, ONSETS, AUDIOS
from scenes.videosynth import VideoSynth
from scenes.looper.looper import Looper
from scenes.strawberries import Strawberries


DEVICENAME_INPUT = None
DEVICENAME_OUTPUT = None
# DEVICENAME_INPUT = b'Scarlett 2i4 USB'
# DEVICENAME_OUTPUT = b'Scarlett 2i4 USB'



class App:
    FLAGS = pg.FULLSCREEN
    FLAGS = 0
    FLAGS = pg.SCALED | pg.FULLSCREEN
    WIDTH = 1024
    HEIGHT = 768
    # FPS = 30
    FPS = 240


    def __init__(self):


        #pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT)
        pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT, allowedchanges=0)
        pg.init()
        pg.font.init()


        self.audio_thread = AudioRecord(inputdevice=DEVICENAME_INPUT)
        self.audio_thread.start()


        joys = {}
        for x in range(pg.joystick.get_count()):
            j = pg.joystick.Joystick(x)
            joys[x] = j
            j.init()


        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), self.FLAGS)
        self.clock = pygame.time.Clock()

        self.running = True

        self.videosynth = VideoSynth(self)
        self.videosynth.active = False
        self.looper = Looper(self)
        self.strawberries = Strawberries(self)
        self.strawberries.active = False
        self.scenes = [self.looper, self.videosynth, self.strawberries]

        self.gifmaker = None

    def looper_active(self):
        self.looper.active = True
        self.looper.redraw()
        self.videosynth.active = False
        self.strawberries.active = False
        self.FPS = 240

    def videosynth_active(self):
        self.looper.active = False
        self.videosynth.active = True
        self.strawberries.active = False
        self.FPS = 30


    def strawberries_active(self):
        self.looper.active = False
        self.videosynth.active = False
        self.strawberries.active = True
        self.FPS = 30

    def events(self, events):
        """
        """
        for event in events:
            if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key in [pg.K_ESCAPE, pg.K_q]:
                self.running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_0:
                self.looper_active()
            elif event.type == pg.KEYDOWN and event.key == pg.K_9:
                self.videosynth_active()
            elif event.type == pg.KEYDOWN and event.key == pg.K_8:
                self.strawberries_active()

        if not self.running:
            return
        # print(self.scenes[::-1], events)
        for scene in self.scenes[::-1]:
            if scene.active:
                scene.events(events)

    def update(self, elapsed_time):
        """ update all the scenes until one returns False.
        """
        self.audio_thread.update()

        for scene in self.scenes[::-1]:
            if scene.active:
                if not scene.update(elapsed_time):
                    break

        self.clock.tick(self.FPS)

    def render(self):
        """ Render the highest active scene.

        If scene.propagate_render is True, the render will
            continue to be propagated.
        """

        all_rects = []
        for scene in self.scenes[::-1]:
            if scene.active:
                rects = scene.render()
                if rects is not None:
                    all_rects.extend(rects)
                if not getattr(scene, 'propagate_render', False):
                    break
        # print(all_rects)
        pygame.display.update(all_rects)


    def main(self):
        """
        """

        elapsed_time = 0
        while self.running:
            fs = time.time()
            self.events(pygame.event.get())
            self.update(elapsed_time)
            self.render()
            elapsed_time = (time.time() - fs) * 1000
            if self.gifmaker is not None:
                self.gifmaker.update(events, self.screen)

        self.audio_thread.audio_going = False

        pygame.quit()





def main(args):
    try:
        gamemain(args)
    except KeyboardInterrupt:
        print('Keyboard Interrupt...')
        print('Exiting')

def gamemain(args):

    app = App()
    app.main()




if __name__ == '__main__':
    main(sys.argv)
