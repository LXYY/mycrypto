from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.middleware import local_filter_middleware

import functools

WSS_PROVIDER_URL = 'wss://blue-weathered-dust.fantom.quiknode.pro/237f50101eac2e6ebfc59da36ffaa02e28973e0d/'

@functools.lru_cache(maxsize=None)
def get_web3_client(wss_provider_url=WSS_PROVIDER_URL):
    web3_client = Web3(Web3.WebsocketProvider(wss_provider_url))
    web3_client.middleware_onion.inject(geth_poa_middleware, layer=0)
    web3_client.middleware_onion.add(local_filter_middleware)

    return web3_client


def get_gas_fee(gas_to_use):
    return Web3.fromWei(gas_to_use * get_web3_client().eth.gas_price, 'ether')
