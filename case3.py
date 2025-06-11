import requests
from collections import Counter

ETHERSCAN_API_KEY = "too lazy to put in env"
# first 3 addresses found on the list of point 1 (AND safe-deployments), other are only from safe-deployments
TARGET_ADDRESSES = [
    "0x40a2accbd92bca938b02010e17a5b8929b49130d",
    "0x9641d764fc13c8b624c04430c7356c1c7c8102e2",
    "0xa238cbeb142c10ef7ad8442c6d1f9e89e07e7761",
    "0x8d29be29923b68abfdd21e541b9374737b49cdad",
    "0x998739bfdaadde7c933b942a68053933098f9eda",
    "0xa1dabef33b3b82c7814b6d82a79e50f4ac44102b",
    "0x38869bf66a61cf6bdb996a6ae40d5853fd43b526"
]
METHOD_ID = "0x8d80ff0a"

def get_transactions(address):
    url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 22460000,
        "endblock": 99999999,
        "apikey": ETHERSCAN_API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["result"]

def print_top_10(addresses):
    cont = Counter([addr.lower() for addr in addresses])
    top_10 = cont.most_common(10)
    print("Top 10:\n")
    for i, (addr, count) in enumerate(top_10, 1):
        print(f"{i}. {addr} → {count}")

def main():
    non_safe_tx = 0
    addresses = []
    for address in TARGET_ADDRESSES:
        print(f"Checking address: {address}")
        txs = get_transactions(address)
        for tx in txs:
            if tx["to"] and tx["to"].lower() == address:
                if tx["input"].startswith(METHOD_ID):
                    data = tx["input"][138:]  # Removes the method ID, offset and length
                    while len(data) >= 170: # a new tx is at least 85 bytes
                        data_len = int(data[106:170], 16) * 2
                        addr = "0x" + data[202:242]
                        method = data[170:178]
                        if data_len == 0:
                            pass # this is a transfer, skip
                        elif method != "6a761202":
                            non_safe_tx += 1
                            # print(f"Non-safe transaction found: {tx['hash']} with method {method} and address {addr}")
                        else:
                            addresses.append(addr)
                        data = data[170 + data_len:]
    print_top_10(addresses)
    print(f"Total non-safe transactions: {non_safe_tx}")

if __name__ == "__main__":
    main()
