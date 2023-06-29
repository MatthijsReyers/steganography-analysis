from shutil import copyfile
import subprocess
from tanMap.tanmap import embed_tan_map, extract_tan_map
import os, utils, wave, math
import numpy as np
import pandas as pd
from tqdm import tqdm
import shutil

MAX_SIZE = 256

TMP_WAV = './tmp.wav'
SECRET_OUT = './secret.out.tmp'

DF_COLUMNS = ['File', 'Message size (bytes)', 'mse', 'snr' ]


def generate_partial_secrets(secret_bytes: int):
    secret_bytes
    with open('secret.sherlock.txt', 'r') as file:
        with open(utils.TMP_FILE, 'w+') as out_file:
            bs = ''
            MAX_TRIES = 100
            for i in range(MAX_TRIES):
                chunk = file.read(secret_bytes + 100)
                if chunk == '':
                    file.seek(0)
                bs += chunk
                if len(bs) > secret_bytes:
                    break
            if i == MAX_TRIES:
                raise Exception('MAX_TRIES exceeded')
            out_file.seek(0)
            out_file.write(bs[:secret_bytes])
            out_file.flush()

def apply_hide4pgp(file: str, secret_bytes: int):
    generate_partial_secrets(secret_bytes)
    
    IN_FILE = file
    OUT_FILE = TMP_WAV

    # Hide4pgp is stupid and does not allow you to specify an output file.
    try: copyfile(IN_FILE, OUT_FILE)
    except: subprocess.run(['cp', IN_FILE, OUT_FILE])

    result = subprocess.run(
        [ './hide4pgp', OUT_FILE, utils.TMP_FILE ],
        capture_output=True
    )
    return result.stderr.decode('utf-8') + ' ' + result.stdout.decode('utf-8')

def apply_steghide(file: str, secret_bytes: int, out_file: str):
    generate_partial_secrets(secret_bytes)

    # Get Hide4pgp capacity.
    result = subprocess.run(
        [ 'steghide', 'embed', 
         '--nochecksum',
         '--dontembedname',
         '--force',
         '--embedfile', utils.TMP_FILE, 
         '--coverfile', file, 
         '--encryption', 'none',
         '--passphrase', utils.STEGHIDE_PASS, 
        #  '--compress', '9',
         '--compress', '1',
         '--stegofile', out_file ], 
        capture_output=True
    )
    err = result.stderr.decode('utf-8')
    if 'the cover file is too short to embed the data' in err:
        raise Exception(err + ' ' + file)


def extract_hide4pgp(stegofile: str):
    result = subprocess.run(
        [ 
            './hide4pgp', 
            '-x', stegofile,
            SECRET_OUT,
        ], 
        capture_output=True,
        timeout=10
    )
    res = result.stderr.decode('utf-8')
    if 'Error: File seems not' in res:
        raise Exception(f'Failed to extract secret data: {res}')

def extract_steghide(stegofile: str, out_file: str):
    result = subprocess.run(
        [ 
            'steghide', 'extract', 
            '--force',
            '--passphrase', utils.STEGHIDE_PASS,
            '--stegofile', stegofile,
            '--extractfile', out_file,
        ], 
        capture_output=True
    )
    res = result.stderr.decode('utf-8')
    if not f'wrote extracted data to' in res:
        raise Exception(f'Failed to extract secret data: {res}')
    return True


def load_file(file):
    with wave.open(file, mode='rb') as wav:
        frames = wav.readframes(wav.getnframes())
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        dt = np.dtype('uint16')
        dt = dt.newbyteorder('<')
        audio = np.frombuffer(frames, dtype=dt)
    return sample_width, frame_rate, audio


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


