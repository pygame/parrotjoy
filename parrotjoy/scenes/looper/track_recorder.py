"""Controlling a track recorder. With joystick and keyboard,
"""
import time

import pygame as pg

from ...metronome import Bpm
from ...tracks import Track

# from ...audiorecord import PITCHES, ONSETS, AUDIOS
from ...audiorecord import AUDIOS, AudioRecord


JOY_SELECT = 8
JOY_START = 9
JOY_1 = 0
JOY_2 = 1
JOY_3 = 2
JOY_4 = 3
JOY_R1 = 5
JOY_R2 = 7
JOY_L1 = 4
JOY_L2 = 6

TRIM_AMOUNT = 0.1


class Joy:
    """For keeping track of if joy buttons were pressed down."""

    def __init__(self):
        self.joys = {}
        self.joys[0] = {}
        self.joys[0]["buttons"] = {}
        for button_num in range(20):
            self.joys[0]["buttons"][button_num] = 0

    def events(self, events):
        """Looks for JOYBUTTONDOWN and JOYBUTTONUP events."""
        for event in events:
            if event.type == pg.JOYBUTTONDOWN:
                self.joys[0]["buttons"][event.button] = 1
            if event.type == pg.JOYBUTTONUP:
                self.joys[0]["buttons"][event.button] = 0


class TrackRecorder:
    """For recording, and playing back different tracks."""

    def __init__(self, audio_thread: AudioRecord):

        self.audio_thread = audio_thread

        # busy loop until we get some sound coming in.
        # This syncs the 'bpm' timer to the sound input.
        while 1:
            if not self.audio_thread.audio_queue.empty():
                self.bpm = Bpm()
                break
            time.sleep(0.0001)

        self.tracks = [Track(self.bpm) for x in range(4)]
        self.track_idx = 0
        self.track = self.tracks[self.track_idx]

        self.joys = Joy()
        self.playing = False
        """ True if we should play the sounds.
        """

    def play(self):
        """Plays the audio for the tracks."""
        print("TrackRecorder: play")
        if self.playing:
            first_two_tracks = self.tracks[:2]
            for track in first_two_tracks:
                print(track.sounds)
                for sound in track.sounds:
                    sound.play()
                    # print(
                    #     self.bpm.time_since_start(0.0),
                    #     sound.get_length(),
                    #     self.bpm._elapsed_time,
                    #     self.bpm.get_time_for_loop(),
                    # )

    def start(self):
        """Tell it to start playing the sounds."""
        self.stop()
        self.playing = True
        self.bpm.start_at_beginning()

    def stop(self):
        """Tell it to STOP playing the sounds."""
        self.playing = False
        for track in self.tracks:
            for sound in track.sounds:
                sound.stop()

    def trim_audio(self, start: int = 0, end: int = 0):
        """Trims the audio for the selected track."""
        track = self.tracks[self.track_idx]
        track.trim_audio(start=start, end=end)
        track.stop()
        track.play()

    def _event_joy_axis_motion(self, event):
        """Used by events() to handle the joy related events."""
        if event.axis == 0 and event.value < -0.01:
            # lpaddle left
            self.trim_audio(start=-TRIM_AMOUNT)
        elif event.axis == 0 and event.value >= 0.01:
            # lpaddle right
            self.trim_audio(start=TRIM_AMOUNT)
        elif event.axis == 2 and event.value < -0.01:
            # rpaddle left
            self.trim_audio(end=TRIM_AMOUNT)
        elif event.axis == 2 and event.value >= 0.01:
            # rpaddle right
            self.trim_audio(end=-TRIM_AMOUNT)

    def _event_joy_button_down(self, event):
        """Used by events() to handle the joy related events."""
        track_buttons = [JOY_1, JOY_2, JOY_3, JOY_4]
        if event.button in track_buttons:
            track_idx = track_buttons.index(event.button)
            track = self.tracks[track_idx]
            self.track_idx = track_idx

            joy_buttons = self.joys.joys[0]["buttons"]

            if joy_buttons[JOY_R1]:
                track.start_new_next()
            elif joy_buttons[JOY_R2]:
                track.add_to_next()
            elif joy_buttons[JOY_L1]:
                track.erase()
                if track_idx == 0:
                    self.bpm.init(70, 60 / 70.0)
            elif track.recording:
                # r1, r2, l1 not pressed, we are recording.
                if track.recording == 2:
                    track.finish()
            else:
                track.play()

        elif event.button == JOY_SELECT:
            self.stop()
        elif event.button == JOY_START:
            self.start()
            # self.track.add_to()
            # self.track.finish()

    def _event_key_down(self, event):
        if event.key == pg.K_z:
            self.audio_thread.audio_going = False
        elif event.key == pg.K_s:
            self.track.start_new_next()
        elif event.key == pg.K_s and pg.key.get_mods() & pg.KMOD_SHIFT:
            self.track.add_to_next()
        elif event.key == pg.K_p:
            self.track.play()
        elif event.key == pg.K_f:
            self.track.finish()
            # if track.sounds:
            #     for sound in track.sounds[-5]:
            #         sound.play()
        elif event.key == pg.K_w:
            self.trim_audio(start=-TRIM_AMOUNT)
        elif event.key == pg.K_e:
            self.trim_audio(start=TRIM_AMOUNT)
        elif event.key == pg.K_r:
            self.trim_audio(end=TRIM_AMOUNT)
        elif event.key == pg.K_t:
            self.trim_audio(end=-TRIM_AMOUNT)

    def events(self, events):
        """Update the tracks based on user input."""

        self.bpm.update()

        # update the tracks because sometimes there is no audio
        for track in self.tracks:
            track.update(None)

        self.joys.events(events)

        for event in events:
            if event.type == AUDIOS:
                for audio in event.audios:
                    for track in self.tracks:
                        track.update(audio)
            elif event.type == pg.KEYDOWN:
                self._event_key_down(event)
            elif event.type == pg.JOYAXISMOTION:
                self._event_joy_axis_motion(event)
            elif event.type == pg.JOYBUTTONDOWN:
                self._event_joy_button_down(event)

        self._track_starting_ending_changing()

    def _track_starting_ending_changing(self):
        """When the track starts, ends or is changed (trimmed).

        We can start it again if it's finished or changed.
        We can play the sound again when it's time to play it.
        """
        # if the first track was just finished, we see how big it is.
        track_finished_or_trimmed = (
            self.tracks[0].finished or self.tracks[0].trimmed
        ) or (self.tracks[1].finished or self.tracks[1].trimmed)
        if track_finished_or_trimmed:
            # get the longest of the two looping tracks.
            sound_length1 = 0
            sound_length2 = 0
            if self.tracks[0].sounds:
                sound_length1 = self.tracks[0].sounds[0].get_length()
            if self.tracks[1].sounds:
                sound_length2 = self.tracks[1].sounds[0].get_length()

            sound_length = max(sound_length1, sound_length2)

            space_between_beats = sound_length / 4.0
            bpm = 60 / space_between_beats
            self.bpm.init(bpm, space_between_beats)
            self.start()

        should_play_at_start = self.bpm.started_beat and self.bpm.first_beat
        if should_play_at_start:
            self.play()
