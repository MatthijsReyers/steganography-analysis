import os, math
from extract import extract_gan, extract_hide4pgp, extract_steghide, extract_tan
from utils import SECRET_FILE, NOISE_TYPES
import pandas as pd
import numpy as np

ROBUST_CSV = 'results/robustness.csv'
COLUMNS = ['File', 'Source file', 'Noise level (db)', 'Method', 'Expected size', 'Extracted size', 'Bit errors', 'Bit errors (%)']

method_names = { 'hide4pgp': 'Hide4pgp', 'steghide': 'StegHide' }
methods = [
    # 'hide4pgp', 
    # 'steghide',
    # 'gan1',
    'tan',
]
extractors = [
    # extract_hide4pgp, 
    # extract_steghide,
    # extract_gan,
    extract_tan,
]
noise_types = NOISE_TYPES

hiding_capacity = pd.read_csv('results/hiding_capacity.csv', index_col=0)
hiding_capacity_gan = pd.read_csv('results/gan1_sherlock.csv', index_col=0)
hiding_capacity_tan = pd.read_csv('results/tanmap_ptp.csv', index_col=0)

secret = b''
with open(SECRET_FILE, 'rb') as secret_file:
    x = 'a'
    while len(x) > 0:
        x = secret_file.read()
        secret += x


def get_bit_errors(a, b):
    res = 0
    for i in range(0,8):
        if ((a >> i) & 0b01) != ((b >> i) & 0b01):
            res += 1
    return res   


def get_expected_size(file, method) -> int:
    if method == 'gan1':
        x = hiding_capacity_gan[hiding_capacity_gan['File'] == file][f'Hiding capacity (bits)']
        return round(x.item() / 8)
    if method == 'tan':
        x = hiding_capacity_tan[hiding_capacity_tan['File'] == file]
        x = x.groupby('File').max()
        x = x['Message size (bytes)']
        return int(x.item())
    name = method_names[method]
    x = hiding_capacity[hiding_capacity['File'] == file][f'{name} (bytes)']
    return int(x.item())

def count_bit_errors(a, b, size=None):
    if size == None:
        size = min(len(a), len(b))
    counter = 0
    checking = min(len(a), len(b), size)
    for i in range(checking):
        counter += get_bit_errors(a[i], b[i])
    # Assume missing bits are "errors"
    counter += 8 * max(0, size - checking)
    return counter


if __name__ == '__main__':
    try:
        df = pd.read_csv(ROBUST_CSV, index_col=0)
    except:
        df = pd.DataFrame([], columns=COLUMNS)


    for method, extract in zip(methods, extractors):
        print(f'Starting on {method}')
        for noise_type in noise_types:
            data = list()
            
            folder = f'data/{method}/robustness/{noise_type}/'
            for file in os.listdir(folder):
                if '.wav' in file:
                    stego_file = folder+file
                    original_file = file
                    original_file = file.split('_')[0] + '.wav'
                    db = int(file.split('_')[1].replace('db.wav', ''))
                    expected_size = get_expected_size(original_file, method)
                    
                    try:
                        result = extract(stego_file)
                        truth = secret[:expected_size]

                        bit_err = count_bit_errors(result, truth, expected_size)
                        result_size = len(result)

                    except Exception as e:
                        bit_err = expected_size * 8
                        result_size = 0

                    try:
                        bit_err_percent = (bit_err / (expected_size * 8))
                    except:
                        bit_err_percent = 1

                    data.append([
                        original_file, file, db, method, expected_size, result_size, bit_err, bit_err_percent
                    ])

            print(f'Finished noise type {noise_type}')
            df2 = pd.DataFrame(data, columns=COLUMNS)
            df = pd.concat([df, df2])
            df.to_csv(ROBUST_CSV)

# def compute_bit_errors(ground_truth: bytes):
#     result_bytes = bytes()
#     with open(TMP_FILE, 'rb') as result:
#         result_bytes = result.read()
#         assert len(result_bytes) > 0

#     bit_errors = 0
#     for i, b in enumerate(result_bytes):
#         if b != ground_truth[i]:
#             bit_errors += get_bit_errors(ground_truth[i], b)

#     x = len(result_bytes)
#     del result_bytes

#     return bit_errors, x


# def compute_result(folder, file, method, ground_truth, hc: pd.DataFrame):
#     stego_file = folder+'/'+file

    # src = file.split('_')[0] + '.wav'
    # db = int(file.split('_')[1].replace('db.wav', ''))
#     name = 'StegHide' if method == 'steghide' else 'Hide4pgp'
#     expected_size = int(list(hc.loc[hc['File'] == src].iterrows())[0][1][name+' (bytes)'])

#     if method == 'hide4pgp': res = extract_hide4pgp(stego_file)
#     elif method == 'steghide': res = extract_steghide(stego_file)
#     else: raise Exception(f'Unknown method: {method}')

#     bits = expected_size * 8
#     size = 0
#     if res:
#         try: 
#             bits, size = compute_bit_errors(ground_truth)
#             bits += (expected_size - size) * 8
#             if size > expected_size:
#                 bits = expected_size * 8
#         except: pass
    
#     return [file, src, db, method, expected_size, size, bits, (bits / (expected_size * 8)) * 100]


# def compute_robustness(methods, noise_types):
#     ground_truth = get_ground_truth()
#     hiding_capacity = get_hiding_capacity()
    
#     data = list()

#     for method in methods:
#         for noise_type in noise_types:
#             folder = f'./data/{method}/robustness/{noise_type}'
#             for file in tqdm(os.listdir(folder), f'Computing robustness {method} {noise_type}'):
#                 if '.wav' in file:
#                     x = compute_result(folder, file, method, ground_truth, hiding_capacity)
#                     data.append(x)

#     df = pd.DataFrame(data, columns=['File', 'Source file', 'Noise level (db)', 'Method', 'Expected size', 'Extracted size', 'Bit errors', 'Bit errors (%)'])
#     return df


# if __name__ == '__main__':
#     # compute_robustness(METHODS, NOISE_TYPES)
#     df = compute_robustness(['hide4pgp', 'steghide'], ['wind'])
#     df.to_csv('results/robustness.csv')