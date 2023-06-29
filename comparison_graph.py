import matplotlib.pyplot as plt
import numpy as np
import wave

file = 'disco.00071.wav'
file = 'spoken.SX369.wav'

def get_signal(file):
    with wave.open(file, 'r') as wav:
        signal = wav.readframes(-1)
        signal = np.fromstring(signal, np.int16)
    return signal

methods = ['Hide4pgp', ]

signal = get_signal('data/original/'+file)


fig = plt.subplots(3, 4, figsize=(12, 8, ))
plt.title("Signal Wave...")
plt.plot(signal)
plt.show()