def compute_hide4pgp():
    OUT_DF = 'results/hide4pgp_ptp.csv'
    with open(utils.SECRET_FILE) as secret_file:
        secret_data = secret_file.read()
    secret_data = secret_data*1000

    files = os.listdir('data/original')

    try:
        df = pd.read_csv(OUT_DF, index_col=0)
        already_processed = set(df['File'])
    except:
        df = pd.DataFrame([], columns=DF_COLUMNS)
        already_processed = set()

    hiding_cap = pd.read_csv('./results/hiding_capacity.csv', index_col=0)

    for file in files:
        if file in already_processed:
            print('Skipping', file, '!!!')
            continue
        elif '.wav' in file:
            print(f'Working on {file}')
            data = []

            i = hiding_cap[ hiding_cap['File'] == file ]['Hide4pgp (bytes)'].first_valid_index()
            max_size = math.floor((hiding_cap[ hiding_cap['File'] == file ]['Hide4pgp (bytes)'])[i])

            sizes = list(range(1, 32))
            sizes += list(range(32, 512, 10))
            sizes += list(range(512, max(max_size, 3400), 500))
            if max_size > 3400:
                sizes += list(range(2048, max_size, 10000))
            sizes += [ max_size ]

            for msg_size in tqdm(sizes):
                msg = secret_data[:msg_size]

                try:
                    os.remove(TMP_WAV)
                    os.remove(SECRET_OUT)
                except: pass

                try:
                    x = apply_hide4pgp('data/original/'+file, msg_size)
                    extract_hide4pgp(TMP_WAV)
                    with open(SECRET_OUT) as xxx:
                        extracted_msg = xxx.read()
                except Exception as e:
                    print(x)
                    print(e)
                    extracted_msg = ''

                if msg != extracted_msg:
                    print('Failed at', msg_size, 'bytes')
                    print(x)
                    break
                    mse = None
                    snr = None

                else:
                    _, _, audio = load_file('data/original/'+file)
                    _, _, stego_audio = load_file('tmp.wav')

                    mse = compute_mse(audio, stego_audio)
                    snr = compute_snr(audio, mse)

                data.append([file, msg_size, mse, snr])

            df2 = pd.DataFrame(data, columns=DF_COLUMNS)
            df = pd.concat([df, df2])
            df.to_csv(OUT_DF)


def compute_steghide():
    OUT_DF = 'results/steghide_ptp.csv'
    with open(utils.SECRET_FILE) as secret_file:
        secret_data = secret_file.read()
    secret_data = secret_data*1000

    files = os.listdir('data/original')

    try:
        df = pd.read_csv(OUT_DF, index_col=0)
        already_processed = set(df['File'])
    except:
        df = pd.DataFrame([], columns=DF_COLUMNS)
        already_processed = set()

    hiding_cap = pd.read_csv('./results/hiding_capacity.csv', index_col=0)

    for file in files:
        if file in already_processed:
            print('Skipping', file, '!!!')
            continue
        elif '.wav' in file:
            print(f'Working on {file}')
            data = []

            i = hiding_cap[ hiding_cap['File'] == file ]['StegHide (bytes)'].first_valid_index()
            max_size = math.floor((hiding_cap[ hiding_cap['File'] == file ]['StegHide (bytes)'])[i])

            sizes = list(range(1, 32))
            sizes += list(range(32, 512, 10))
            sizes += list(range(512, max(max_size, 3400), 500))
            if max_size > 3400:
                sizes += list(range(3400, max_size, 10000))
            sizes += [ max_size ]

            for msg_size in tqdm(sizes):
                msg = secret_data[:msg_size]

                try:
                    os.remove(TMP_WAV)
                    os.remove(SECRET_OUT)
                except: pass

                try:
                    x = apply_steghide('data/original/'+file, msg_size, TMP_WAV)
                    extract_steghide(TMP_WAV, SECRET_OUT)
                    with open(SECRET_OUT) as xxx:
                        extracted_msg = xxx.read()
                except Exception as e:
                    print(x)
                    print(e)
                    extracted_msg = ''

                if msg != extracted_msg:
                    print('Failed at', msg_size, 'bytes')
                    print(x)
                    break
                    mse = None
                    snr = None

                else:
                    _, _, audio = load_file('data/original/'+file)
                    _, _, stego_audio = load_file('tmp.wav')

                    mse = compute_mse(audio, stego_audio)
                    snr = compute_snr(audio, mse)

                data.append([file, msg_size, mse, snr])

            df2 = pd.DataFrame(data, columns=DF_COLUMNS)
            df = pd.concat([df, df2])
            df.to_csv(OUT_DF)


if __name__ == '__main__':
    # compute_hide4pgp()
    compute_steghide()
    # try:
    #     os.remove(TMP_WAV)
    #     os.remove(SECRET_OUT)
    # except: pass
    
    # file = 'disco.00001.wav'
    # msg_size = 238012

    # apply_hide4pgp('data/original/'+file, msg_size)
    # extract_hide4pgp(TMP_WAV)

    # with open(utils.SECRET_FILE) as secret_file:
    #     secret_data = secret_file.read()
    # secret_data = secret_data*1000

    # msg = secret_data[:msg_size]

    # with open(SECRET_OUT) as xxx:
    #     extracted_msg = xxx.read()

    # print(len(msg), len(extracted_msg), extracted_msg == msg)

    # print(msg)
    # print(extracted_msg)
