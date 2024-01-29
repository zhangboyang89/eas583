from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
import requests
import json
import time

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# You will need the ABI to connect to the contract
# The file 'abi.json' has the ABI for the bored ape contract
# In general, you can get contract ABIs from etherscan
# https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('/home/codio/workspace/abi.json', 'r') as f:
# with open(r'H:\My Drive\Programs\python\mcit\eas583\abi.json', 'r') as f:
	abi = json.load(f)

############################
# Connect to an Ethereum node
api_url = 'https://mainnet.infura.io/v3/a5abf3836c914bf9a102f468b8475100'  # YOU WILL NEED TO TO PROVIDE THE URL OF AN ETHEREUM NODE
provider = HTTPProvider(api_url)
web3 = Web3(provider)
contract = web3.eth.contract(address=contract_address, abi=abi)


def get_ape_info(apeID):
	assert isinstance(apeID, int), f"{apeID} is not an int"
	assert 1 <= apeID, f"{apeID} must be at least 1"

	token_uri = contract.functions.tokenURI(apeID).call()
	token_uri = f"https://gateway.pinata.cloud/ipfs/{token_uri.split('//')[1]}"
	response = requests.get(token_uri)
	metadata = response.json()
	image_url = metadata.get("image")
	attributes = metadata.get("attributes", [])
	eyes_trait = next((item for item in attributes if item["trait_type"] == "Eyes"), None)

	data = {'owner': contract.functions.ownerOf(apeID).call(),
			'image': image_url,
			'eyes': eyes_trait['value']}

	assert isinstance(data, dict), f'get_ape_info{apeID} should return a dict'
	assert all([a in data.keys() for a in
				['owner', 'image', 'eyes']]), f"return value should include the keys 'owner','image' and 'eyes'"

	return data
