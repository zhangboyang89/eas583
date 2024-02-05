import hashlib
import os
import random
import string

def hash_collision(k):
    if not isinstance(k, int):
        print("hash_collision expects an integer")
        return (b'\x00', b'\x00')
    if k < 0:
        print("Specify a positive number of bits")
        return (b'\x00', b'\x00')

    def random_string():
        str_len = 10
        return ''.join(random.choice(string.ascii_letters +
                                     string.digits) for _ in range(str_len))

    def match_k(hash1, hash2, k):
        # Convert the hex hashes to binary
        bin_hash1 = bin(int(hash1, 16))[2:].zfill(256)
        bin_hash2 = bin(int(hash2, 16))[2:].zfill(256)
        return bin_hash1[-k:] == bin_hash2[-k:]

    x = random_string()
    x_hash = hashlib.sha256(x.encode('utf-8')).hexdigest()

    while True:
        # Generate a new random string and hash it
        y = random_string()
        y_hash = hashlib.sha256(y.encode('utf-8')).hexdigest()

        # Check if the last k bits match
        if match_k(x_hash, y_hash, k):
            return x.encode('utf-8'), y.encode('utf-8')

