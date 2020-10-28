"""For grabbing camera data in a thread and putting pygame Surfaces on a queue.

https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture

TODO:

- A window per camera for the demo might be good.
- Add a --what cmdline argument (or a better name) for selecting a camera by index.
"""
import sys
from threading import Thread
from queue import Queue

import pygame as pg
import pygame.camera

pg.camera = pygame.camera  # hack for pylance thinking pygame.camera is unused.

# If we can use cv2 use that by default.
USE_CV2 = False

try:
    import cv2  # pylint ignore: wrong-import-position

    USE_CV2 = True
except ImportError:
    pass

# cv2 has troubles with pylint
# pylint: disable=no-member


class VideoThreadCV2(Thread):
    """Camera Surfaces into queue."""

    def __init__(
        self,
        what: int | str = 1,
        width: int = 640,
        height: int = 480,
    ):
        """Camera Surfaces into a queue.

        :param int | str what: What to open. Either an index or a string path.
        :param int width: Width in pixels of Surface to put in the Queue.
        :param int height: Height in pixels of Surface to put in the Queue.
        """
        Thread.__init__(self)
        self.size = (width, height)

        self.going = True
        self.queue: Queue[pg.Surface | bool] = Queue()
        self.camera = cv2.VideoCapture(what)
        if not self.camera.isOpened():
            self.going = False
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def stop(self):
        """Stop going."""
        self.going = False

    def run(self):
        """While going put video frames on the queue."""
        while self.going:
            try:
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                    frame = cv2.flip(frame, 1)
                    surface = pg.surfarray.make_surface(frame)
                    self.queue.put(surface)
                else:
                    self.queue.put(False)
            except KeyboardInterrupt:
                break
        self.camera = None


class VideoThreadPygame(Thread):
    """Camera Surface into queue."""

    def __init__(self, what=0, width=640, height=480):
        """Camera Surfaces into a queue.

        :param int | str what: What to open. Either an index or a string path.
        :param int width: Width in pixels of Surface to put in the Queue.
        :param int height: Height in pixels of Surface to put in the Queue.
        """
        Thread.__init__(self)
        self.size = (width, height)

        self.going = True
        self.queue = Queue()

        if not pg.camera.init():
            self.going = False
            return

        cams = pg.camera.list_cameras()
        if cams:
            self.camera = pg.camera.Camera(cams[what], self.size, "RGB")
            self.going = True
        else:
            self.camera = None
            self.going = False

        if self.camera is not None:
            self.camera.start()

        self.snapshot = pg.Surface(self.size, 0, pg.display.get_surface())

    def stop(self):
        """Stop going."""
        self.going = False

    def run(self):
        """While going put video frames on the queue."""
        while self.going:
            try:
                # self.snapshot = self.camera.get_image(self.snapshot)
                surface = self.camera.get_image()
                if surface is not None:
                    self.queue.put(surface)
            except KeyboardInterrupt:
                break
        self.camera = None


VideoThread = VideoThreadCV2 if USE_CV2 else VideoThreadPygame


def main():
    """So we can demo this module out."""

    import argparse  # pylint: disable=import-outside-toplevel

    def init_argparse() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            usage="%(prog)s [OPTION]",
            description="View a camera. Optionally choose --pygame or --cv2",
        )
        parser.add_argument(
            "--pygame",
            dest="pygame",
            action="store_const",
            const=True,
            default=not USE_CV2,
            help="use pygame camera",
        )
        parser.add_argument(
            "--cv2",
            dest="cv2",
            action="store_const",
            const=True,
            default=USE_CV2,
            help="use cv2 camera",
        )

        return parser

    parser = init_argparse()
    args = parser.parse_args()

    pg.init()
    screen = pg.display.set_mode([640, 480])
    # video_thread = VideoThread('some_movie.mp4')
    if args.pygame:
        print("using pygame camera")
        video_thread = VideoThreadPygame(0, 640, 480)
    else:
        print("using cv2 camera")
        video_thread = VideoThreadCV2(1, 640, 480)

    video_thread.daemon = True
    video_thread.start()
    try:
        while True:

            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    sys.exit(0)

            while not video_thread.queue.empty():
                surface = video_thread.queue.get()
                if surface:
                    screen.blit(surface, (0, 0))
            pg.display.flip()

    except (KeyboardInterrupt, SystemExit):
        pg.quit()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
