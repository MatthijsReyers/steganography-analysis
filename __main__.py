from get_data import get_data
from generate_stego_data import generate_stego_data
from compute_hiding_capacity import compute_hiding_capacity
from generate_secret_data import generate_secret_data
from compute_transparency import compute_transparency

# Copies a select view files over from the 'Gztan' and 'Timit' folders.
get_data()

# Generates a file with random bytes to be used as secret data.
generate_secret_data()

# Computes a pandas dataframe with the hiding capacity of each tool/method.
hiding_capacity = compute_hiding_capacity()
hiding_capacity.to_csv('results/hiding_capacity.csv')

# Generate the stego data 
generate_stego_data(hiding_capacity)

# Compute perceptual transparency of different methods.
compute_transparency()

