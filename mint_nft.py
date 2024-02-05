from web3 import Web3
import json
from eth_account import Account
import os

# Connect to the Avalanche Fuji Testnet
w3 = Web3(Web3.HTTPProvider('https://api.avax-test.network/ext/bc/C/rpc'))

# Contract address and ABI
contract_address = '0x85ac2e065d4526FBeE6a2253389669a12318A412'
with open(r'H:\My Drive\Programs\python\mcit\eas583\NFT.abi', 'r') as f:
    contract_abi = json.load(f)

# Set up the contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)



# Your account details
private_key = '0x152d1949e8feacbf4a75acfe0679930a4c9d1bb57d88246b16aeca8627e1067b'  # Be cautious with your private key
account = Account.from_key(private_key)
nonce = w3.eth.get_transaction_count(account.address)

claim_nonce = os.urandom(32)  # 32 bytes random nonce

# Prepare the transaction
claim_txn = contract.functions.claim(account.address, Web3.to_hex(claim_nonce)).build_transaction({
    'chainId': 43113,  # Chain ID for Avalanche Fuji Testnet
    'gas': 2000000,
    'gasPrice': w3.to_wei('50', 'gwei'),
    'nonce': nonce,
})

# Sign the transaction
signed_txn = w3.eth.account.sign_transaction(claim_txn, private_key=private_key)

# Send the transaction
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

# Wait for the transaction to be mined
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)