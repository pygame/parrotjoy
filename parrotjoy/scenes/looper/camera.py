from ...camera_cv import VideoThread

# CAMERA_RES = list(map(int, [640//1.3, 480//1.3]))
CAMERA_RES = [480, 360]


class Camera:
    """Just a camera that can draw."""
    def __init__(self):
        self.video_thread = None
        self.start()

    def start(self):
        """Open up a new camera."""
        if getattr(self, "video_thread", None):
            self.video_thread.stop()
        # TODO: FIXME: this camera id should be selectable.
        camera_id = 0

        self.video_thread = VideoThread(camera_id, CAMERA_RES[0], CAMERA_RES[1])
        self.video_thread.daemon = True
        self.video_thread.start()

    def draw(self, screen):
        """Draw onto the screen, and return the rectangles."""
        rects = []
        while not self.video_thread.queue.empty():
            surface = self.video_thread.queue.get()
            if surface:
                if self.video_thread.size[0] == CAMERA_RES[0]:
                    video_x = screen.get_width() - CAMERA_RES[0]
                    video_y = (screen.get_height() - CAMERA_RES[1]) - 25
                else:
                    video_x = 0
                    video_y = 0
                video_rect = screen.blit(surface, (video_x, video_y))
                rects.append(video_rect)

        return rects
