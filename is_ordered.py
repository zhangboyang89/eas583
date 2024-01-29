from web3 import Web3
import random
import json

rpc_url = "https://mainnet.infura.io/v3/a5abf3836c914bf9a102f468b8475100"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    pass
else:
    print("Failed to connect to Ethereum node!")

"""
Takes a block number
Returns a boolean that tells whether all the transactions in the block are ordered by priority fee

Before EIP-1559, a block is ordered if and only if all transactions are sorted in decreasing order of the gasPrice field

After EIP-1559, there are two types of transactions
    *Type 0* The priority fee is tx.gasPrice - block.baseFeePerGas
    *Type 2* The priority fee is min( tx.maxPriorityFeePerGas, tx.maxFeePerGas - block.baseFeePerGas )

Conveniently, most type 2 transactions set the gasPrice field to be min( tx.maxPriorityFeePerGas + block.baseFeePerGas, tx.maxFeePerGas )
"""


def is_ordered_block(block_num):

    block = w3.eth.get_block(block_num)
    transactions = block['transactions']
    ls_priority_fee = []

    if not transactions:
        return True

    for t_id in transactions:
        tx = w3.eth.get_transaction(t_id)
        if tx['type'] == 0 or 'gasPrice' in tx:
            priority_fee = tx['gasPrice']
        elif tx['type'] == 2:
            priority_fee = min(tx['maxPriorityFeePerGas'], tx['maxFeePerGas'] - block['baseFeePerGas'])
        else:
            raise ValueError("Transaction Incorrect")

        ls_priority_fee.append(priority_fee)

    return ls_priority_fee == sorted(ls_priority_fee, reverse=True)


"""
This might be useful for testing
"""
if __name__ == "__main__":
    latest_block = w3.eth.get_block_number()

    london_hard_fork_block_num = 12965000
    assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

    n = 5

    for _ in range(n):
        # Pre-London
        block_num = random.randint(1, london_hard_fork_block_num - 1)
        ordered = is_ordered_block(block_num)
        if ordered:
            print(f"Block {block_num} is ordered")
        else:
            print(f"Block {block_num} is not ordered")

        # Post-London
        block_num = random.randint(london_hard_fork_block_num, latest_block)
        ordered = is_ordered_block(block_num)
        if ordered:
            print(f"Block {block_num} is ordered")
        else:
            print(f"Block {block_num} is not ordered")
