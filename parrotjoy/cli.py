""" Command line interface.
"""
import sys
import os

# pylint: disable=import-outside-toplevel


def cli_main():
    """Entry point for the app"""
    # figure out our directories

    # these directories will be used if parrotjoy cannot find
    # the directories in the location of the main program
    if sys.platform == "win32":
        data_directory = "C:\\Program Files\\parrotjoy"
        code_directory = "C:\\Program Files\\parrotjoy\\code"
    else:
        data_directory = "/usr/share/games/parrotjoy"
        code_directory = "/usr/lib/games/parrotjoy"

    # first try to get the path from the parrotjoy package.
    try:
        import parrotjoy

        if isinstance(parrotjoy, list):
            localpath = os.path.abspath(parrotjoy.__path__[0])
        else:
            localpath = os.path.abspath(parrotjoy.__path__[0])
    except ImportError:
        localpath = os.path.split(os.path.abspath(sys.argv[0]))[0]

    testdata = localpath
    testcode = os.path.join(localpath, ".")

    if os.path.isdir(os.path.join(testdata, "data")):
        data_directory = testdata
    if os.path.isdir(testcode):
        code_directory = testcode

    # pyinstaller uses this variable to store the path
    #   where it extracts data to.
    pyinstaller_path = getattr(sys, "_MEIPASS", None)
    if pyinstaller_path:
        data_directory = os.path.join(pyinstaller_path, "data")
    else:
        # apply our directories and test environment
        os.chdir(data_directory)
        sys.path.insert(0, code_directory)
        check_dependencies(code_directory)

    # run game and protect from exceptions
    try:
        # import pdb;pdb.set_trace()
        try:
            from .main import main
        except ImportError:
            from parrotjoy.main import main

        main(sys.argv)
    except KeyboardInterrupt:
        print("Keyboard Interrupt (Control-C)...")
    except:
        # must wait on any threading
        # if game.thread:
        #     game.threadstop = 1
        #     while game.thread:
        #         pg.time.wait(10)
        #         print('waiting on thread...')

        # we need to enable a debug handler for release.
        exception_handler()
        # if game.DEBUG:
        # raise
        raise


def check_dependencies(code_directory):
    "only returns if everything looks ok"
    msgs = []

    # make sure this looks like the right directory
    if not os.path.isdir(code_directory):
        msgs.append("Cannot locate parrotjoy modules")
    if not os.path.isdir("data"):
        msgs.append("Cannot locate parrotjoy data files")

    # is correct pg found?
    try:
        import pygame as pg

        if pg.ver < "2.1.0":
            msgs.append("Requires pygame 2.1.0 or Greater, You Have " + pg.ver)
    except ImportError:
        msgs.append("Cannot import pygame, install version 2.1.0 or higher")
        pg = None

    # check that we have FONT and IMAGE
    if pg:
        if not pg.font:
            msgs.append("pg requires the SDL_ttf library, not available")
        if not pg.image or not pg.image.get_extended():
            msgs.append("pg requires the SDL_image library, not available")

    if msgs:
        msg = "\n".join(msgs)
        errorbox(msg)


# Pretty Error Handling Code...


def __pgbox(title, message):
    try:
        import pygame as pg

        pg.quit()  # clean out anything running
        pg.display.init()
        pg.font.init()
        screen = pg.display.set_mode((460, 140))
        pg.display.set_caption(title)
        font = pg.font.Font(None, 18)
        foreg, backg, liteg = (0, 0, 0), (180, 180, 180), (210, 210, 210)
        ok = font.render("Ok", 1, foreg, liteg)
        okbox = ok.get_rect().inflate(200, 10)
        okbox.centerx = screen.get_rect().centerx
        okbox.bottom = screen.get_rect().bottom - 10
        screen.fill(backg)
        screen.fill(liteg, okbox)
        screen.blit(ok, okbox.inflate(-200, -10))
        pos = [10, 10]
        for text in message.split("\n"):
            if text:
                msg = font.render(text, 1, foreg, backg)
                screen.blit(msg, pos)
            pos[1] += font.get_height()
        pg.display.flip()
        while 1:
            e = pg.event.wait()
            if (
                e.type == pg.QUIT
                or (
                    e.type == pg.KEYDOWN
                    and e.key in [pg.K_ESCAPE, pg.K_SPACE, pg.K_RETURN, pg.K_KP_ENTER]
                )
                or (e.type == pg.MOUSEBUTTONDOWN and okbox.collidepoint(e.pos))
            ):
                break
        pg.quit()
    except pg.error as exc:
        print(title, message)
        raise ImportError from exc


handlers = [__pgbox]


def __showerrorbox(message):
    title = os.path.splitext(os.path.split(sys.argv[0])[1])[0]
    title = title.capitalize() + " Error"
    for e in handlers:
        try:
            e(title, message)
            break
        except (ImportError, NameError, AttributeError):
            pass


def errorbox(message):
    message = str(message)
    if not message:
        message = "Error"
    __showerrorbox(message)
    sys.stderr.write("ERROR: " + message + "\n")
    raise SystemExit


def exception_handler():
    import traceback

    exec_type, info, trace = sys.exc_info()
    tracetop = traceback.extract_tb(trace)[-1]
    # pylint: disable=consider-using-f-string
    tracetext = "File %s, Line %d" % tracetop[:2]
    if tracetop[2] != "?":
        tracetext += ", Function %s" % tracetop[2]
    exception_message = '%s:\n%s\n\n%s\n"%s"'
    message = exception_message % (str(exec_type), str(info), tracetext, tracetop[3])
    if exec_type not in (KeyboardInterrupt, SystemExit):
        __showerrorbox(message)


if __name__ == "__main__":
    cli_main()
