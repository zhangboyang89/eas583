"""
    We are agnostic about how the students submit their merkle proofs to the on-chain contract
    But if they were to submit using Python, this would be a good way to do it
"""
from web3 import Web3
import json
import os
from eth_account import Account
from web3.middleware import geth_poa_middleware #Necessary for POA chains
import sys
import random
from hexbytes import HexBytes


def hashPair( a,b ):
    """
        The OpenZeppelin Merkle Tree Validator we use sorts the leaves
        https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MerkleProof.sol#L217
        So you must sort the leaves as well

        Also, hash functions like keccak are very sensitive to input encoding, so the solidity_keccak function is the function to use

        Another potential gotcha, if you have a prime number (as an int) bytes(prime) will *not* give you the byte representation of the integer prime
        Instead, you must call int.from_bytes(prime,'big').

        This function will hash leaves in a Merkle Tree in a way that is compatible with the way the on-chain validator hashes leaves
    """
    if a < b:
        return Web3.solidity_keccak( ['bytes32','bytes32'], [a,b] )
    else:
        return Web3.solidity_keccak( ['bytes32','bytes32'], [b,a] )

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


if __name__ == "__main__":

    def is_prime(n):
        """Check if a number is prime."""
        if n <= 1:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True


    def generate_primes(n):
        """Generate the first n prime numbers."""
        primes = []
        num = 2
        while len(primes) < n:
            if is_prime(num):
                primes.append(num)
            num += 1
        return primes


    primes = generate_primes(8192)

    def prime_to_bytes32(prime):
        #return Web3.solidity_keccak(['uint256'], [prime])
        return prime.to_bytes(32, 'big')

    leaves = [prime_to_bytes32(prime) for prime in primes]
    leaves.sort()

    def build_tree(leaves):
        if len(leaves) == 1:
            return leaves[0], {leaves[0]: []}

        new_leaves = []
        proofs = {}
        for i in range(0, len(leaves), 2):
            left = leaves[i]
            right = leaves[i + 1] if i + 1 < len(leaves) else left
            new_leaf = hashPair(left, right)
            new_leaves.append(new_leaf)

            proofs[left] = proofs.get(left, []) + [right]
            proofs[right] = proofs.get(right, []) + [left]
            proofs[new_leaf] = proofs.get(left, []) + proofs.get(right, [])

        root, child_proofs = build_tree(new_leaves)
        proofs.update(child_proofs)
        return root, proofs


    root, proofs = build_tree(leaves)

    selected_index = 425  # For example, the first leaf
    selected_leaf = leaves[selected_index]

    def get_proof(root, proofs, selected_leaf):
        proof = []
        while selected_leaf != root:
            sibling = proofs[selected_leaf][0]
            proof.append(sibling)
            selected_leaf = hashPair(selected_leaf, sibling)
        return proof

    proof = get_proof(root, proofs, selected_leaf)


    chain = 'avax'

    with open( r"H:\My Drive\Programs\python\mcit\eas583\validator.abi", "r" ) as f:
        abi = json.load(f)

    address = "0xb728f421b33399Ae167Ff01Ad6AA8fEFace845F7"

    w3 = connectTo(chain)
    contract = w3.eth.contract( abi=abi, address=address )

    private_key = '0x152d1949e8feacbf4a75acfe0679930a4c9d1bb57d88246b16aeca8627e1067b'
    account = Account.from_key(private_key)

    # Prepare the function with arguments

    nonce = w3.eth.get_transaction_count(account.address)
    transaction = contract.functions.submit(proof, selected_leaf).build_transaction({
        'chainId': 43113,  # Mainnet; change accordingly
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    # Sign and send the transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Wait for the transaction to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(tx_receipt['status'])
    print(w3.eth.get_balance(account.address))