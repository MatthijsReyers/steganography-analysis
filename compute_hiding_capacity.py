import os, subprocess, re, wave
from utils import STEGHIDE_PASS, makeDirectory
import pandas as pd
from tqdm import tqdm

HIDE4PGP_REGEX = r"(You may hide up to )(\d+)( bytes in)"
STEGHIDE_REGEX = r"(capacity: )(.+)(\n)"

def compute_hiding_capacity() -> pd.DataFrame:
    makeDirectory('results')

    data = list()

    for audio in tqdm(os.listdir('data/original'), '[*] Computing hiding capacity'):
        url = 'data/original/'+audio

        # Get audio file size:
        with wave.open(url, 'rb') as wav_file:
            frames = wav_file.getnframes()
            wav_bytes = wav_file.readframes(999999999999999999999999999999)
            wav_bytes = len(wav_bytes)

        # Get Hide4pgp capacity.
        result = subprocess.run(
            [ './hide4pgp', '-i', url ], 
            capture_output=True
        ).stderr.decode('utf-8')
        result = re.search(HIDE4PGP_REGEX, result)
        hide4pgp_byte_count = int(result.group(2))

        # Get steghide capacity.
        result = subprocess.run(
            [ 'steghide', '--info', '--passphrase', STEGHIDE_PASS, url ], 
            capture_output=True
        ).stdout.decode('utf-8')
        result = re.search(STEGHIDE_REGEX, result).group(2)
        multiplier = 0
        if 'KB' in result:
            result = result.replace('KB', '')
            multiplier = 1000
        result = float(result.replace(',', '.').strip())
        steghide_byte_count = multiplier * result

        data.append([audio, wav_bytes, hide4pgp_byte_count, steghide_byte_count])


    df = pd.DataFrame(data, columns=['File', 'Size (bytes)', 'Hide4pgp (bytes)', 'StegHide (bytes)'])
    df['Hide4pgp (%)'] = 100 * (df['Hide4pgp (bytes)'] / df['Size (bytes)'])
    df['StegHide (%)'] = 100 * (df['StegHide (bytes)'] / df['Size (bytes)'])

    return df


if __name__ == '__main__':

    df = compute_hiding_capacity()
    df.to_csv('results/hiding_capacity.csv')
