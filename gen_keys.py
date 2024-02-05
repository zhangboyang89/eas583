from web3 import Web3
import eth_account
import os
from eth_account import Account


def get_keys(challenge, keyId=0, filename="eth_mnemonic.txt"):
    """
    Generate a stable private key
    challenge - byte string
    keyId (integer) - which key to use
    filename - filename to read and store mnemonics

    Each mnemonic is stored on a separate line
    If fewer than (keyId+1) mnemonics have been generated, generate a new one and return that
    """

    w3 = Web3()

    with open(filename, 'r') as file:
        mnemonics = file.readlines()

    while len(mnemonics) <= keyId:
        new_mnemonic = w3.eth.account.create().key.hex()
        mnemonics.append(new_mnemonic + '\n')
        with open(filename, 'a') as file:
            file.write(new_mnemonic + '\n')

    acct = Account.from_key(mnemonics[keyId].strip())
    msg = eth_account.messages.encode_defunct(challenge)
    sig = acct.sign_message(msg)

    eth_addr = acct.address

    assert eth_account.Account.recover_message(
        msg, signature=sig.signature.hex()
    ) == eth_addr, f"Failed to sign message properly"

    # return sig, acct #acct contains the private key
    return sig, eth_addr




if __name__ == "__main__":
    for i in range(4):
        challenge = os.urandom(64)
        sig, addr = get_keys(challenge=challenge, keyId=i,
                             filename=r'H:\My Drive\Programs\python\mcit\eas583\eth_mnemonic.txt')
        print(addr)
