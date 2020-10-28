"""Recording audio and doing some analysis on it as we go.
"""
# pylint: disable=no-member
from queue import Queue

import numpy as np
import aubio
import pygame as pg
from pygame.midi import (
    midi_to_frequency,
    midi_to_ansi_note,
)
from pygame._sdl2 import (  # pylint: disable=no-name-in-module
    AUDIO_F32,
    get_audio_device_names,
    AudioDevice,
    AUDIO_ALLOW_FORMAT_CHANGE,
)


AUDIOS = pg.event.custom_type()
ONSETS = pg.event.custom_type()
PITCHES = pg.event.custom_type()


class MusicInfo:
    """For finding pitch changes, and onsets in audio.

    It posts these event types to the pygame event queue:
    - PITCHES (pitches, notes, frequencies)
    - ONSETS (onsets)
    """

    def __init__(self, frequency):
        self.pitch_queue = Queue()
        self.onset_queue = Queue()

        # onset detection.
        win_s = 1024
        hop_s = win_s // 2
        self.onset = aubio.onset("default", win_s, hop_s, frequency)

        tolerance = 0.8
        self.pitch_o = aubio.pitch("yin", win_s, hop_s, frequency)
        self.pitch_o.set_unit("midi")
        self.pitch_o.set_tolerance(tolerance)

    def on_data(self, signal):
        """For when we get data.

        Might run in a different thread at a high rate.
        """
        pitch = self.pitch_o(signal)[0]
        # pitch = int(round(pitch))
        if int(round(pitch)):
            # confidence = self.pitch_o.get_confidence()
            # print("pitch, confidence", pitch, confidence, midi_to_ansi_note(pitch))
            self.pitch_queue.put(pitch)

        onset = self.onset(signal)
        if onset > 1:
            # print("%f" % self.onset.get_last_s())
            self.onset_queue.put(True)

    def update(self):
        """Update every frame tick."""
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
            pg.event.post(
                pg.event.Event(
                    PITCHES, pitches=pitches, notes=notes, frequencies=frequencies
                )
            )

        onsets = []
        while not self.onset_queue.empty():
            onsets.append(self.onset_queue.get())

        if onsets:
            pg.event.post(pg.event.Event(ONSETS, onsets=onsets))


class AudioRecord:
    """Recording audio and doing some analysis on it as we go.

    It looks for onsets (beats), pitch detection (notes, and midi frequencies)
    """

    def __init__(self, inputdevice):
        self.audio_device = None
        self.inputdevice = inputdevice
        self.audio_going = True
        self.audio_queue = Queue()
        self.music_info = None

        self.callback = lambda audiodevice, stream: self.on_data(  # pylint: disable=unnecessary-lambda
            audiodevice, stream
        )

    def start(self):
        """Start listening to audio."""
        frequency = 44100

        just_names = get_audio_device_names(iscapture=1)
        print(just_names)
        devicename = (
            self.inputdevice if self.inputdevice in just_names else just_names[0]
        )
        print(f"Using: {devicename}")

        self.music_info = MusicInfo(frequency)

        self.audio_device = AudioDevice(
            devicename=devicename,
            iscapture=1,
            frequency=frequency,
            audioformat=AUDIO_F32,
            numchannels=1,
            chunksize=512,
            allowed_changes=AUDIO_ALLOW_FORMAT_CHANGE,
            callback=self.callback,
        )

        self.audio_device.pause(0)

    def update(self):
        """To be called in a pygame event loop."""
        audios = []
        while not self.audio_queue.empty():
            # print('-----audio from queue')
            # print(time.time() - time_start)
            audios.append(self.audio_queue.get())

        if audios:
            pg.event.post(pg.event.Event(AUDIOS, audios=audios))

        self.music_info.update()

    def on_data(self, audiodevice, audiobuffer):
        """For when we get data.

        Might run in a different thread at a high rate.
        """
        # print(audiodevice)
        assert audiodevice
        self.audio_queue.put(bytes(audiobuffer))
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        self.music_info.on_data(signal)

    def __del__(self):
        self.audio_device.pause(1)
        self.audio_device.close()
