import random
import math
import os
import glob
import string
import time

import pygame as pg

from ..audiorecord import PITCHES, ONSETS

# constants
WINSIZE = [1920, 1080]
WINSIZE = [2048, 1280]
WINSIZE = [640, 480]
WINSIZE = [2448 // 2, 2448 // 2]
WINSIZE = [1000, 1000]
WINCENTER = [320, 240]

WINSIZE = [1024, 768]
WINCENTER = [int(1024 / 2), int(768 / 2)]
NUMSTARS = 150


def load_letters(extra_sizes=None):
    if extra_sizes is None:
        extra_sizes = [(100, 100), (768, 768)]
    letter_path = os.path.join("data", "images", "letters")
    fnames = glob.glob(os.path.join(letter_path, "*.jpg"))
    image_paths = {os.path.split(f)[1].split(".jpg")[0]: f for f in fnames}

    images = {}

    def load_image(letter):
        surf = pg.image.load(image_paths[letter])
        images[letter] = surf.convert()
        for x, y in extra_sizes:
            images[f"{letter}{x}x{y}"] = pg.transform.smoothscale(
                surf, (x, y)
            ).convert()

    pg.threads.tmap(load_image, image_paths)
    return images


def init_star():
    "creates new star values"
    direction = random.randrange(100000)
    velocity_multiplier = random.random() * 0.6 + 0.4
    vel = [
        math.sin(direction) * velocity_multiplier,
        math.cos(direction) * velocity_multiplier,
    ]
    return vel, WINCENTER[:]


def initialize_stars():
    "creates a new starfield"
    stars = []
    for _ in range(NUMSTARS):
        star = init_star()
        vel, pos = star
        steps = random.randint(0, WINCENTER[0])
        pos[0] = pos[0] + (vel[0] * steps)
        pos[1] = pos[1] + (vel[1] * steps)
        vel[0] = vel[0] * (steps * 0.09)
        vel[1] = vel[1] * (steps * 0.09)
        stars.append(star)
    move_stars(stars)
    return stars


def draw_stars(surface, stars, color):
    "used to draw (and clear) the stars"
    for _, pos in stars:
        pos = (int(pos[0]), int(pos[1]))
        surface.set_at(pos, color)


def move_stars(stars):
    "animate the star values"
    for vel, pos in stars:
        pos[0] = pos[0] + vel[0]
        pos[1] = pos[1] + vel[1]
        if not 0 <= pos[0] <= WINSIZE[0] or not 0 <= pos[1] <= WINSIZE[1]:
            vel[:], pos[:] = init_star()
        else:
            vel[0] = vel[0] * 1.05
            vel[1] = vel[1] * 1.05


def normalize(n, range1, range2):
    delta1 = range1[1] - range1[0]
    delta2 = range2[1] - range2[0]
    return min((delta2 * (n - range1[0]) / delta1) + range2[0], range2[1])


PAUSE_TIME = 0.2


class Strawberries:
    def __init__(self, app):
        self.active = True

        self.screen = app.screen
        self._app = app

        random.seed()
        self.stars = initialize_stars()

        self.letters = load_letters()
        self.letter_i = 0
        self.ascii_lowercase = string.ascii_lowercase

        self.pause_on_letter = time.time()
        self.random_pause = False

        self.pause_time = PAUSE_TIME

    def events(self, events):
        for e in events:
            if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                WINCENTER[:] = list(e.pos)
            if e.type == PITCHES:
                y = normalize(e.frequencies[0], [50, 350], [0, 768])
                WINCENTER[:] = [int(1024 / 2), y]
                # print(y, e.frequencies[0])
            if e.type == ONSETS:
                if not self.random_pause:
                    self.pause_on_letter = time.time()

            if e.type == pg.KEYDOWN:
                if e.key == pg.K_r:
                    self.random_pause = not self.random_pause
                    self.pause_time = PAUSE_TIME
                if e.key == pg.K_e:
                    self.pause_time += -0.02
                if e.key == pg.K_t:
                    self.pause_time += 0.02

    def update(self, elapsed_time):
        """return True to let other scenes update. False to only us update."""

    def render(self):
        """return rects.

        If scene.propagate_render is True, the render will
            continue to be propagated.
        """
        screen = self.screen

        white = 255, 240, 200
        # black = 20, 20, 40
        black = 0, 0, 0
        screen.fill(black)

        x = int((1024 - 768) // 2)
        key = self.ascii_lowercase[self.letter_i] + "768x768"
        if key not in self.letters:
            return []
        screen.blit(self.letters[key], (x, 0))

        # print (pause_on_letter)
        if self.pause_on_letter:
            # print('yoooooop', pause_on_letter + 1.0, time.time())
            if self.pause_on_letter + self.pause_time < time.time():
                # print('finished')
                self.pause_on_letter = 0
        else:
            self.letter_i += 1
            if self.letter_i >= len(self.ascii_lowercase):
                self.letter_i = 0
            if self.random_pause:
                if random.randint(0, 10) == 5:
                    self.pause_on_letter = time.time()

        draw_stars(screen, self.stars, black)
        move_stars(self.stars)
        draw_stars(screen, self.stars, white)
        return [self.screen.get_rect()]
