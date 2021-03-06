"""

https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture
"""
import pygame
import pygame.camera
from pygame.locals import *
import numpy as np
import sys
from threading import Thread
from queue import Queue

USE_CV2 = False

try:
    import cv2
    USE_CV2 = True
except:
    pass


class VideoThreadCV2(Thread):
    """ Camera Surface into queue.
    """
    def __init__(self, what=1, width=640, height=480):
        Thread.__init__(self)
        self.width = width
        self.height = height

        self.going = True
        self.queue = Queue()
        self.camera = cv2.VideoCapture(what)
        if not self.camera.isOpened():
            self.going = False
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def stop(self):
        self.going = False

    def run(self):
        while self.going:
            try:
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    frame = cv2.flip(frame, 1)
                    surface = pygame.surfarray.make_surface(frame)
                    self.queue.put(surface)
                else:
                    self.queue.put(False)
            except KeyboardInterrupt:
                break
        self.camera = None


class VideoThreadPygame(Thread):
    """ Camera Surface into queue.
    """
    def __init__(self, what=1, width=640, height=480):
        Thread.__init__(self)
        self.width = width
        self.height = height
        self.size = (width, height)

        self.going = True
        self.queue = Queue()

        try:
            pygame.camera.init()
        except:
            self.going = False
            return

        clist = pygame.camera.list_cameras()
        if clist:
            self.camera = pygame.camera.Camera(clist[0], self.size, "RGB")
            self.going = True
        else:
            self.camera = None
            self.going = False

        if self.camera is not None:
            self.camera.start()

        self.snapshot = pygame.surface.Surface(self.size, 0, pygame.display.get_surface())


    def stop(self):
        self.going = False

    def run(self):
        while self.going:
            try:
                # self.snapshot = self.camera.get_image(self.snapshot)
                snapshot = self.camera.get_image()
                if snapshot is not None:
                    self.queue.put(surface)
            except KeyboardInterrupt:
                break
        self.camera = None

if USE_CV2:
    VideoThread = VideoThreadCV2
else:
    VideoThread = VideoThreadPygame




def main():
    pygame.init()
    screen = pygame.display.set_mode([640, 480])
    # video_thread = VideoThread('some_movie.mp4')
    video_thread = VideoThread(1, 640, 480)
    video_thread.daemon = True
    video_thread.start()
    clock = pygame.time.Clock()
    try:
        while True:

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    sys.exit(0)

            while not video_thread.queue.empty():
                surface = video_thread.queue.get()
                if surface:
                    screen.blit(surface, (0,0))
            pygame.display.flip()
            # clock.tick(30)



    except (KeyboardInterrupt, SystemExit):
        pygame.quit()

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
