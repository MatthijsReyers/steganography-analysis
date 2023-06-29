import os, utils, wave, math
import numpy as np
import pandas as pd
from tqdm import tqdm
import torch

from gan1 import gan, spectrogram, payload
from gan1.utils import load_wav, plot_spec

MAX_SIZE = 256

DF_COLUMNS = ['File', 'Message size (bytes)', 'mse', 'snr' ]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def compute_mse(original: np.ndarray, changed: np.ndarray):
    assert len(original) == len(changed)
    n = len(original)
    data = (original - changed) ** 2
    return (sum(data) / n)


def compute_snr(original: np.ndarray, mse: int):
    n = len(original)
    data = original ** 2
    signal = (sum(data) / n)
    return 10 * math.log10(signal / mse)


def compute_gan():
    with open(utils.SECRET_FILE) as secret_file:
        secret_data = secret_file.read()

    files = os.listdir('data/shortened')

    df = pd.DataFrame([], columns=DF_COLUMNS)

    for file in files:
        if '.wav' in file:
            print(f'Working on {file}')
            data = []

            path = 'data/shortened/'+file
            wav, bitrate, bits = load_wav(path)

            # Convert wav to spectrogram.
            cover_spec, hop_length = spectrogram.wav_to_spectro(wav)
            _, H, W = cover_spec.size()
            cover_spec = cover_spec[None].to(device)

            # Ssshh... Don't worry about it..
            cover_audio = (wav[0] * 32767).numpy().round().astype('int16').astype('uint16')

            sizes = list(range(1, 64))
            failures = 0
            MAX_FAILURES = 5

            for msg_size in tqdm(sizes):
                if failures > MAX_FAILURES:
                    break

                # Prepare secret for embedding.
                msg = secret_data[:msg_size]
                secret = payload.make_payload(W, H, msg)
                secret = secret.to(device)

                # Try to embed secret.
                stego_spec = gan.embed_message(cover_spec, secret)
                stego_spec = stego_spec.detach()
                stego_audio = spectrogram.spectro_to_wav(stego_spec[0], hop_length)

                try:
                    text_out, count = gan.decode_message(stego_spec)
                except Exception as e:
                    print(e)
                    text_out = ''

                if text_out[:msg_size] != msg:
                    print('Failed at', msg_size, 'bytes', msg, text_out)
                    failures += 1

                # Ssshh... Don't worry about it..
                stego_audio = (stego_audio * 32767).round().astype('int16').astype('uint16')

                mse = compute_mse(cover_audio, stego_audio)
                snr = compute_snr(cover_audio, mse)

                data.append([file, msg_size, mse, snr])

            df2 = pd.DataFrame(data, columns=DF_COLUMNS)
            df = pd.concat([df, df2])
            df.to_csv('results/gan_ptp.csv')





if __name__ == '__main__':
    compute_gan()
