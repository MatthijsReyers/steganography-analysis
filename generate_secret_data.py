import random
from utils import SECRET_FILE

ascii_bytes = 'abcdefghijklmnopqrstuvwxyz'
ascii_bytes += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_bytes += '0123456789'
ascii_bytes += '-=[]{};:,.<>/?'

ascii_bytes = ascii_bytes

def generate_secret_data():
    DATA_SIZE = 2**20
    RANDOM_SEED = 82394323205
    
    random.seed(RANDOM_SEED)

    with open('secret.txt', 'bw+') as file:
        # file.write(random.randbytes(DATA_SIZE).replace(b'\x00', b''))
        data = ''.join(random.choices(ascii_bytes, k=DATA_SIZE))
        file.write(data.encode())

if __name__ == '__main__':
    generate_secret_data()
