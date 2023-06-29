from utils import makeDirectory, SECRET_FILE
from tqdm import tqdm
import os, gan1, torch
from gan1 import gan, spectrogram, payload
from gan1.utils import load_wav, plot_spec
import scipy.io.wavfile as wavfile
import pandas as pd
import wave
import numpy as np

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def save_spectrogram(spec, bitrate, hop_length, out_file):
    spec = spec[0].detach()
    wav = spectrogram.spectro_to_wav(spec, hop_length)
    convert_spec(out_file, bitrate, wav)

def compute_short_version(in_file, out_file) -> int:
    wav, bitrate, bits = load_wav(in_file)
    cover, hop_length = spectrogram.wav_to_spectro(wav)
    wav2 = spectrogram.spectro_to_wav(cover, hop_length)
    convert_spec(out_file, bitrate, wav2)

def convert_spec(outfile, bitrate, wav):
    wav /= 1.414
    wav *= 32767
    wavfile.write(outfile, bitrate, wav.astype(np.int16))

def compute_gan1():
    makeDirectory('data/gan1')
    makeDirectory('data/gan1/sherlock')

    SECRET_FILE = 'secret.sherlock.txt'
    with open(SECRET_FILE, 'r') as file:
        secrets = file.read()

    data = list()
    counter = 0

    rows = os.listdir('data/original')
    for file in tqdm(rows, '[*] Generating stego files'):
        if '.wav' in file:

            # Load the wav file.
            path = 'data/original/'+file
            out_path = 'data/gan1/sherlock/'+file
            wav, bitrate, bits = load_wav(path)
            
            # Convert wav to spectrogram.
            cover, hop_length = spectrogram.wav_to_spectro(wav)
            _, H, W = cover.size()
            cover = cover[None].to(device)

            hiding_capacity = 0
            message_count = 0


            # Try different payload sizes until the maximum one has been determined.
            for payload_size in range(1, 100):
                
                # Prepare secret for embedding.
                secret = secrets[:payload_size]
                secret = payload.make_payload(W, H, secret)
                secret = secret.to(device)

                # Try to embed secret.
                generated = gan.embed_message(cover, secret)

                try:
                    text_out, count = gan.decode_message(generated)
                    if text_out[:payload_size] != secrets[:payload_size]:
                        raise Exception('Incorrect result!')

                    hiding_capacity = payload_size * 8
                    message_count = count
                    save_spectrogram(generated, bitrate, hop_length, out_path)

                except:
                    break
            
            # We do want an output file, even if we failed to embed even a single character.
            if payload_size == 1:
                save_spectrogram(generated, bitrate, hop_length, out_path)

            data.append([
                file, hiding_capacity, message_count, bits
            ])

    return data
    

if __name__ == '__main__':
    data = compute_gan1()

    makeDirectory('data/shortened')
    
    df = pd.DataFrame(data=data, columns=[
        'File',
        'Hiding capacity (bits)',
        'Message count',
        'File size (bits)',
    ])

    # df = pd.read_csv('results/gan1.csv', index_col=0)

    for i, row in df.iterrows():
        compute_short_version('data/original/'+row['File'], 'data/shortened/'+row['File'])

    df['Hiding capacity (%)'] = (df['Hiding capacity (bits)'] / df['File size (bits)']) * 100

    df.to_csv('results/gan1_sherlock.csv')
