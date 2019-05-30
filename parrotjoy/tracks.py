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



def make_pygame_sound(abuffer=None, array=None):
    # convert the data from float32 into int32.
    # float32_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
    if array is None:
        float32_data = np.frombuffer(abuffer, dtype=np.float32)
    else:
        float32_data = array
    stereo = np.vstack([float32_data, float32_data]).T
    #print(stereo)
    reshaped_float32_data = float32_data.reshape(-1, 1)
    stereo = np.hstack((reshaped_float32_data, reshaped_float32_data))
    # print (stereo.shape)
    # print (pg.mixer.get_init())
    asound = pg.mixer.Sound(array=stereo)
    return asound


def mix_audio(audio1, audio2):
    """ mix two pieces of audio together.

    The output should be as long as the final one.
    """

    audio_is_longer = len(audio1) >= len(audio2)
    longer_audio = audio1 if audio_is_longer else audio2
    shorter_audio = audio2 if audio_is_longer else audio1

    common_part = longer_audio[:len(shorter_audio)]
    left_overs = longer_audio[len(shorter_audio):]

    # mixed_audio = (common_part * 0.5 + shorter_audio * 0.5)
    mixed_audio = (common_part + shorter_audio)

    newaudio = np.concatenate((mixed_audio, left_overs))
    return newaudio


def trim_audio(audio, start_trim=0, end_trim=0, rate=44100, channels=1):
    """ return the audio with the start_trim, and end_trim removed.

    :param audio: a numpy array of samples.
    :param rate: samples per second.
    :param start_trim: seconds from the start of the track to use.
    :param end_trim: seconds from the end of the track to use.
    """
    if end_trim > 0:
        return audio[int(rate * start_trim):-int(rate * end_trim)]
    else:
        return audio[int(rate * start_trim):]




class Track:

    def __init__(self, bpm):
        self.bpm = bpm
        self.add_to_mode = False
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []

        self.sounds = []
        self.add_to_mode = False
        self.recording = False
        """
        recording
            - False, not recording
            - 1,     starting a new track
            - 2,     adding to
        """

        self.start_trim = 0
        """ seconds from the start of the track to use.
        """
        self.end_trim = 0
        """ seconds from the end of the track to use.
        """

        self.erased = False
        self.finished = False
        self.trimmed = False

        self._start_new_next = False
        self._add_to_next = False

    def start_new_next(self):
        print("track: start_new_next")
        self._start_new_next = True
        self.recording = 1
    def add_to_next(self):
        print("track: add_to_next")
        self._add_to_next = True
        self.recording = 1

    def start_new(self):
        print("track: start_new")
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []
        self.sounds = []
        self.add_to_mode = False
        self.recording = 2

    def add_to(self):
        print("track: add_to")
        self.frames_add_to = []
        self.add_to_mode = True
        self.recording = 2

    def handle_start_new_next(self):
        # handle add_to_next() and start_new_next() calls.
        # We start them on the first beat of the loop.
        # print("handle_start_new_next", self.bpm.first_beat, self.bpm.started_beat)
        if self.bpm is not None:
            if self.bpm.first_beat and self.bpm.started_beat:
                if self._start_new_next:
                    self.start_new()
                    self._start_new_next = False
                if self._add_to_next:
                    self.add_to()
                    self._add_to_next = False

    def erase(self):
        print("track: erase")
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []
        self.sounds = []
        self.add_to_mode = False
        self.recording = False
        self.erased = True
        self.trimmed = False

    def trim_audio(self, start=0, end=0):
        self.start_trim += start
        self.end_trim += end
        if self.end_trim - 0.000001 < 0:
            self.end_trim = 0
        if self.end_trim > 2:
            # TODO: if end_trim > sound_length
            self.end_trim = 2


        if self.start_trim - 0.000001 < 0:
            self.start_trim = 0
        if self.start_trim > 2:
            # TODO: if start_trim > sound_length
            self.start_trim = 2


        print("trim_audio", start, end, self.start_trim, self.end_trim)
        if len(self.audios_untrimmed):
            frames = self.audios_untrimmed[0]
        else:
            frames = self.audios[0]

        audio = np.frombuffer(frames, dtype=np.float32)
        trimmed_audio = trim_audio(audio, self.start_trim, self.end_trim)
        self.sounds = [
            make_pygame_sound(array=trimmed_audio)
        ]
        if not len(self.audios_untrimmed):
            self.audios_untrimmed = self.audios[:]

        self.audios = [trimmed_audio.tobytes()]
        self.trimmed = True

    def finish(self):
        print("track: finish")
        self.recording = False
        # print(f'duration_seconds:{audio.duration_seconds}')
        if self.add_to_mode:
            all_frames = b''.join(self.frames_add_to)
        else:
            all_frames = b''.join(self.frames)

        self.audios.append(all_frames)

        if self.add_to_mode:
            audio1 = np.frombuffer(self.audios[0], dtype=np.float32)
            if len(self.audios) == 2:
                audio2 = np.frombuffer(self.audios[1], dtype=np.float32)
                mixed_audio = mix_audio(audio1, audio2)
            else:
                mixed_audio = mix_audio(audio1, audio1)
            self.audios = [mixed_audio.tobytes()]
            self.sounds = [
                make_pygame_sound(array=mixed_audio)
            ]
        else:
            self.sounds = [make_pygame_sound(all_frames)]
        self.add_to_mode = False
        self.finished = True


    def play(self):
        for sound in self.sounds:
            sound.play()

    def stop(self):
        for sound in self.sounds:
            sound.stop()

    def update(self, audiobuffer):
        # print(f'id: {id(audiobuffer)}')
        if self.recording:
            if self.recording == 2 and audiobuffer is not None:
                if self.add_to_mode:
                    self.frames_add_to.append(audiobuffer)
                else:
                    self.frames.append(audiobuffer)
        if self.erased:
            self.erased = False
        if self.trimmed:
            self.trimmed = False
        if self.finished:
            print("update: finished")
            self.finished = False

        self.handle_start_new_next()


