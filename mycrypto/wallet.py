from mycrypto.blockchain_metadata import get_blockchain_metadata
from eth_account import Account
import secrets
import urllib.parse


def create_new_wallet():
    private_key = secrets.token_hex(32)
    return get_wallet_from_key(private_key)


def get_wallet_from_key(private_key):
    return Account.from_key(private_key)
