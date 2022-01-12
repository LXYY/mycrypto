from mycrypto.blockchain_metadata import get_blockchain_metadata
from eth_account import Account
import secrets
import urllib.parse

class Wallet:
    def __init__(self, name, blockchain_type):
        self._name = name,
        self._blockchain_metadata = get_blockchain_metadata(blockchain_type)
        self._create_address()

    def _create_address(self):
        self._private_key = secrets.token_hex(32)
        self._address = Account.from_key(self._private_key).address

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
