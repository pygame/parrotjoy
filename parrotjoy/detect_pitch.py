"""

https://www.youtube.com/watch?v=W585xR3bjLM

YIN pitch detection algorithm
De Cheveigné, A., & Kawahara, H. (2002). YIN, a fundamental frequency estimator for speech and music. The Journal of the Acoustical Society of America, 111(4), 1917-1930.

"""


import numpy as np

from scipy import signal
from scipy.io import wavfile

# a 1HZ signal
# def f(x):
#     f_0 = 1
#     return np.sin(x * np.pi * 2 * f_0)

# a harder signal
def f(x):
    f_0 = 1
    envelope = lambda x: np.exp(-x)
    return np.sin(x * np.pi * 2 * f_0) * envelope(x)

# auto correlation function
# signal, Window size, time step, 
# lag number of samples to shift the curry by
def ACF(f, W, t, lag):
    return np.sum(
        f[t : t + W] * 
        f[lag + t : lag + t + W]
    )


# difference function
def DF(f, W, t, lag):
    return (ACF(f, W, t, 0) 
    + ACF(f, W, t + lag, 0) 
    - (2 * ACF(f, W, t, lag))
    )

# cummlative mean normalized difference function
def CMNDF(f, W, t, lag):
    if lag == 0:
        return 1
    return DF(f, W, t, lag) / np.sum([DF(f, W, t, j + 1) for j in range(lag)]) * lag


# def detect_pitch(f, W, t, sample_rate, bounds):
#     DF_vals = [DF(f, W, t, i) for i in range(*bounds)]
#     sample = np.argmin(DF_vals) + bounds[0]
#     return sample_rate / sample

# def detect_pitch(f, W, t, sample_rate, bounds):
#     CMNDF_vals = [CMNDF(f, W, t, i) for i in range(*bounds)]
#     sample = np.argmin(CMNDF_vals) + bounds[0]
#     return sample_rate / sample

def detect_pitch(f, W, t, sample_rate, bounds, thresh=0.1):
    CMNDF_vals = [CMNDF(f, W, t, i) for i in range(*bounds)]
    sample = None
    for i, val in enumerate(CMNDF_vals):
        if val < thresh:
            sample = i + bounds[0]
            break

    if sample is None:
        sample = np.argmin(CMNDF_vals) + bounds[0]
    return sample_rate / sample


# def main():
#     sample_rate = 500
#     start = 0
#     end = 5
#     num_samples = int(sample_rate * (end - start) + 1)
#     window_size = 200
#     bounds = [20, num_samples // 2]

#     x = np.linspace(start, end, num_samples)
#     print(detect_pitch(f(x), window_size, 1, sample_rate, bounds))

def main():
    sample_rate, data = wavfile.read("singer.wav")
    data = data.astype(np.float64)
    window_size = int(5 / 2000 * 44100)
    bounds = [20, 2000]

    pitches = []

    for i in range(data.shape[0] // (window_size + 3)):
        pitches.append(
            detect_pitch(
                data,
                window_size,
                i * window_size,
                sample_rate,
                bounds
            )
        )
    print(pitches)



if __name__ == "__main__":
    main()


# improvements:
#   more accurate
#   padding signal to avoid crashes
#   memoization to improve time it takes to run
