""" Some examples for generating and converting sounds for pygame.

Python 2.7, 3.6

Shows:
    - a simple 'square wave' generated
    - resampling sample rates (eg, 8363 to 44100)
    - using built in python array for making pygame.Sound samples.
    - samples at different bit sizes
    - converting from signed 8 to signed 16bit
    - how initializing the mixer changes what samples Sound needs.
    - Using the python stdlib audioop.ratecv for sample rate conversion.
    - drawing sound sample arrays as a waveform scaled into a Surface.

Square Wave
  https://en.wikipedia.org/wiki/Square_wave
MOD (file format)
  https://en.wikipedia.org/wiki/MOD_(file_format)

pygame.mixer.get_init
    https://www.pygame.org/docs/ref/mixer.html#pygame.mixer.get_init
pygame.Sound
    https://www.pygame.org/docs/ref/mixer.html#pygame.mixer.Sound

array (python stdlib)
    https://docs.python.org/3/library/array.html
wave (python stdlib)
    https://docs.python.org/3/library/wave.html
audioop.ratecv (python stdlib)
    https://docs.python.org/3/library/audioop.html?highlight=audio#audioop.ratecv

"""

from array import array
import pygame as pg

def scale_samples_to_surf(width, height, samples):
    """ Returns a generator containing (x, y) to draw a waveform.

    :param width: width of surface to scale points to.
    :param height: height of surface to scale points to.
    :param samples: an array of signed 1 byte or signed 2 byte.
    """
    # assert samples.typecode in ['h', 'b']
    # precalculate a bunch of variables, so not done in the loop.
    len_samples = len(samples)
    width_per_sample = width / len_samples
    height_1 = height - 1

    if hasattr(samples, 'typecode'):
        if samples.typecode == 'h':
            # for array typecode 'h', -32768 to 32768
            factor = 1.0 / 65532
            normalize_modifier = int(65532 / 2)
        elif samples.typecode == 'b':
            # for array typecode 'b', -127 to 127
            factor = 1.0 / 256
            normalize_modifier = int(256 / 2)
    else:
        import numpy as np
        mult = 16
        # breakpoint()
#        if samples.dtype == np.uint8
        factor = 1.0 / (65532/mult)
        normalize_modifier = int(65532 / (2 * mult))

    return ((
        int((sample_number + 1) * width_per_sample),
        int(
            (1.0 -
                (factor *
                    (samples[sample_number] + normalize_modifier)))
            * (height_1)
        ))
    for sample_number in range(len_samples))


def chunks(alist, chunk_size):
    """chunk_size chunks from alist."""
    for i in range(0, len(alist), chunk_size):
        yield alist[i:i + chunk_size]

def average_chunks(parts):
    """get the average value for each chunk"""
    for chunk in parts:
        yield sum(chunk) / len(chunk)

def resize_samples(samples, width):
    if len(samples) < width:
        return samples
    per_pixel = len(samples) / width
    chunk_size = int(round(per_pixel))
    return average_chunks(chunks(samples, chunk_size))


def draw_wave(surf,
              samples,
              wave_color = (0, 0, 0),
              background_color = pg.Color('white')):
    """Draw array of sound samples as waveform into the 'surf'.

    :param surf: Surface we want to draw the wave form onto.
    :param samples: an array of signed 1 byte or signed 2 byte.
    :param wave_color: color to draw the wave form.
    :param background_color: to fill the 'surf' with.

    waveform_surf = pg.Surface((320, 200)).convert()
    draw_wave(
        waveform_surf,
        sound.samples,
        background_color=(0,0,0),
        wave_color=(255, 255, 255))
    """
    if background_color is not None:
        surf.fill(background_color)
    width, height = surf.get_size()
    if samples.shape[0] == 0:
        return
    if 1:
        newsamples = resize_samples(samples, width)
        if hasattr(samples, 'typecode'):
            assert samples.typecode in ['h', 'b']
            samples = array(samples.typecode, newsamples)
        else:
            samples = list(newsamples)

    points = tuple(scale_samples_to_surf(width, height, samples))
    if points:
        pg.draw.lines(surf, wave_color, False, points)



