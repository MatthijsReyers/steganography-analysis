import os, sys, torch

NOISE_TYPES = ['wind', 'chirping_birds', 'rain', 'crickets']
METHODS = ['steghide', 'hide4pgp']

STEGHIDE_PASS = 'a47ie67nc7opwp932mds83mr6vcbjd02'
TMP_FILE = 'secret.tmp.bin'
SECRET_FILE = 'secret.sherlock.txt'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def makeDirectory(dir: str):
    try: os.mkdir(dir)
    except FileExistsError: pass

