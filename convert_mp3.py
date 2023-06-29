import os, utils, subprocess

def convert_mp3():
    utils.makeDirectory('data/mp3')

    ORIGINALS = 'data/original'

    for wav_file in os.listdir(ORIGINALS):
        mp3_file = ORIGINALS.replace('original', 'mp3') + '/' + wav_file.replace('wav', 'mp3')
        wav_file = ORIGINALS + '/' + wav_file

        result = subprocess.run(
            [ 'ffmpeg', '-i', wav_file, '-vn', '-b:a', '320k', mp3_file ], 
            capture_output=True
        ).stdout.decode('utf-8')

if __name__ == '__main__':
    convert_mp3()
