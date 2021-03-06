import os
import sys
import io
import random
from threading import Thread
from queue import Queue
import time


import numpy as np
import aubio
import pygame as pg
pygame = pg

from parrotjoy.metronome import Bpm, BpmCounter, BpmLight, BpmLine
from parrotjoy.audiorecord import PITCHES, ONSETS, AUDIOS
from parrotjoy.draw_sound import draw_wave
from parrotjoy.camera_cv import VideoThread
from parrotjoy.tracks import Track
from parrotjoy.resources import gfx


class Joy:
    """ For keeping track of if joy buttons were pressed down.
    """
    def __init__(self):
        self.joys = {}
        self.joys[0] = {}
        self.joys[0]['buttons'] = {}
        for x in range(20):
            self.joys[0]['buttons'][x] = 0

    def events(self, events):
        for e in events:
            if e.type == pg.JOYBUTTONDOWN:
                self.joys[0]['buttons'][e.button] = 1
            if e.type == pg.JOYBUTTONUP:
                self.joys[0]['buttons'][e.button] = 0


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


class TrackRecorder:
    """ For recording, and playing back different tracks.
    """
    def __init__(self, audio_thread):


        self.audio_thread = audio_thread


        # busy loop until we get some sound coming in.
        # This syncs the 'bpm' timer to the sound input.
        found = False
        while 1:
            if not self.audio_thread.audio_queue.empty():
                self.bpm = Bpm()
                break
            time.sleep(0.0001)

        self.tracks = [Track(self.bpm) for x in range(4)]
        self.track_idx = 0
        self.track = self.tracks[self.track_idx]

        self.joys = Joy()
        self.joy_buttons = self.joys.joys[0]['buttons']
        self.playing = False
        """ True if we should play the sounds.
        """


    def play(self):
        print("TrackRecorder: play")
        if self.playing:
            first_two_tracks = self.tracks[:2]
            for track in first_two_tracks:
                print(track.sounds)
                for sound in track.sounds:
                    channel = sound.play()
                    # channel.set_endevent(pg.USEREVENT+2)
                    print(self.bpm.time_since_start(0.0), sound.get_length(), self.bpm._elapsed_time, self.bpm.get_time_for_loop())

    def start(self):
        """ Tell it to start playing the sounds.
        """
        self.stop()
        self.playing = True
        self.bpm.start_at_beginning()


    def stop(self):
        """ Tell it to STOP playing the sounds.
        """
        self.playing = False
        for track in self.tracks:
            for sound in track.sounds:
                sound.stop()

    def event_joy(self, e):
        track_buttons = [JOY_1, JOY_2, JOY_3, JOY_4]
        if e.type == pg.JOYBUTTONDOWN and e.button in track_buttons:
            track_idx = track_buttons.index(e.button)
            track = self.tracks[track_idx]
            self.track_idx = track_idx
            if self.joy_buttons[JOY_R1]:
                track.start_new_next()
            elif self.joy_buttons[JOY_R2]:
                track.add_to_next()
            elif self.joy_buttons[JOY_L1]:
                track.erase()
                if track_idx == 0:
                    self.bpm.init(70, 60/70.0)
            elif track.recording:
                # r1, r2, l1 not pressed, we are recording.
                if track.recording == 2:
                    track.finish()
            else:
                track.play()


    def trim_audio(self, start=0, end=0):
        track = self.tracks[self.track_idx]
        track.trim_audio(start=start, end=end)
        track.stop()
        track.play()


    def events(self, events):

        # print('bpm updating...')
        self.bpm.update()

        # update the tracks because sometimes there is no audio
        for track in self.tracks:
            track.update(None)

        self.joys.events(events)

        for e in events:
            # print("events", e)
            if e.type == pg.QUIT:
                running = False
            elif e.type == PITCHES:
                for pitch in e.pitches:
                    pass
            elif e.type == ONSETS:
                for onset in e.onsets:
                    pass
            elif e.type == AUDIOS:
                for audio in e.audios:
                    for track in self.tracks:
                        track.update(audio)

            if e.type == pg.KEYDOWN:
                if e.key == pg.K_z:
                    self.audio_thread.audio_going = False
                if e.key == pg.K_s:
                    self.track.start_new_next()
                if e.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.track.add_to_next()
                if e.key == pg.K_p:
                    self.track.play()
                if e.key == pg.K_f:
                    self.track.finish()
                    # if track.sounds:
                    #     for sound in track.sounds[-5]:
                    #         sound.play()
                if e.key == pg.K_w:
                    self.trim_audio(start=-TRIM_AMOUNT)
                if e.key == pg.K_e:
                    self.trim_audio(start=TRIM_AMOUNT)
                if e.key == pg.K_r:
                    self.trim_audio(end=TRIM_AMOUNT)
                if e.key == pg.K_t:
                    self.trim_audio(end=-TRIM_AMOUNT)

            self.event_joy(e)

            if e.type == pg.JOYAXISMOTION:
                if e.axis == 0 and e.value < -0.01:
                    # lpaddle left
                    self.trim_audio(start=-TRIM_AMOUNT)
                elif e.axis == 0 and e.value >= 0.01:
                    # lpaddle right
                    self.trim_audio(start=TRIM_AMOUNT)
                elif e.axis == 2 and e.value < -0.01:
                    #rpaddle left
                    self.trim_audio(end=TRIM_AMOUNT)
                elif e.axis == 2 and e.value >= 0.01:
                    #rpaddle right
                    self.trim_audio(end=-TRIM_AMOUNT)


            if e.type == pg.JOYBUTTONDOWN and e.button == JOY_SELECT:
                self.stop()
            if e.type == pg.JOYBUTTONDOWN and e.button == JOY_START:
                self.start()
                pass
                # self.track.add_to()
                # self.track.finish()

            if e.type == pg.JOYBUTTONUP:
                pass
                # self.joys[0]['buttons'][e.button] = 0

        # if the first track was just finished, we see how big it is.
        if ((self.tracks[0].finished or self.tracks[0].trimmed) or
            (self.tracks[1].finished or self.tracks[1].trimmed)):
            # get the longest of the two looping tracks.
            sound_length1 = 0
            sound_length2 = 0
            if self.tracks[0].sounds:
                sound_length1 = self.tracks[0].sounds[0].get_length()
            if self.tracks[1].sounds:
                sound_length2 = self.tracks[1].sounds[0].get_length()

            sound_length = max(sound_length1, sound_length2)

            space_between_beats = sound_length / 4.
            bpm = 60 / space_between_beats
            self.bpm.init(bpm, space_between_beats)
            self.start()


