import requests
import json


def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

    headers = {
        "pinata_api_key": "1cf0ddaa6334a659d968",
        "pinata_secret_api_key": '5c0504e39761b95851dcf1bdf2361d69c9f9c01d4a682f3ea986f02403d77b85',
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Error pinning data: {response.text}")

    cid = response.json()['IpfsHash']

    return cid


def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), "get_from_ipfs accepts a cid in the form of a string"

    url = f"https://gateway.pinata.cloud/ipfs/{cid}"
    response = requests.get(url)

    if response.status_code == 200:
        if content_type == 'json':
            data = response.json()
        else:
            data = response.text

    else:
        raise Exception("Error downloading JSON data")

    assert isinstance(data, dict), "get_from_ipfs should return a dict"

    return data


if __name__ == '__main__':
    data = {'test': 'success'}
    cid = pin_to_ipfs(data)
    retrieved_data = get_from_ipfs(cid)
    assert data == retrieved_data
