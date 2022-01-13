import csv
import urllib.parse
from mycrypto.blockchain_metadata import get_blockchain_metadata
from mycrypto.blockchain_metadata import BlockchainType
from web3 import Web3


class WalletWriter:
    def __init__(self, blockchain, csv_path):
        if isinstance(blockchain, str):
            blockchain = BlockchainType[blockchain]
        self._blockchain_metadata = get_blockchain_metadata(blockchain)
        self._csv_path = csv_path
        self._fields = ['Name', 'Blockchain', 'Address', 'Private Key', 'Scan Url']
        self._wallets = []

    def add_wallet(self, name, wallet):
        self._wallets.append((name, wallet))

    def write(self):
        with open(self._csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self._fields)

            for name, wallet in self._wallets:
                scan_url = urllib.parse.urljoin(self._blockchain_metadata.block_explorer_url,
                                                'address/' + wallet.address)
                csv_writer.writerow(
                    [name, self._blockchain_metadata.type.name, wallet.address, Web3.toHex(wallet.privateKey),
                     scan_url])
