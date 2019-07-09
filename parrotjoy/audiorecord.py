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
from pygame.midi import frequency_to_midi, midi_to_frequency, midi_to_ansi_note
pygame = pg

from pygame._sdl2 import *

AUDIOS = pg.locals.USEREVENT + 12
ONSETS = pg.locals.USEREVENT + 13
PITCHES = pg.locals.USEREVENT + 14


class AudioRecord:
    """ The SDL2 version.
    """
    def __init__(self, inputdevice):
        self.inputdevice = inputdevice
        self.audio_going = True
        self.oneset_queue = Queue()
        self.audio_queue = Queue()
        self.pitch_queue = Queue()

        self.callback = lambda audiodevice, stream: self.on_data(audiodevice, stream)

    def update(self):
        """ To be called in a pygame event loop.
        """
        audios = []
        while not self.audio_queue.empty():
            # print('-----audio from queue')
            # print(time.time() - time_start)
            audio = self.audio_queue.get()
            audios.append(audio)

        if audios:
            pg.event.post(pg.event.Event(AUDIOS, audios=audios))

        onsets = []
        while not self.oneset_queue.empty():
            onsets.append(self.oneset_queue.get())

        if onsets:
            pg.event.post(pg.event.Event(ONSETS, onsets=onsets))

        pitches = []
        notes = []
        frequencies = []
        while not self.pitch_queue.empty():

            # print("pitch, confidence", pitch, confidence, midi_to_ansi_note(pitch))
            pitch = self.pitch_queue.get()
            pitches.append(pitch)
            notes.append(midi_to_ansi_note(pitch))
            frequencies.append(midi_to_frequency(pitch))

        if pitches:
            pg.event.post(pg.event.Event(PITCHES, pitches=pitches, notes=notes, frequencies=frequencies))






    def on_data(self, audiodevice, audiobuffer):
        self.audio_queue.put(bytes(audiobuffer))
        #print(type(audiobuffer), len(audiobuffer))
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        # print(audiodevice)
        onset = self.onset(signal)
        if onset > 1:
            # print("%f" % self.onset.get_last_s())
            self.oneset_queue.put(True)


        pitch = self.pitch_o(signal)[0]
        #pitch = int(round(pitch))
        if int(round(pitch)):
            confidence = self.pitch_o.get_confidence()
            # print("pitch, confidence", pitch, confidence, midi_to_ansi_note(pitch))
            self.pitch_queue.put(pitch)

    def start(self):
        FORMAT = AUDIO_F32
        CHANNELS = 1
        RATE = 44100
        CHUNK = 512

        iscapture = 1

        names = [(x, get_audio_device_name(x, 1))
                 for x in range(get_num_audio_devices(iscapture))]
        justnames = [get_audio_device_name(x, 1)
                     for x in range(get_num_audio_devices(iscapture))]
        print(names)
        if self.inputdevice in justnames:
            devicename = self.inputdevice
        else:
            devicename = justnames[0]
        print(f"Using: {devicename}")


        # onset detection.
        win_s = 1024
        hop_s = win_s // 2
        self.onset = aubio.onset("default", win_s, hop_s, RATE)


        tolerance = 0.8
        self.pitch_o = aubio.pitch("yin", win_s, hop_s, RATE)
        self.pitch_o.set_unit("midi")
        self.pitch_o.set_tolerance(tolerance)


        self.audio_device = AudioDevice(
            devicename=devicename,
            iscapture=1,
            frequency=RATE,
            audioformat=AUDIO_F32,
            numchannels=CHANNELS,
            chunksize=CHUNK,
            allowed_changes=AUDIO_ALLOW_FORMAT_CHANGE,
            callback=self.callback,
        )

        self.audio_device.pause(0)

    def __del__(self):
        self.audio_device.pause(1)
        self.audio_device.close()
