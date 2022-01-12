from mycrypto.web3_utils import get_web3_client
from web3.contract import Contract
from web3 import Web3
import functools

ERC20_ABI = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[],"name":"Unpause","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"isOwner","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"unpause","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]'

def transfer_main_token(from_wallet, to_wallet_address, amount, nonce_delta=0):
    web3_client = get_web3_client()
    txn = {
        'to': to_wallet_address,
        'chainId': Web3.toHex(56),
        'value': web3_client.toWei(amount, 'ether'),
        'nonce': web3_client.eth.get_transaction_count(from_wallet.address) + nonce_delta,
        'gasPrice': web3_client.eth.gas_price,
        'gas': 21000,
    }
    signed_txn = web3_client.eth.account.sign_transaction(txn, from_wallet.privateKey)
    txn_hash = web3_client.eth.send_raw_transaction(signed_txn.rawTransaction)
    return Web3.toHex(txn_hash)

def transfer_erc20_token(token_contract, from_wallet, to_wallet_address, amount, nonce_delta=0):
    wei_amount =  Web3.toWei(amount, 'ether')
    web3_client = get_web3_client()
    contract = get_token_contract(token_contract)
    txn = contract.functions.transfer(to_wallet_address, wei_amount).buildTransaction({
        'from': from_wallet.address,
        'nonce': web3_client.eth.get_transaction_count(from_wallet.address) + nonce_delta,
        'gasPrice': web3_client.eth.gas_price,
    })
    signed_txn = web3_client.eth.account.sign_transaction(txn, from_wallet.privateKey)
    txn_hash = web3_client.eth.send_raw_transaction(signed_txn.rawTransaction)
    return Web3.toHex(txn_hash)

def get_main_token_balance(address):
    return Web3.fromWei(get_web3_client().eth.get_balance(address), 'ether')

def get_erc20_token_balance(token_contract, address):
    return Web3.fromWei(get_token_contract(token_contract).functions.balanceOf(address).call(),  'ether')

@functools.lru_cache(maxsize=None)
def get_token_contract(token_contract):
    return get_web3_client().eth.contract(address=Web3.toChecksumAddress(token_contract), abi=ERC20_ABI)
