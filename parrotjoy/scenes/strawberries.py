import random, math, os, glob, string, time, pygame
from pygame.locals import *

#constants
WINSIZE = [1920, 1080]
WINSIZE = [2048, 1280]
WINSIZE = [640, 480]
WINSIZE = [2448/2, 2448/2]
WINSIZE = [1000, 1000]
WINCENTER = [320, 240]

WINSIZE = [1024, 768]
WINCENTER = [int(1024 / 2), int(768 / 2)]
NUMSTARS = 150



def load_letters(extra_sizes = [(100, 100), (768, 768)]):
    letter_path = os.path.join('data', 'images', 'letters')
    # fnames = glob.glob(os.path.join(letter_path, '*.png'))
    # image_paths = {os.path.split(f)[1].split('.png')[0]: f for f in fnames}
    fnames = glob.glob(os.path.join(letter_path, '*.jpg'))
    image_paths = {os.path.split(f)[1].split('.jpg')[0]: f for f in fnames}

    images = {}

    def load_image(letter):
        surf = pygame.image.load(image_paths[letter])
        images[letter] = surf.convert()
        for x, y in extra_sizes:
            images[letter + '%sx%s' % (x, y)] = pygame.transform.smoothscale(surf, (x, y)).convert()

    # def load_image(letter):
    #     surf = pygame.image.load(image_paths[letter])
    #     if surf.get_size() != (2448, 2448):
    #         surf = pygame.transform.smoothscale(surf, (2448, 2448))
    #     images[letter] = surf.convert()
    #     for x, y in extra_sizes:
    #         images[letter + '%sx%s' % (x, y)] = pygame.transform.smoothscale(surf, (x, y)).convert()

    pygame.threads.tmap(load_image, image_paths)
    return images



def init_star():
    "creates new star values"
    dir = random.randrange(100000)
    velmult = random.random()*.6+.4
    vel = [math.sin(dir) * velmult, math.cos(dir) * velmult]
    return vel, WINCENTER[:]


def initialize_stars():
    "creates a new starfield"
    stars = []
    for x in range(NUMSTARS):
        star = init_star()
        vel, pos = star
        steps = random.randint(0, WINCENTER[0])
        pos[0] = pos[0] + (vel[0] * steps)
        pos[1] = pos[1] + (vel[1] * steps)
        vel[0] = vel[0] * (steps * .09)
        vel[1] = vel[1] * (steps * .09)
        stars.append(star)
    move_stars(stars)
    return stars


def draw_stars(surface, stars, color):
    "used to draw (and clear) the stars"
    for vel, pos in stars:
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



    def events(self, events):
        for e in events:
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                WINCENTER[:] = list(e.pos)


    def update(self, elapsed_time):
        """ return True to let other scenes update. False to only us update.
        """
        pass

    def render(self):
        """ return rects.

            If scene.propagate_render is True, the render will
                continue to be propagated.
        """
        screen = self.screen

        white = 255, 240, 200
        # black = 20, 20, 40
        black = 0, 0, 0
        screen.fill(black)

        x = int((1024 - 768) // 2)
        key = self.ascii_lowercase[self.letter_i] + '768x768'
        if not key in self.letters:
            return []
        screen.blit(self.letters[key], (x, 0))
        # print (pause_on_letter)
        if self.pause_on_letter:
            # print('yoooooop', pause_on_letter + 1.0, time.time())
            if self.pause_on_letter + 0.7 < time.time():
                # print('finished')
                self.pause_on_letter = 0
        else:
            self.letter_i += 1
            if self.letter_i >= len(self.ascii_lowercase):
                self.letter_i = 0

            if random.randint(0, 10) == 5:
                self.pause_on_letter = time.time()

        draw_stars(screen, self.stars, black)
        move_stars(self.stars)
        draw_stars(screen, self.stars, white)
        return [self.screen.get_rect()]
