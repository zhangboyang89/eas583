from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware  # Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"


def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts[chain]


def getContractABI(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    if chain == 'source':
        # look for Deposit events
        for item in contracts[chain]['abi']:
            if item['type'] == 'event':
                if item['name'] == 'Deposit':
                    return item
    elif chain == 'destination':
        # look for Unwrap events
        for item in contracts[chain]['abi']:
            if item['type'] == 'event':
                if item['name'] == 'Unwrap':
                    return item


def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    w3_source = connectTo('avax')
    w3_destination = connectTo('bsc')

    # Inject POA middleware for testnets that use Proof of Authority
    w3_source.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3_destination.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Load contract ABIs and addresses
    source_contract_abi = getContractInfo('source')['abi']
    destination_contract_abi = getContractInfo('destination')['abi']
    source_contract_address = getContractInfo('source')['address']
    destination_contract_address = getContractInfo('destination')['address']

    # Create contract instances
    source_contract = w3_source.eth.contract(address=source_contract_address, abi=source_contract_abi)
    destination_contract = w3_destination.eth.contract(address=destination_contract_address,
                                                       abi=destination_contract_abi)

    private_key = '0x152d1949e8feacbf4a75acfe0679930a4c9d1bb57d88246b16aeca8627e1067b'
    warden_account = w3_source.eth.account.from_key(private_key)

    def call_wrap_function(token_address, recipient_address, amount):
        nonce = w3_destination.eth.get_transaction_count(warden_account.address)
        tx = destination_contract.functions.wrap(token_address, recipient_address, amount).build_transaction({
            'chainId': 97,
            'gas': 2000000,
            'gasPrice': w3_destination.eth.gas_price,
            'nonce': nonce,
        })
        signed_tx = w3_destination.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3_destination.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")

    def call_withdraw_function(token_address, recipient_address, amount):
        nonce = w3_source.eth.get_transaction_count(warden_account.address)
        # Build the transaction to call the `withdraw` function
        tx = source_contract.functions.withdraw(token_address, recipient_address, amount).build_transaction({
            'chainId': 43113,
            'gas': 2000000,
            'gasPrice': w3_source.eth.gas_price,
            'nonce': nonce,
        })
        # Sign the transaction with the warden's private key
        signed_tx = w3_source.eth.account.sign_transaction(tx, private_key)
        # Send the signed transaction
        tx_hash = w3_source.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")

    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    if chain == 'source':
        event_abi = getContractABI(chain)
        contract_address = getContractInfo(chain)['address']
        contract = w3_source.eth.contract(address=contract_address, abi=event_abi)

        arg_filter = {}
        end_block = w3_source.eth.get_block_number()
        start_block = end_block - 5
        print(f"Scanning blocks {start_block} - {end_block} on {chain}")
        event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block,
                                                             argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        for evt in events:
            call_wrap_function(evt.args['token'], evt.args['recipient'], evt.args['amount'])

    elif chain == 'destination':
        event_abi = getContractABI(chain)
        contract_address = getContractInfo(chain)['address']
        contract = w3_source.eth.contract(address=contract_address, abi=event_abi)

        arg_filter = {}
        end_block = w3_source.eth.get_block_number()
        start_block = end_block - 5
        print(f"Scanning blocks {start_block} - {end_block} on {chain}")
        event_filter = contract.events.Unwrap.create_filter(fromBlock=start_block, toBlock=end_block,
                                                            argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        for evt in events:
            call_withdraw_function(evt.args['token'], evt.args['recipient'], evt.args['amount'])

#
# def register_token(token_address_to_register):
#     # Connect to the network
#     w3_source = connectTo('avax')
#
#     source_contract_abi = getContractInfo('source')['abi']
#     source_contract_address = getContractInfo('source')['address']
#
#     # Create contract instances
#     source_contract = w3_source.eth.contract(address=source_contract_address, abi=source_contract_abi)
#
#     # Admin account
#     private_key = '0x152d1949e8feacbf4a75acfe0679930a4c9d1bb57d88246b16aeca8627e1067b'
#     admin_account = w3_source.eth.account.from_key(private_key)
#
#     # Build transaction
#     nonce = w3_source.eth.get_transaction_count(admin_account.address)
#     transaction = source_contract.functions.registerToken(token_address_to_register).build_transaction({
#         'chainId': w3_source.eth.chain_id,
#         'gas': 200000,  # You may need to adjust this value
#         'gasPrice': w3_source.eth.gas_price,
#         'nonce': nonce,
#     })
#
#     # Sign transaction
#     signed_txn = w3_source.eth.account.sign_transaction(transaction, private_key)
#
#     # Send transaction
#     txn_hash = w3_source.eth.send_raw_transaction(signed_txn.rawTransaction)
#     print(f"Transaction hash: {txn_hash.hex()}")
#
#     # Wait for the transaction to be mined
#     txn_receipt = w3_source.eth.wait_for_transaction_receipt(txn_hash)
#     print(f"Token registered. Transaction receipt: {txn_receipt}")
#
#
# if __name__ == '__main__':
#     register_token('0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c')
#     register_token('0x0773b81e0524447784CcE1F3808fed6AaA156eC8')