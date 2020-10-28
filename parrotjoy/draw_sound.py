"""For drawing sounds as a waveform.
"""
from typing import Sequence

from array import array
import pygame as pg

Samples = Sequence[float] | Sequence[int] | array
Color = pg.Color | str | tuple


def scale_samples_to_surf(width: int, height: int, samples: Samples):
    """Returns a generator containing (x, y) to draw a waveform.

    :param width: width of surface to scale points to.
    :param height: height of surface to scale points to.
    :param samples: an array of signed 1 byte or signed 2 byte.
    """
    # assert samples.typecode in ['h', 'b']
    # precalculate a bunch of variables, so not done in the loop.
    len_samples = len(samples)
    width_per_sample = width / len_samples
    height_1 = height - 1

    if isinstance(samples, array):
        if samples.typecode == "h":
            # for array typecode 'h', -32768 to 32768
            factor = 1.0 / 65532
            normalize_modifier = int(65532 / 2)
        elif samples.typecode == "b":
            # for array typecode 'b', -127 to 127
            factor = 1.0 / 256
            normalize_modifier = int(256 / 2)
    else:
        mult = 16
        factor = 1.0 / (65532 / mult)
        normalize_modifier = int(65532 / (2 * mult))

    return (
        (
            int((sample_number + 1) * width_per_sample),
            int(
                (1.0 - (factor * (samples[sample_number] + normalize_modifier)))
                * (height_1)
            ),
        )
        for sample_number in range(len_samples)
    )


def chunks(alist, chunk_size):
    """chunk_size chunks from alist.

    Breaks the input up into parts of length `chunk_size`.
    """
    for i in range(0, len(alist), chunk_size):
        yield alist[i : i + chunk_size]


def average_chunks(parts):
    """Get average value for each chunk"""
    for chunk in parts:
        yield sum(chunk) / len(chunk)


def resize_samples(samples: Samples, width: int):
    """Returns averaged `samples` with the number of chunks `width`."""
    if len(samples) < width:
        return samples
    per_pixel = len(samples) / width
    chunk_size = int(round(per_pixel))
    return average_chunks(chunks(samples, chunk_size))


def draw_wave(
    surf: pg.Surface,
    samples: Samples,
    wave_color: Color = pg.Color("black"),
    background_color: Color | None = pg.Color("white"),
):
    """Draw array of sound samples as waveform into the 'surf'.

    :param surf: Surface we want to draw the wave form onto.
    :param samples: an array of signed 1 byte or signed 2 byte.
    :param wave_color: color to draw the wave form.
    :param background_color: to fill the 'surf' with.

    ```python
        waveform_surf = pg.Surface((320, 200)).convert()
        draw_wave(
            waveform_surf,
            sound.samples,
            background_color=(0,0,0),
            wave_color=(255, 255, 255))
    ```
    """
    if background_color is not None:
        surf.fill(background_color)
    width, height = surf.get_size()
    if len(samples) == 0:
        return

    newsamples = resize_samples(samples, width)
    if isinstance(samples, array):
        assert samples.typecode in ["h", "b"]
        samples = array(samples.typecode, newsamples)
    else:
        samples = list(newsamples)

    points = tuple(scale_samples_to_surf(width, height, samples))
    if points:
        pg.draw.lines(surf, wave_color, False, points)