class RecordingWave(pg.sprite.DirtySprite):
    """ Shows a
    """
    def __init__(self, track, track_idx):
        pg.sprite.DirtySprite.__init__(self)
        self.track = track
        self.track_idx = track_idx

        # how many pixels wide for how many seconds?
        self.full_width_seconds = 5
        self.wave_width = 320

        self.image_height = 130
        self.background_color = (0, 0, 0)
        self.image = pg.Surface((320, self.image_height)).convert()
        self.image.fill(self.background_color)
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 70 + (self.track_idx * self.image_height)
        self.state = None

    def draw_wave(self):

        # How big should the image be?
        #    Depends on how much sound is recorded.
        sound_length = self.track.sounds[0].get_length()
        image_width = self.wave_width / self.full_width_seconds * sound_length
        self.image = pg.Surface((image_width, self.image_height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 70 + (self.track_idx * self.image_height)


        float32_data = np.frombuffer(self.track.audios[0], dtype=np.float32)
        int16_data = ((float32_data / 1.414) * pow(2, 16) // 2).astype(np.int16)
        samples = int16_data

        draw_wave(
            self.image,
            samples,
            background_color=self.background_color,
            wave_color=(255, 255, 255))


    def update(self):
        """
        """
        # print("RecordingWave: self.track.recording, self.state, self.track.recording, self.track.add_to_mode")
        # print(self.track.recording, self.state, self.track.recording, self.track.add_to_mode)
        if self.track.recording == 2 and (not self.track.add_to_mode) and self.state != 'recording':
            print('WAVE: recording')
            self.image.fill((0, 0, 0))
            self.dirty = 1
            self.state = 'recording'
        elif self.track.add_to_mode and self.state != 'add_to_mode':
            print('WAVE: add_to_mode')
            self.state = 'add_to_mode'
        elif (
            (not (self.track.recording or self.track.add_to_mode)) and
            self.state in ['add_to_mode', 'recording']
        ):
            print('WAVE: update wave')
            if self.track.sounds and self.track.sounds[0]:
                self.draw_wave()
            self.dirty = 1
            self.state = None
        elif self.track.erased:
            print('WAVE: erased')
            self.image.fill((0, 0, 0))
            self.dirty = 1
        elif self.track.trimmed:
            print('WAVE: trimmed')
            if self.track.sounds and self.track.sounds[0]:
                self.draw_wave()
            self.dirty = 1
            self.state = None


class RecordingLight(pg.sprite.DirtySprite):
    """ Shows a red 'light' representing each beat.
    """
    def __init__(self, track, track_idx):
        pg.sprite.DirtySprite.__init__(self)
        self.track = track
        self.track_idx = track_idx

        self.image = pg.Surface((20, 20))
        self.image.fill((25, 25, 25))
        self.rect = self.image.get_rect().copy()
        self.rect.x = 50 + (track_idx * 30)
        self.rect.y = 30
        self.state = None

    def update(self):

        if self.track.recording == 1 and (not self.track.add_to_mode) and self.state != 'preparing':
            self.image.fill((0, 0, 255))
            self.dirty = 1
            self.state = 'preparing'
        elif self.track.recording == 2 and (not self.track.add_to_mode) and self.state != 'recording':
            self.image.fill((0, 255, 255))
            self.dirty = 1
            self.state = 'recording'
        elif self.track.add_to_mode and self.state != 'add_to_mode':
            self.image.fill((0, 255, 0))
            self.dirty = 1
            self.state = 'add_to_mode'
        elif (
            (not (self.track.recording or self.track.add_to_mode)) and
            self.state in ['add_to_mode', 'recording']
        ):
            self.image.fill((25, 25, 25))
            self.dirty = 1
            self.state = None
        # print (self.state, self.track.recording, self.track.add_to_mode)


class Parrot(pg.sprite.DirtySprite):
    """
    """
    def __init__(self):
        pg.sprite.DirtySprite.__init__(self)
        self.image = gfx('parrotjoy-logo.png')
        self.rect = self.image.get_rect().copy()
        self.rect.x = pg.display.get_surface().get_width() - self.rect.width
        self.rect.y = 20
        # self.dirty = 1


class Gif:
    def __init__(self):
        self.path = '/tmp/'
        self.start_saving = False
        self.finished_saving = False
        self.surfs = []
        self.fps = 30
    def finish(self):
        print("saving gifs")
        image_paths = []
        for frame_idx, surf in enumerate(self.surfs):
            image_path = f'{self.path}/bla_%05d.png' % frame_idx
            image_paths.append(image_path)
            pygame.image.save(surf, image_path)

        convertpath = 'convert'
        cmd = [
            convertpath,
            "-delay", f"{1000 // self.fps},1000",
            "-size", f'{self.surfs[0].get_width()}x{self.surfs[0].get_height()}']
        cmd += image_paths
        cmd += [f"{self.path}/anim.gif"]
        print(cmd)
        import subprocess
        subprocess.call(cmd)

        for image_path in image_paths:
            os.remove(image_path)

        self.image_path = []
        self.finished_saving = False

    def update(self, events, screen):
        for e in events:
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_a and not self.start_saving:
                    self.start_saving = True
                    self.finished_saving = False
                    print("recording surfs, press a")
                elif e.key == pg.K_a and self.start_saving:
                    self.start_saving = False
                    self.finished_saving = True
        if self.finished_saving:
            self.finish()
        if self.start_saving:
            self.surfs.append(screen.copy())


# CAMERA_RES = list(map(int, [640//1.3, 480//1.3]))
CAMERA_RES = [480, 360]

class Looper:
    def __init__(self, app):
        self.active = True

        self.screen = app.screen
        self._app = app

        # We loop quickly so timing can be more accurate with the sounds.
        self.fps = 240

        #TODO: FIXME: this camera id should be selectable.
        camera_id = 0
        self.video_thread = VideoThread(camera_id, CAMERA_RES[0], CAMERA_RES[1])
        self.video_thread.daemon = True
        self.video_thread.start()



        track_recorder = TrackRecorder(app.audio_thread)
        self.track_recorder = track_recorder

        recording_lights = [
            RecordingLight(track, idx)
            for idx, track in enumerate(track_recorder.tracks)
        ]
        self.recording_lights = recording_lights

        recording_waves = [
            RecordingWave(track, idx)
            for idx, track in enumerate(track_recorder.tracks)
        ]
        self.recording_waves = recording_waves


        bpm_counter = BpmCounter(track_recorder.bpm)
        self.bpm_counter = bpm_counter

        bpm_light = BpmLight(track_recorder.bpm)
        self.bpm_light = bpm_light

        bpm_line = BpmLine(track_recorder.bpm)
        self.bpm_line = bpm_line


        self.parrot = Parrot()

        pg.display.set_caption('press space 4 times to adjust BPM timing')
        screen = app.screen

        background = pg.Surface(screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))
        self.background = background

        sprite_list = [bpm_counter, bpm_light, bpm_line] + recording_lights + recording_waves + [self.parrot]
        allsprites = pg.sprite.LayeredDirty(
            sprite_list,
            _time_threshold=1000/10.0
        )
        allsprites.clear(screen, background)
        self.allsprites = allsprites


    def redraw(self):
        screen = self.screen
        bpm_counter = self.bpm_counter
        track_recorder = self.track_recorder
        allsprites = self.allsprites
        background = self.background

        rects = []
        rects.append(screen.blit(background, (0, 0)))
        allsprites.clear(screen, background)
        for spr in allsprites:
            spr.dirty = 1
        allsprites.draw(screen)
        pg.display.update(rects)

    def events(self, events):
        rects = []

        screen = self.screen
        bpm_counter = self.bpm_counter
        track_recorder = self.track_recorder
        allsprites = self.allsprites
        video_thread = self.video_thread
        background = self.background

        for e in events:
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key in [pg.K_ESCAPE, pg.K_q]:
                going = False

            if e.type == pg.KEYDOWN and e.key in [pg.K_c]:
                self.redraw()

                # allsprites.clear(screen, background)
                video_thread.stop()
                # video_thread = VideoThread(1, 1920, 1080)
                video_thread = VideoThread(0, CAMERA_RES[0], CAMERA_RES[1])
                video_thread.daemon = True
                video_thread.start()
            if e.type == pg.KEYDOWN and e.key in [pg.K_v]:
                screen.blit(background, (0, 0))
                allsprites.clear(screen, background)
                video_thread.stop()
                # video_thread = VideoThread(1, 1920, 1080)
                video_thread = VideoThread(0, CAMERA_RES[0], CAMERA_RES[1])
                video_thread.daemon = True
                video_thread.start()


        track_recorder.events(events)


        if track_recorder.bpm.started_beat and track_recorder.bpm.first_beat:
            track_recorder.play()

        bpm_counter.events(events)

        self.rects = rects



    def update(self, elapsed_time):
        """ return True to let other scenes update. False to only us update.
        """
        pass

    def render(self):
        """ return rects.

            If scene.propagate_render is True, the render will
                continue to be propagated.
        """
        rects = self.rects
        screen = self.screen
        bpm_counter = self.bpm_counter
        track_recorder = self.track_recorder
        allsprites = self.allsprites
        video_thread = self.video_thread
        bpm_line = self.bpm_line


        # the line changes color depending on when we are recording.
        for track in track_recorder.tracks:
            if track.recording == 1:
                bpm_line.color = bpm_line.preparing_color
                break
            elif track.recording == 2:
                bpm_line.color = bpm_line.recording_color
                break
            else:
                bpm_line.color = bpm_line.not_recording_color


        if video_thread.width != 1920:
            allsprites.update()
            rects.extend(allsprites.draw(screen))


        while not video_thread.queue.empty():
            surface = video_thread.queue.get()
            if surface:
                if video_thread.width == CAMERA_RES[0]:
                    video_x = screen.get_width() - CAMERA_RES[0]
                    video_y = (screen.get_height() - CAMERA_RES[1]) - 25
                else:
                    video_x = 0
                    video_y = 0
                video_rect = screen.blit(surface, (video_x, video_y))
                rects.append(video_rect)
        return rects
