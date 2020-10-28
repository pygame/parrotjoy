import os
import subprocess

import pygame as pg


class GifSaver:
    def __init__(self):
        self.path = "/tmp/"
        self.start_saving = False
        self.finished_saving = False
        self.surfs = []
        self.fps = 30

    def finish(self):
        print("saving gifs")
        image_paths = []
        for frame_idx, surf in enumerate(self.surfs):
            image_path = f"{self.path}/bla_%05d.png" % frame_idx
            image_paths.append(image_path)
            pg.image.save(surf, image_path)

        convertpath = "convert"
        cmd = [
            convertpath,
            "-delay",
            f"{1000 // self.fps},1000",
            "-size",
            f"{self.surfs[0].get_width()}x{self.surfs[0].get_height()}",
        ]
        cmd += image_paths
        cmd += [f"{self.path}/anim.gif"]
        print(cmd)

        subprocess.call(cmd)

        for image_path in image_paths:
            os.remove(image_path)

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
