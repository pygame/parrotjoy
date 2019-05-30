import sys
import io
import random
import math
from threading import Thread
from queue import Queue
import time


import numpy as np
import aubio
import pygame as pg
pygame = pg

from tracks import Track
from audiorecord import AudioRecord, PITCHES, ONSETS, AUDIOS


DEVICENAME_INPUT = None
DEVICENAME_OUTPUT = None
# DEVICENAME_INPUT = b'Scarlett 2i4 USB'
# DEVICENAME_OUTPUT = b'Scarlett 2i4 USB'


from pygame.midi import frequency_to_midi, midi_to_frequency, midi_to_ansi_note


def main():

    #pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT)
    pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT, allowedchanges=0)

    pg.init()

    running = True

    audio_thread = AudioRecord(inputdevice=DEVICENAME_INPUT)
    audio_thread.start()

    track = Track(None)

    screen_width, screen_height = 640, 480
    screen = pg.display.set_mode((screen_width, screen_height))

    class Visual(object):
        def __init__(self, x, y, color, size):
            self.x = x
            self.y = y
            self.color = color
            self.size = size

        def update(self):
            self.size -= 6
            return self

    colors = [ (random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)) for x in range(10)]
    visuals = []

    clock = pg.time.Clock()
    time_start = time.time()

    while running:

        # while not audio_thread.audio_queue.empty():
        #     # print(time.time() - time_start)
        #     track.update(audio_thread.audio_queue.get())
        audio_thread.update()

        for event in pg.event.get():
            # print(event)
            if event.type == pg.QUIT:
                running = False
            elif event.type == PITCHES:
                pass
            elif event.type == ONSETS:
                for onset in event.onsets:
                    visuals.append(Visual(
                        random.randint(0, screen_width),
                        random.randint(0, screen_height),
                        random.choice(colors),
                        size=300
                    ))

            elif event.type == AUDIOS:
                for audio in event.audios:
                    track.update(audio)

            if event.type == pg.KEYDOWN:
                if event.unicode == 'q':
                    running = False
                if event.unicode == 'z':
                    audio_thread.audio_going = False
                if event.unicode == 's':
                    track.start_new()
                if event.unicode == 'S':
                    track.add_to()
                if event.unicode == 'p':
                    track.play()

                if event.unicode == 'f':
                    track.finish()
                    # if track.sounds:
                    #     for sound in track.sounds[-5]:
                    #         sound.play()


        screen.fill((0, 0, 0))
        new_visuals = []
        for place, visual in enumerate(visuals):
            if visual.size > 2:
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], 0, math.pi/2, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], math.pi/2, math.pi, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], math.pi,3*math.pi/2, 2)
                pg.draw.arc(screen, visual.color, [visual.x, visual.y, visual.size, visual.size], 3*math.pi/2, 2*math.pi, 2)

                new_visuals.append(visual.update())

        visuals = new_visuals

        fps = clock.tick(30)
        pg.display.flip()
        # print(f'{fps}')

    audio_thread.audio_going = False



if __name__ == '__main__':
    main()
    pg.display.quit()
