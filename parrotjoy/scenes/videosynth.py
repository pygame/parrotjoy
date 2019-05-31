import random
import math
import time

import pygame as pg

from parrotjoy.tracks import Track
from parrotjoy.audiorecord import PITCHES, ONSETS, AUDIOS



class Visual(object):
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size

    def update(self):
        self.size -= 6
        return self


class VideoSynth:
    def __init__(self, app):
        self.active = True

        self.screen = app.screen
        self._app = app

        self.colors = [
            (random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)) for x in range(10)
        ]
        self.visuals = []

        self.track = Track(None)

    def render(self):
        screen = self.screen
        screen.fill((0, 0, 0))
        new_visuals = []
        for place, visual in enumerate(self.visuals):
            if visual.size > 2:
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], 0, math.pi/2, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], math.pi/2, math.pi, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], math.pi,3*math.pi/2, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], 3*math.pi/2, 2*math.pi, 2)

                new_visuals.append(visual.update())

        self.visuals = new_visuals
        return [self.screen.get_rect()]



    def update(self, elapsed_time):
        pass


    def events(self, events):
        screen_width, screen_height = self.screen.get_size()
        for event in events:
            if event.type == PITCHES:
                pass
            elif event.type == ONSETS:
                for onset in event.onsets:
                    self.visuals.append(Visual(
                        random.randint(0, screen_width),
                        random.randint(0, screen_height),
                        random.choice(self.colors),
                        size=300
                    ))
            elif event.type == AUDIOS:
                for audio in event.audios:
                    self.track.update(audio)


