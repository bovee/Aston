import numpy as np
import scipy.io.wavfile
import scipy.signal


def as_sound(df, speed=60, cutoff=50):

    # make a 1d array for the sound
    to_t = lambda t: (t - df.index[0]) / speed
    wav_len = int(to_t(df.index[-1]) * 60 * 44100)
    wav = np.zeros(wav_len)

    # create an artificial array to interpolate times out of
    tmask = np.linspace(0, 1, df.shape[0])

    # come up with a mapping from mz to tone
    min_hz, max_hz = 50, 1000
    min_mz, max_mz = min(df.columns), max(df.columns)

    def mz_to_wv(mz):
        """
        Maps a wavelength/mz to a tone.
        """
        try:
            mz = float(mz)
        except:
            return 100
        wv = (mz * (max_hz - min_hz) - max_hz * min_mz + min_hz * max_mz) \
                / (max_mz - min_mz)
        return int(44100 / wv)

    # go through each trace and map it into the sound array
    for i, mz in enumerate(df.columns):
        if float(mz) < cutoff:
            # clip out mz/wv below a certain threshold
            # handy if data has low level noise
            continue
        print(str(i) + '/' + str(df.shape[1]))
        inter_x = np.linspace(0, 1, wav[::mz_to_wv(mz)].shape[0])
        wav[::mz_to_wv(mz)] += np.interp(inter_x, tmask, df.values[:, i])

    # scale the new array and write it out
    scaled = wav / np.max(np.abs(wav))
    scaled = scipy.signal.fftconvolve(scaled, np.ones(5) / 5, mode='same')
    scaled = np.int16(scaled * 32767)
    scipy.io.wavfile.write('test.wav', 44100, scaled)
