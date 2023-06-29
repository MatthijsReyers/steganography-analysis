from tanMap.tanmap import embed_tan_map, extract_tan_map
import os, utils, wave, math
import numpy as np
import pandas as pd
from tqdm import tqdm
# from compute_transparency import compute_mse, compute_snr

MAX_SIZE = 256

DF_COLUMNS = ['File', 'Message size (bytes)', 'mse', 'snr' ]

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


def compute_tanmap():
    with open(utils.SECRET_FILE) as secret_file:
        secret_data = secret_file.read()

    files = os.listdir('data/original')

    df = pd.DataFrame([], columns=DF_COLUMNS)

    for file in files:
        if '.wav' in file:
            print(f'Working on {file}')
            data = []

            with wave.open('data/original/'+file, mode='rb') as wav:
                frames = wav.readframes(wav.getnframes())
                sample_width = wav.getsampwidth()
                frame_rate = wav.getframerate()
                dt = np.dtype('uint16')
                dt = dt.newbyteorder('<')
                audio = np.frombuffer(frames, dtype=dt) 

            max_size = math.floor((len(frames) / 2) / 8)

            sizes = list(range(1, 32))
            sizes += list(range(32, 1024, 10))
            sizes += list(range(1024, max_size, 100))

            for msg_size in tqdm(sizes):
                msg = secret_data[:msg_size]

                stego_audio = embed_tan_map(audio, msg)
                try:
                    extracted_msg = extract_tan_map(stego_audio)
                    extracted_msg = extracted_msg.decode()
                except Exception as e:
                    print(e)
                    extracted_msg = ''


                if msg != extracted_msg:
                    print('Failed at', msg_size, 'bytes')
                    break

                mse = compute_mse(audio, stego_audio)
                snr = compute_snr(audio, mse)

                data.append([file, msg_size, mse, snr])

            df2 = pd.DataFrame(data, columns=DF_COLUMNS)
            df = pd.concat([df, df2])
            df.to_csv('results/tanmap_ptp.csv')





if __name__ == '__main__':
    compute_tanmap()
