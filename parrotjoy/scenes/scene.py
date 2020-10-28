class Scene:
    def __init__(self, app):
        self.active = True

        self.screen = app.screen
        self._app = app

    def events(self, events):
        """Events for us to process.
        """

    def update(self, elapsed_time: float):
        """ return True to let other scenes update. False to only us update.
        """

    def render(self):
        """ return rects.

            If scene.propagate_render is True, the render will
                continue to be propagated.
        """
