from mycrypto.blockchain_metadata import get_blockchain_metadata
from eth_account import Account
import secrets
import urllib.parse


class Wallet:
    def __init__(self, name, blockchain_metadata, address, private_key):
        self._name = name
        self._blockchain_metadata = blockchain_metadata
        self._address = address
        self._private_key = private_key

    @classmethod
    def create(cls, name, blockchain_type):
        private_key, address = cls._create_address()
        blockchain_metadata = get_blockchain_metadata(blockchain_type)
        return Wallet(name=name, blockchain_metadata=blockchain_metadata, address=address, private_key=private_key)

    @classmethod
    def _create_address(cls):
        private_key = secrets.token_hex(32)
        address = Account.from_key(private_key).address
        return private_key, address

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def private_key(self):
        return self._private_key

    @property
    def scan_url(self):
        return urllib.parse.urljoin(self._blockchain_metadata.block_explorer_url, str(self._address))

    @property
    def blockchain_metadata(self):
        return self._blockchain_metadata
