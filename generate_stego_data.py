import wave
import pandas as pd
import subprocess
from compute_robustness import extract_steghide
from utils import makeDirectory, STEGHIDE_PASS, TMP_FILE
from shutil import copyfile
from tqdm import tqdm
import numpy as np

def generate_partial_secrets(secret_bytes: int):
    secret_bytes
    with open('secret.sherlock.txt', 'r') as file:
        with open(TMP_FILE, 'w+') as out_file:
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
    
    IN_FILE = 'data/original/' + file
    OUT_FILE = 'data/hide4pgp/' + file

    # Hide4pgp is stupid and does not allow you to specify an output file.
    try: copyfile(IN_FILE, OUT_FILE)
    except: subprocess.run(['cp', IN_FILE, OUT_FILE])

    # Get Hide4pgp capacity.
    result = subprocess.run(
        [ './hide4pgp', OUT_FILE, TMP_FILE ],
        capture_output=True
    )
    # print(result.stderr.decode('utf-8'), end='')
    # print(result.stdout.decode('utf-8'), end='')


def update_hiding(file, method, value):
    print(f'Updating hc for {file}: {value}')
    df = pd.read_csv('results/hiding_capacity.csv', index_col=0)
    df.loc[df['File'] == file, f'{method} (bytes)'] = value
    total = int(df.loc[df['File'] == file]['Size (bytes)'])
    df.loc[df['File'] == file, f'{method} (%)'] = value / total
    df.to_csv('results/hiding_capacity.csv')


def apply_steghide(file: str, secret_bytes: int):
    generate_partial_secrets(secret_bytes)

    IN_FILE = 'data/original/' + file
    OUT_FILE = 'data/steghide/' + file

    # Get Hide4pgp capacity.
    result = subprocess.run(
        [ 'steghide', 'embed', 
         '--nochecksum',
         '--dontembedname',
         '--force',
         '--embedfile', TMP_FILE, 
         '--coverfile', IN_FILE, 
         '--encryption', 'none',
         '--passphrase', STEGHIDE_PASS, 
        #  '--compress', '9',
         '--compress', '1',
         '--stegofile', OUT_FILE ], 
        capture_output=True
    )
    err = result.stderr.decode('utf-8')
    if 'the cover file is too short to embed the data' in err:
        raise Exception(err + ' ' + IN_FILE)
    
    # extract_steghide(OUT_FILE)
    # with open(TMP_FILE) as out_file:
    #     extracted_msg = ''
    #     msg = 'a'
    #     while len(msg) > 0:
    #         msg = out_file.read(secret_bytes)
    #         extracted_msg += msg
    
    # print(len(extracted_msg), secret_bytes)

    # print(result.stderr.decode('utf-8'), end='', file=sys.stderr)
    # print(result.stdout.decode('utf-8'), end='')


def apply_tan(file: str, secret_bytes: int):
    with wave.open(file, mode='rb') as wav:
        frames = wav.readframes(wav.getnframes())
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        dt = np.dtype('uint16')
        dt = dt.newbyteorder('<')
        audio = np.frombuffer(frames, dtype=dt) 
    

    msg = b"hello world, its a beautiful day"*1000
    msg = b"""-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu
KUpRKfFLfRYC9AIKjbJTWit+CqvjWYzvQwECAwEAAQJAIJLixBy2qpFoS4DSmoEm
o3qGy0t6z09AIJtH+5OeRV1be+N4cDYJKffGzDa88vQENZiRm0GRq6a+HPGQMd2k
TQIhAKMSvzIBnni7ot/OSie2TmJLY4SwTQAevXysE2RbFDYdAiEBCUEaRQnMnbp7
9mxDXDf6AU0cN/RPBjb9qSHDcWZHGzUCIG2Es59z8ugGrDY+pxLQnwfotadxd+Uy
v/Ow5T0q5gIJAiEAyS4RaI9YG8EWx/2w0T67ZUVAw8eOMB6BIUg0Xcu+3okCIBOs
/5OiPgoTdSy7bcF9IGpSE8ZgGKzgYQVZeN97YE00
-----END RSA PRIVATE KEY-----"""

    stego_audio = embed_tan_map(audio, msg)
    out = extract_tan_map(stego_audio, msg_size=len(msg))

    with wave.open('demo.wav', mode='wb') as wav:
        frames = stego_audio.tobytes()
        wav.setsampwidth(sample_width)
        wav.setnchannels(1)
        wav.setframerate(frame_rate)
        wav.writeframes(frames)

def generate_stego_data(hiding_capacity: pd.DataFrame):
    makeDirectory('data/hide4pgp')
    makeDirectory('data/steghide')

    rows = list(hiding_capacity.iterrows())

    for i, row in tqdm(rows, '[*] Generating stego files'):
        file = row['File']
        apply_hide4pgp(file, int(row['Hide4pgp (bytes)']))

        # Steghide application has a stupid bug where it will report a higher hiding capacity than 
        # it can actually realize, so we need to detect a failure and scale back the HC until a 
        # real value is found.
        steghide_bytes = int(row['StegHide (bytes)'])
        try: 
            apply_steghide(file, steghide_bytes)
        except:
            for bs in range(steghide_bytes, 0, -1):
                try:
                    apply_steghide(file, bs)
                    break
                except Exception as e: 
                    pass
            update_hiding(file, 'StegHide', bs)




if __name__ == '__main__':
    hiding_capacity = pd.read_csv('results/hiding_capacity.csv', index_col=0)
    generate_stego_data(hiding_capacity)
