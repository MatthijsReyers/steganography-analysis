from pydub import AudioSegment
import pandas as pd
from utils import NOISE_TYPES, makeDirectory
import os
from tqdm import tqdm
import shutil

ESC_ROOT = './ESC-50/audio/'
noise_meta = pd.read_csv('./ESC-50/meta/esc50.csv')


def cut_noise(noise: AudioSegment, length: int):
    """ Cuts or extends noise signal to make it the provided length. """
    while len(noise) < length:
        noise += noise
    return noise[:length]


def generate_noise_wav(noise_file, base_file, out_file, noise_strength):
    base = AudioSegment.from_wav(base_file)
    noise = AudioSegment.from_wav(noise_file)
    noise = cut_noise(noise, len(base))
    noise -= noise_strength
    edited = base.overlay(noise, position=0)
    edited.export(
        out_file+'_'+str(noise_strength)+'db.wav', 
        format='wav',
        bitrate="352"
    )


def generate_wavs_for_sample(noise_file, noise_type, method, sample):
    tmp = sample.replace('.wav', '')
    levels = [ 2**i for i in range(0, 16) ]
    for noise_level in levels:
        generate_noise_wav(
            ESC_ROOT+noise_file,
            f'./data/{method}/{sample}',
            f'./data/{method}/robustness/{noise_type}/{tmp}',
            noise_level
        )


def generate_wavs_for_noise(noise_type, method):
    # Figure out which noise file to use:
    grouped = noise_meta.loc[noise_meta['category'] == noise_type]
    wind_rows = list(grouped.iterrows())
    noise_file = wind_rows[0][1]['filename']
    
    makeDirectory(f'./data/{method}/robustness/{noise_type}')

    # Loop over all samples.
    for sample in tqdm(os.listdir(f'./data/{method}'), f'Generating robustness data for {method} - {noise_type}'):
        if '.wav' in sample:
            generate_wavs_for_sample(noise_file, noise_type, method, sample)


def generate_wavs_for_method(method: str):
    folder = f'./data/{method}/robustness/'
    try: shutil.rmtree(folder)
    except: pass
    makeDirectory(folder)
    for noise_type in NOISE_TYPES:
        generate_wavs_for_noise(noise_type, method)


def generate_robustness_data():
    # generate_wavs_for_method('steghide')
    # generate_wavs_for_method('hide4pgp')
    # generate_wavs_for_method('gan1')
    generate_wavs_for_method('tan')


if __name__ == '__main__':
    generate_robustness_data()

