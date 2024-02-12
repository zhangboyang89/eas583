import eth_account
from eth_account import Account


def sign_challenge(challenge):
    """
        Takes a challenge (string)
        Returns addr, sig
        where addr is an ethereum address (in hex)
        and sig is a signature (in hex)
    """
    private_key = '0x152d1949e8feacbf4a75acfe0679930a4c9d1bb57d88246b16aeca8627e1067b'
    acct = Account.from_key(private_key)
    msg = eth_account.messages.encode_defunct(text=challenge)
    sig = acct.sign_message(msg)

    addr = acct.address

    assert eth_account.Account.recover_message(
        msg, signature=sig.signature.hex()
    ) == addr, f"Failed to sign message properly"

    return addr, sig.signature.hex()


if __name__ == "__main__":
    """
        This may help you test the signing functionality of your code
    """
    import random
    import string

    letters = string.ascii_letters
    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32))

    addr, sig = sign_challenge(challenge)

    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)

    if eth_account.Account.recover_message(
            eth_encoded_msg, signature=sig) == addr:
        print(f"Success: signed the challenge {challenge} using address {addr}!")
    else:
        print(f"Failure: The signature does not verify!")
        print(f"signature = {sig}")
        print(f"address = {addr}")
        print(f"challenge = {challenge}")
