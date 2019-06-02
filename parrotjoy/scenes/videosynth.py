import random
import math
import time

import pygame as pg

from parrotjoy.tracks import Track
from parrotjoy.audiorecord import PITCHES, ONSETS, AUDIOS


SIZE = 300


class Visual(object):
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size

    def update(self):
        self.size -= 6
        return self



def normalize(n, range1, range2):
    delta1 = range1[1] - range1[0]
    delta2 = range2[1] - range2[0]
    return min((delta2 * (n - range1[0]) / delta1) + range2[0], range2[1])

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
        self.blend_colors = [
            pg.Color('red'),
            pg.Color('green'),
            pg.Color('blue'),
        ]
        self.visuals = []

        self.track = Track(None)

        self.size = SIZE
        self.blend = False

    def render(self):
        screen = self.screen
        screen.fill((0, 0, 0))
        new_visuals = []
        for place, visual in enumerate(self.visuals):
            if visual.size > 2:

                if self.blend:
                    surface = pg.Surface((200, 200)).convert_alpha()
                    surface.fill((0,0,0,0))
                    pg.draw.circle(surface, visual.color, (100, 100), 100, 0)
                    screen.blit(surface, (visual.x, visual.y), special_flags=pg.BLEND_ADD)
                else:
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
            e = event
            if event.type == PITCHES:
                pass
                if self.blend and self.blend != 2:
                    y = int(normalize(e.frequencies[0], [50, 350], [0, 2]))
                    self.visuals.append(Visual(
                        random.randint(0, screen_width),
                        random.randint(0, screen_height),
                        self.blend_colors[y],
                        size=self.size
                    ))

            elif event.type == ONSETS:
                if self.blend == 2:
                    for onset in event.onsets:
                        self.visuals.append(Visual(
                            random.randint(0, screen_width),
                            random.randint(0, screen_height),
                            random.choice(self.blend_colors),
                            size=self.size*2
                        ))

                if not self.blend:
                    for onset in event.onsets:
                        self.visuals.append(Visual(
                            random.randint((screen_width//4), screen_width - (screen_width//2)),
                            random.randint((screen_height//4), screen_height - (screen_height//2)),
                            random.choice(self.colors),
                            size=self.size
                        ))
            elif event.type == AUDIOS:
                for audio in event.audios:
                    self.track.update(audio)


            if e.type == pg.KEYDOWN:
                if e.key == pg.K_r:
                    self.size = SIZE
                if e.key == pg.K_e:
                    self.size += -10
                if e.key == pg.K_t:
                    self.size += 10
                if e.key == pg.K_b:
                    self.blend = not self.blend
                if e.key == pg.K_n:
                    self.blend = 2

