import click

from uniswap_utils import get_amounts_in


class ElectronTrader:
    def __init__(self, wallet, proto_price_gap, max_stable_coin_slippage, poll_interval_ms):
        self._wallet = wallet
        self._proto_price_gap = proto_price_gap
        self._max_stable_coin_slippage = max_stable_coin_slippage
        self._poll_interval_ms = poll_interval_ms

    def get_proto_price(self):
        return get_amounts_in(1, ['USDC', 'PROTO'], 'PROTOFI', 'FANTOM')

    def get_elct_price(self):
        return get_amounts_in(1, ['DAI', 'WFTM', 'ELCT'], 'SPOOKY_SWAP', 'FANTOM')

    def run(self):
        click.echo('Running Electron trader...')
