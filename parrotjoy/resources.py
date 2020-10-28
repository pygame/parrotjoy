"""Basically doing sound effects, graphics and music-ing.

Does paths, loading, caching, converting and such... for us.

gfx('parrot.png', convert=True) will look into the data/images/ folder, load the image,
and maybe even convert the image for you.

Next place you use gfx('parrot.png', convert=True) will give you the same cached image.

This means when using gfx, you just use it.
Don't not worry about paths, caching, converting and such things.
"""
import os
from typing import Dict, Tuple
import pygame as pg

# Our secret stashes.
_SFX_CACHE : Dict[str, pg.mixer.Sound] = {}
_GFX_CACHE : Dict[Tuple[str, bool, bool], pg.Surface] = {}


def data_path() -> str:
    """Returns file system path for where the data at."""
    if os.path.exists("data"):
        path = "data"
    else:
        path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data",
        )
    return path


def music(
    name: str | None = None,
    load: bool = True,
    play: bool = True,
    stop: bool | None = False,
) -> None:
    """Basically music-ing. music('song.mp3')

    :param name: the music file to play. Relative to data/sounds.
    :param load: Start loading the music. If music is loaded already it's faster to play.
    :param play: Play music.
    :param stop: Stop music.

    #### Example

    ```python
    music('bla.ogg')
    music(stop=True)
    ```
    """
    if load and name is None:
        raise ValueError("load=True requires using a name")
    if (play and load) or (play and stop):
        raise ValueError("load=True requires using a name")

    # perhaps the mixer is not included or initialised.
    if pg.mixer and pg.mixer.get_init():
        if load and not stop and name is not None:
            pg.mixer.music.load(music_path(name))
        if play and stop is None or stop is False:
            pg.mixer.music.play()
        elif stop:
            pg.mixer.music.stop()


def music_path(name: str) -> str:
    """Returns file system path for where the given music is at."""
    path = os.path.join(data_path(), "sounds", name)
    return path


def gfx(name: str, convert: bool = False, convert_alpha: bool = False) -> pg.Surface:
    """Basically graphics using. Loading/converting/cached. gfx('parrot.png')

    :param name: looks in data/images/ for the name to load.
    :param convert: convert to the most meow
    :param convert_alpha: convert_alpha()
    :param play: Play music.
    :param stop: Stop music.

    #### Example

    ```python
    gfx('parrot.png')
    gfx('parrot.png', convert=True)
    gfx('parrot.png', convert_alpha=True)
    ```
    """
    gfx_key = (name, convert, convert_alpha)
    if gfx_key in _GFX_CACHE:
        return _GFX_CACHE[gfx_key]

    path = os.path.join(data_path(), "images", name)
    surf = pg.image.load(path)
    if convert:
        surf = surf.convert()
    if convert_alpha:
        surf = surf.convert_alpha()

    _GFX_CACHE[gfx_key] = surf
    return surf


def sfx(snd: str, play: bool = False, stop: bool = False) -> pg.mixer.Sound:
    """Basically sound using. Loading/converting/cached. sfx('parrot.mp3')

    :param snd: looks in data/sounds/ for the sound to load.
    :param play: Play sound.
    :param stop: Stop sound.

    #### Example

    ```python
    sfx('parrot.mp3')
    sfx('parrot.png', play=True)
    sfx('parrot.png', convert_alpha=True)
    ```
    """
    snd_key = snd
    if snd_key in _SFX_CACHE:
        sound = _SFX_CACHE[snd_key]
    else:
        path = os.path.join(data_path(), "sounds", snd)
        sound = pg.mixer.Sound(path)
        _SFX_CACHE[snd_key] = sound

    # print(snd_key, play, stop, time.time())
    if play:
        sound.play()
    if stop:
        sound.stop()
    return sound
