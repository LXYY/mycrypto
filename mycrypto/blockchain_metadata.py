from enum import Enum

class BlockchainType(Enum):
    ETH = 'ETH'
    BSC = 'BSC'
    POLYGON = 'POLYGON'

class BlockchainMetadata:
    def __init__(self, type, rpc_url, id, currency, block_explorer_url):
        self._type = type
        self._rpc_url = rpc_url
        self._id = id
        self._currency = currency
        self._block_explorer_url = block_explorer_url

    @property
    def type(self):
        return self._type

    @property
    def rpc_url(self):
        return self._rpc_url

    @property
    def id(self):
        return self._id

    @property
    def currency(self):
        return self._currency

    @property
    def block_explorer_url(self):
        return self._block_explorer_url


_BLOCKCHAIN_METADATA = {
    BlockchainType.ETH: BlockchainMetadata(
        type=BlockchainType.ETH,
        rpc_url='https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
        id=1,
        currency='ETH',
        block_explorer_url='https://etherscan.io',
    ),
    BlockchainType.BSC: BlockchainMetadata(
        type=BlockchainType.BSC,
        rpc_url='https://bsc-dataseed.binance.org/',
        id=56,
        currency='BNB',
        block_explorer_url='https://bscscan.com',
    ),
    BlockchainType.POLYGON: BlockchainMetadata(
        type=BlockchainType.POLYGON,
        rpc_url='https://polygon-rpc.com',
        id=137,
        currency='MATIC',
        block_explorer_url='https://polygonscan.com',
    ),
}

def get_blockchain_metadata(blockchain_type):
    return _BLOCKCHAIN_METADATA.get(blockchain_type)
