import os, subprocess
import wave
from utils import STEGHIDE_PASS, device
from gan1 import spectrogram, payload, gan
from gan1.utils import load_wav
from tqdm import tqdm
import numpy as np
from tanMap.tanmap import extract_tan_map

def extract_steghide(stego_file: str) -> bytes:
    output_file = 'tmp/steghide.tmp'

    try: os.remove(output_file)
    except: pass

    result = subprocess.run(
        [ 
            'steghide', 'extract', 
            '--force',
            '--passphrase', STEGHIDE_PASS,
            '--stegofile', stego_file,
            '--extractfile', output_file,
        ], 
        capture_output=True
    )
    # print(result.stdout.decode(), end='')
    # print(result.stderr.decode(), end='')
    res = result.stderr.decode('utf-8')
    if not f'wrote extracted data to' in res:
        raise Exception(f'Failed to extract secret data: {res}')

    # Read out data from extracted file.
    with open(output_file, 'rb') as result:
        data = b''
        x = 'a'
        while len(x) > 0:
            x = result.read()
            data += x

    return data


def extract_hide4pgp(stego_file: str) -> bytes:
    output_file = 'tmp/hide4pgp.tmp'
    try: os.remove(output_file)
    except: pass
    result = subprocess.run(
        [ 
            './hide4pgp', 
            '-x', stego_file,
            output_file,
        ], 
        capture_output=True
    )
    res = result.stderr.decode('utf-8') + '\n' + result.stdout.decode('utf-8')
    if 'Error' in res:
        raise Exception(f'Failed to extract secret data: {res}')
    
    # Read out data from extracted file.
    with open(output_file, 'rb') as result:
        data = b''
        x = 'a'
        while len(x) > 0:
            x = result.read()
            data += x

    return data


def extract_gan(stego_file: str) -> bytes:
    wav, bitrate, bits = load_wav(stego_file)

    # Convert wav to spectrogram.
    stego_spec, hop_length = spectrogram.wav_to_spectro(wav)
    _, H, W = stego_spec.size()
    stego_spec = stego_spec[None].to(device)
    # stego_spec = stego_spec.detach()

    try:
        text_out, count = gan.decode_message(stego_spec)
    except Exception as e:
        print(e)
        text_out = ''

    return text_out.encode()


def extract_tan(stego_file: str) -> bytes:

    with wave.open(stego_file, mode='rb') as wav:
        frames = wav.readframes(wav.getnframes())
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        dt = np.dtype('uint16')
        dt = dt.newbyteorder('<')
        stego_audio = np.frombuffer(frames, dtype=dt) 
    
    out = extract_tan_map(stego_audio)
    return out