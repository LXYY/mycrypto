from enum import Enum


class DexType(Enum):
    SPOOKY_SWAP = 'SPOOKY_SWAP'
    PROTOFI = 'PROTOFI'


class DexMetadata:
    def __init__(self, type, router_contract, factory_contract):
        self._type = type
        self._router_contract = router_contract
        self._factory_contract = factory_contract

    @property
    def type(self):
        return self._type

    @property
    def router_contract(self):
        return self._router_contract

    @property
    def factory_contract(self):
        return self._factory_contract


_DEX_METADATA = {
    DexType.SPOOKY_SWAP: DexMetadata(type=DexType.SPOOKY_SWAP,
                                     router_contract='0xF491e7B69E4244ad4002BC14e878a34207E38c29',
                                     factory_contract='0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3'),
    DexType.PROTOFI: DexMetadata(type=DexType.PROTOFI, router_contract='0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235',
                                 factory_contract='0x39720E5Fe53BEEeb9De4759cb91d8E7d42c17b76'),
}

def get_dex_metadata(dex_type):
    if isinstance(dex_type, str):
        dex_type = DexType[dex_type]

    return _DEX_METADATA.get(dex_type)
