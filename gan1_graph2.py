import matplotlib.pyplot as plt
import numpy as np
import wave, librosa
from gan1.utils import load_wav
from gan1.spectrogram import wav_to_spectro

file_good = 'spoken.SX369.wav'
file_bad = 'spoken.SI2033.wav'

good_wav, _, _ = load_wav('data/shortened/'+file_good)
bad_wav, _, _ = load_wav('data/gan1/'+file_bad)

good_spec, _ = wav_to_spectro(good_wav)
bad_spec, _ = wav_to_spectro(bad_wav)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))

def plot_spec(spec, ax):
    spec = spec.numpy()
    spec = spec[0] + 1j*spec[1]
    img = librosa.display.specshow(
        spec, 
        x_axis='time', 
        fmin=0,
        fmax=3000, 
        y_axis='mel', 
        sr=6000, 
        ax=ax
    )

plot_spec(good_spec, ax1)
plot_spec(bad_spec, ax2)

plt.title("Signal Wave...")
plt.show()


# # Load the wav file.
# path = 'data/original/'+file
# out_path = 'data/gan1/'+file
# wav, bitrate, bits = load_wav(path)

# # Convert wav to spectrogram.
# cover, hop_length = spectrogram.wav_to_spectro(wav)
# plot_spec(cover); continue