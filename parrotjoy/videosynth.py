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



DEVICENAME_INPUT = None
DEVICENAME_OUTPUT = None
# DEVICENAME_INPUT = b'Scarlett 2i4 USB'
# DEVICENAME_OUTPUT = b'Scarlett 2i4 USB'


import math
def frequency_to_midi(freqency):
    """ converts a frequency into a MIDI note.

    Rounds to the closest midi note.

    ::Examples::

    >>> frequency_to_midi(27.5)
    21
    >>> frequency_to_midi(36.7)
    26
    >>> frequency_to_midi(4186.0)
    108
    """
    return int(
        round(
            69 + (
                12 * math.log(freqency / 440.0)
            ) / math.log(2)
        )
    )

def midi_to_frequency(midi_note):
    """ Converts a midi note to a frequency.

    ::Examples::

    >>> midi_to_frequency(21)
    27.5
    >>> midi_to_frequency(26)
    36.7
    >>> midi_to_frequency(108)
    4186.0
    """
    return round(440.0 * 2 ** ((midi_note - 69) * (1./12.)), 1)


def midi_to_ansi_note(midi_note):
    """ returns the Ansi Note name for a midi number.

    ::Examples::

    >>> midi_to_ansi_note(21)
    'A0'
    >>> midi_to_ansi_note(102)
    'F#7'
    >>> midi_to_ansi_note(108)
    'C8'
    """
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    num_notes = 12
    note_name = notes[int(((midi_note - 21) % num_notes))]
    note_number = int(round(((midi_note - 21) / 11.0)))
    return '%s%s' % (note_name, note_number)




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




from pygame._sdl2 import *

class AudioRecord:
    """ The SDL2 version.
    """
    def __init__(self):
        self.audio_going = True
        self.oneset_queue = Queue()
        self.audio_queue = Queue()
        self.callback = lambda audiodevice, stream: self.on_data(audiodevice, stream)

    def on_data(self, audiodevice, audiobuffer):
        self.audio_queue.put(bytes(audiobuffer))
        #print(type(audiobuffer), len(audiobuffer))
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        # print(audiodevice)
        if self.onset(signal):
            self.oneset_queue.put(True)


        pitch = self.pitch_o(signal)[0]
        #pitch = int(round(pitch))
        if int(round(pitch)):
            confidence = self.pitch_o.get_confidence()
            # print("pitch, confidence", pitch, confidence, midi_to_ansi_note(pitch))

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
        if DEVICENAME_INPUT in justnames:
            devicename = DEVICENAME_INPUT
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





def main():

    #pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT)
    pg.mixer.pre_init(44100, 32, 2, 1024, devicename=DEVICENAME_OUTPUT, allowedchanges=0)

    pg.init()

    running = True

    audio_thread = AudioRecord()
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

        while not audio_thread.audio_queue.empty():
            # print(time.time() - time_start)
            track.update(audio_thread.audio_queue.get())

        for event in pg.event.get():
            print(event)
            if event.type == pg.QUIT:
                running = False
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

        while not audio_thread.oneset_queue.empty():
            audio_thread.oneset_queue.get()
            visuals.append(Visual(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                random.choice(colors),
                size=300
            ))

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
