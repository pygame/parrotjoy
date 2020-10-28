import numpy as np
from numpy.typing import NDArray
import pygame as pg

# pylint: disable=too-many-instance-attributes

RECORDING_NOT = False
RECORDING_STARTING_A_NEW_TRACK = 1
RECORDING_ADDING_TO = 2


def make_pygame_sound(abuffer=None, array=None) -> pg.mixer.Sound:
    """From abuffer or array create a pyagme sound.

    We assume the passed in data is a mono track.

    The sound returned is in stereo.

    :param abuffer: to create the sound from
    :param array: to create the sound from
    """
    # convert the data from float32 into int32.
    # float32_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
    if array is None:
        float32_data = np.frombuffer(abuffer, dtype=np.float32)
    else:
        float32_data = array
    stereo = np.vstack([float32_data, float32_data]).T
    # print(stereo)
    reshaped_float32_data = float32_data.reshape(-1, 1)
    stereo = np.hstack((reshaped_float32_data, reshaped_float32_data))
    # print (stereo.shape)
    # print (pg.mixer.get_init())
    asound = pg.mixer.Sound(array=stereo)
    return asound


def mix_audio(
    audio1: NDArray[np.float32], audio2: NDArray[np.float32]
) -> NDArray[np.float32]:
    """mix two pieces of audio together.

    The output should be as long as the final one.
    """

    audio_is_longer = len(audio1) >= len(audio2)
    longer_audio = audio1 if audio_is_longer else audio2
    shorter_audio = audio2 if audio_is_longer else audio1

    common_part = longer_audio[: len(shorter_audio)]
    left_overs = longer_audio[len(shorter_audio) :]

    # mixed_audio = (common_part * 0.5 + shorter_audio * 0.5)
    mixed_audio = common_part + shorter_audio

    newaudio = np.concatenate((mixed_audio, left_overs))
    return newaudio


def trim_audio(audio: NDArray[np.float32], start_trim=0, end_trim=0, rate=44100):
    """return the audio with the start_trim, and end_trim removed.

    :param audio: a numpy array of samples.
    :param start_trim: seconds from the start of the track to use.
    :param end_trim: seconds from the end of the track to use.
    :param rate: samples per second.
    """
    if end_trim > 0:
        return audio[int(rate * start_trim) : -int(rate * end_trim)]
    return audio[int(rate * start_trim) :]


class Track:
    def __init__(self, bpm):
        self.bpm = bpm
        self.add_to_mode = False
        """
            - True, recording adds to the existing track.
            - False, recording starts fresh.
        """
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []

        self.sounds = []
        self.recording: RECORDING_NOT | RECORDING_STARTING_A_NEW_TRACK | RECORDING_ADDING_TO = (
            False
        )
        """ The recording state.
        - RECORDING_NOT
        - RECORDING_STARTING_A_NEW_TRACK
        - RECORDING_ADDING_TO
        """

        self.start_trim = 0
        """ seconds from the start of the track to use.
        """
        self.end_trim = 0
        """ seconds from the end of the track to use.
        """

        self.erased = False
        """ If the track was erased this tick.
        """

        self.finished = False
        """ If the track is finished this tick.
        """
        self.trimmed = False
        """ If the track is trimmed this tick.
        """

        self._start_new_next = False
        self._add_to_next = False

        self.frames_add_to = []

    def start_new_next(self):
        "On the first beat of the loop start a new track."
        print("track: start_new_next")
        self._start_new_next = True
        self.recording = RECORDING_STARTING_A_NEW_TRACK

    def add_to_next(self):
        "On the first beat of the loop turn to add to mode."
        print("track: add_to_next")
        self._add_to_next = True
        self.recording = RECORDING_STARTING_A_NEW_TRACK

    def start_new(self):
        "Start a whole new track, resetting things."
        print("track: start_new")
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []
        self.sounds = []
        self.add_to_mode = False
        self.recording = RECORDING_ADDING_TO

    def add_to(self):
        "Switch to add to mode, where audio is added onto existing audio"
        print("track: add_to")
        self.frames_add_to = []
        self.add_to_mode = True
        self.recording = RECORDING_ADDING_TO

    def update_start_new_next(self):
        """Handle add_to_next() and start_new_next() calls.
        We start them on the first beat of the loop.
        """
        # print("update_start_new_next", self.bpm.first_beat, self.bpm.started_beat)
        if self.bpm is not None:
            if self.bpm.first_beat and self.bpm.started_beat:
                if self._start_new_next:
                    self.start_new()
                    self._start_new_next = False
                if self._add_to_next:
                    self.add_to()
                    self._add_to_next = False

    def erase(self):
        "erase all the audio for the track, and reset"
        print("track: erase")
        self.frames = []
        self.audios = []
        self.audios_untrimmed = []
        self.sounds = []
        self.add_to_mode = False
        self.recording = RECORDING_NOT
        self.erased = True
        self.trimmed = False

    def trim_audio(self, start=0, end=0):
        """Trim the audio with some offsets.

        :param start: where to start trimming from
        :param end: where to end trimming from
        """
        self.start_trim += start
        self.end_trim += end
        if self.end_trim - 0.000001 < 0:
            self.end_trim = 0
        self.end_trim = min(self.end_trim, 2)

        if self.start_trim - 0.000001 < 0:
            self.start_trim = 0
        self.start_trim = min(self.start_trim, 2)

        print("trim_audio", start, end, self.start_trim, self.end_trim)
        if self.audios_untrimmed:
            frames = self.audios_untrimmed[0]
        else:
            frames = self.audios[0]

        audio = np.frombuffer(frames, dtype=np.float32)
        trimmed_audio = trim_audio(audio, self.start_trim, self.end_trim)
        self.sounds = [make_pygame_sound(array=trimmed_audio)]
        if not self.audios_untrimmed:
            self.audios_untrimmed = self.audios[:]

        self.audios = [trimmed_audio.tobytes()]
        self.trimmed = True

    def finish(self):
        """Finish recording the track, mix it, then either...

        - create a new sound
        - add to the existing one
        """
        print("track: finish")
        self.recording = RECORDING_NOT
        # print(f'duration_seconds:{audio.duration_seconds}')
        if self.add_to_mode:
            all_frames = b"".join(self.frames_add_to)
        else:
            all_frames = b"".join(self.frames)

        self.audios.append(all_frames)

        if self.add_to_mode:
            audio1 = np.frombuffer(self.audios[0], dtype=np.float32)
            if len(self.audios) == 2:
                audio2 = np.frombuffer(self.audios[1], dtype=np.float32)
                mixed_audio = mix_audio(audio1, audio2)
            else:
                mixed_audio = mix_audio(audio1, audio1)
            self.audios = [mixed_audio.tobytes()]
            self.sounds = [make_pygame_sound(array=mixed_audio)]
        else:
            self.sounds = [make_pygame_sound(all_frames)]
        self.add_to_mode = False
        self.finished = True

    def play(self):
        "play all the sounds"
        for sound in self.sounds:
            sound.play()

    def stop(self):
        "stop all the sounds"
        for sound in self.sounds:
            sound.stop()

    def update(self, audiobuffer):
        "with a new audiobuffer"
        # print(f'id: {id(audiobuffer)}')
        if self.recording:
            if self.recording == RECORDING_ADDING_TO and audiobuffer is not None:
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

        self.update_start_new_next()
