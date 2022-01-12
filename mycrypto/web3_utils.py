from web3 import Web3
from web3.middleware import geth_poa_middleware

import functools

WSS_PROVIDER_URL = 'wss://green-wandering-firefly.bsc.quiknode.pro/ae8a759c7645d5d55537ed9fe16ce4e95edb49fa/'

@functools.lru_cache(maxsize=None)
def get_web3_client():
    web3_client = Web3(Web3.WebsocketProvider(WSS_PROVIDER_URL))
    web3_client.middleware_onion.inject(geth_poa_middleware, layer=0)
    return web3_client
