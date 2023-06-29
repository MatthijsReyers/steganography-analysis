import os, shutil, random, platform
from utils import makeDirectory
from tqdm import tqdm
import pandas as pd

def get_gztan_data():
    GZTAN_DIR = './Gztan/Data/genres_original/'
    GZTAN_SAMPLES_PER_GENRE = 5

    for genres in tqdm(os.listdir(GZTAN_DIR), '[*] Selecting GZTAN data'):
        counter = 0
        for file in os.listdir(GZTAN_DIR+genres):
            if '.wav' in file:
                counter += 1
                shutil.copy(GZTAN_DIR+genres+'/'+file, 'data/original')
            if counter == GZTAN_SAMPLES_PER_GENRE:
                break


def get_timit_data():
    TIMIT_DIR = './Timit/data/'

    path = 'path_from_data_dir'
    if 'windows' in platform.system().lower():
        path = 'path_from_data_dir_windows'

    # Read dataset index.
    timit_dataset = pd.read_csv('./Timit/test_data.csv')

    # Get all the speaker ids.
    speaker_ids = timit_dataset['speaker_id']
    speaker_ids = speaker_ids[speaker_ids.notna()].unique()

    # Seed random for consistent results.
    random.seed(5453219)

    # Pick 10 random speakers
    speakers = random.choices(speaker_ids, k=10)

    for speaker in tqdm(list(speakers), '[*] Selecting TIMIT data'):
        d = timit_dataset[timit_dataset['speaker_id'] == speaker]
        d = d[d['filename'].str.contains('.wav')]

        # Pick 3 random audio files for that speaker
        for (i, file) in random.choices(list(d.iterrows()), k=3):
            shutil.copy(TIMIT_DIR+file[path], 'data/original/spoken.'+file['filename'].replace('.WAV',''))


def get_data():
    makeDirectory('data')
    makeDirectory('data/original')
    get_gztan_data()
    get_timit_data()


if __name__ == '__main__':
    get_data()
