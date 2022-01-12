from enum import Enum

class Currencies:
    BCOIN = 'BCOIN'
    CAKE = 'CAKE'

class CurrencyMetadata:
    def __init__(self, type, name, contract):
        self.type = type
        self.name = name
        self.contract = contract

_CURRENCY_METADATA = {
    Currencies.BCOIN: CurrencyMetadata(Currencies.BCOIN, 'BCOIN', '0x00e1656e45f18ec6747F5a8496Fd39B50b38396D'),
    Currencies.CAKE: CurrencyMetadata(Currencies.CAKE, 'CAKE', '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'),
}

def get_currency_metadata(currency):
    return _CURRENCY_METADATA.get(currency)
