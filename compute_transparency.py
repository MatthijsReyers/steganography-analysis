import wave, struct, os, math
import numpy as np
import pandas as pd
from tqdm import tqdm

def load_samples(path: str) -> any:
    with wave.open(path, 'rb') as audio:
        frames = audio.getnframes()
        frame_bytes = audio.readframes(frames)
        samples = [ struct.unpack("<h", frame_bytes[(i):(2+i)]) for i in range(0, frames, 2) ] 
        return np.array(samples)


def compute_mse(original: np.ndarray, changed: np.ndarray):
    assert len(original) == len(changed)
    n = len(original)
    data = (original - changed) ** 2
    return (sum(data) / n)[0]


def compute_snr(original: np.ndarray, mse: int):
    n = len(original)
    data = original ** 2
    signal = (sum(data)[0] / n)
    return 10 * math.log10(signal / mse)


def compute_method_transparency(base_url, method_name, original_url:str='data/original/'):
    data = list()

    for file in tqdm(os.listdir('data/original'), f'[*] Computing perceptual transparency for {method_name}'):
        original_samples = load_samples(original_url+file)
        stego_samples = load_samples(base_url+'/'+file)

        genre = file.split('.')[0]

        mse = compute_mse(original_samples, stego_samples)
        snr = compute_snr(original_samples, mse)

        data.append([file, genre, mse, snr])
    
    df = pd.DataFrame(data, columns=['File', 'Genre', 'MSE', 'SNR'])
    return df


def compute_transparency():
    # df = compute_method_transparency('data/steghide', 'steghide')
    # df.to_csv('results/perceptual_transparency_steghide.csv')
    
    df = compute_method_transparency('data/gan1', 'gan1', original_url='data/shortened/')
    df.to_csv('results/perceptual_transparency_steghide.csv')

    # df = compute_method_transparency('data/hide4pgp', 'hide4pgp')
    # df.to_csv('results/perceptual_transparency_hide4pgp.csv')


if __name__ == '__main__':
    compute_transparency()
