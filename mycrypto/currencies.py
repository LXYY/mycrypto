from enum import Enum
from mycrypto.blockchain_metadata import BlockchainType


def decimal_to_wei_unit(decimal):
    decimal_unit = {
        0: 'wei',
        3: 'kwei',
        6: 'mwei',
        9: 'gwei',
        12: 'microether',
        15: 'milliether',
        18: 'ether',
    }
    return decimal_unit[decimal]


class Currencies(Enum):
    BCOIN = 'BCOIN'
    CAKE = 'CAKE'
    WFTM = 'WFTM'
    DAI = 'DAI'
    USDC = 'USDC'
    PROTO = 'PROTO'
    ELCT = 'ELCT'


class CurrencyMetadata:
    def __init__(self, type, name, contract, decimal=18):
        self.type = type
        self.name = name
        self.contract = contract
        self.decimal = decimal
        self.wei_unit = decimal_to_wei_unit(decimal)


_CURRENCY_METADATA = {
    (Currencies.BCOIN, BlockchainType.BSC): CurrencyMetadata(Currencies.BCOIN, 'BCOIN',
                                                             '0x00e1656e45f18ec6747F5a8496Fd39B50b38396D'),
    (Currencies.CAKE, BlockchainType.BSC): CurrencyMetadata(Currencies.CAKE, 'CAKE',
                                                            '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'),
    (Currencies.WFTM, BlockchainType.FANTOM): CurrencyMetadata(Currencies.WFTM, 'WFTM',
                                                               '0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83'),
    (Currencies.DAI, BlockchainType.FANTOM): CurrencyMetadata(Currencies.DAI, 'DAI',
                                                              '0x8d11ec38a3eb5e956b052f67da8bdc9bef8abf3e'),
    (Currencies.USDC, BlockchainType.FANTOM): CurrencyMetadata(Currencies.USDC, 'USDC',
                                                               '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 6),
    (Currencies.PROTO, BlockchainType.FANTOM): CurrencyMetadata(Currencies.PROTO, 'PROTO',
                                                                '0xa23c4e69e5eaf4500f2f9301717f12b578b948fb'),
    (Currencies.ELCT, BlockchainType.FANTOM): CurrencyMetadata(Currencies.ELCT, 'ELCT',
                                                               '0x622265EaB66A45FA05bAc9B8d2262AA548FA449E'),
}


def get_currency_metadata(currency, blockchain):
    if isinstance(currency, str):
        currency = Currencies[currency]

    if isinstance(blockchain, str):
        blockchain = BlockchainType[blockchain]

    return _CURRENCY_METADATA.get((currency, blockchain))

