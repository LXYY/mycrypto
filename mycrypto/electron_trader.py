import click
import logging
from decimal import Decimal
from dataclasses import dataclass

from mycrypto.uniswap_utils import get_amounts_in
from mycrypto.token_utils import get_erc20_token_balance
from mycrypto.token_utils import get_main_token_balance
from mycrypto.currencies import get_currency_metadata
from mycrypto.electron_trader_state_machine import ElectronTraderStateMachine
from mycrypto.electron_trader_state_machine import ElectronTraderState

LOG = logging.getLogger(__name__)


@dataclass
class ElectronTraderConfig:
    proto_price_gap: Decimal
    max_price_raise: Decimal
    max_slippage: Decimal
    poll_interval_ms: int
    min_ftm_reserve: Decimal
    ftm_refill_amount: Decimal
    elct_trade_batch: Decimal
    price_gap_increase_interval_sec: int
    price_gap_increase_amount: Decimal
    price_gap_decrease_amount: Decimal


class ElectronTrader:
    def __init__(self, wallet, proto_price_gap, max_price_raise, max_slippage, poll_interval_ms):
        self._wallet = wallet
        self._config = ElectronTraderConfig(proto_price_gap=Decimal(proto_price_gap),
                                            max_price_raise=Decimal(max_price_raise),
                                            max_slippage=Decimal(max_slippage),
                                            poll_interval_ms=poll_interval_ms,
                                            min_ftm_reserve=Decimal(1.0),
                                            ftm_refill_amount=Decimal(5),
                                            elct_trade_batch=Decimal(50),
                                            price_gap_increase_interval_sec=3600,
                                            price_gap_increase_amount=Decimal(0.01),
                                            price_gap_decrease_amount=Decimal(0.005))
        self._dai_metadata = get_currency_metadata('DAI', 'FANTOM')
        self._trader_state_machine = ElectronTraderStateMachine(self)

    def get_proto_price(self):
        return get_amounts_in(1, ['USDC', 'PROTO'], 'PROTOFI', 'FANTOM')

    def get_elct_price(self):
        return get_amounts_in(1, ['DAI', 'WFTM', 'ELCT'], 'SPOOKY_SWAP', 'FANTOM')

    def get_elct_price_after_buy(self, amount):
        return get_amounts_in(amount, ['DAI', 'WFTM', 'ELCT'], 'SPOOKY_SWAP', 'FANTOM') / amount

    def get_ftm_balance(self):
        return get_main_token_balance(self._wallet.address)

    def get_dai_balance(self):
        return get_erc20_token_balance(self._dai_metadata.contract, self._wallet.address)

    def get_wallet(self):
        return self._wallet

    def get_config(self):
        return self._config

    def run(self):
        click.echo('Electron Trader config: %s' % self._config)
        LOG.info('[Init] %s', self._config)
        click.echo('Running Electron trader...')
        curr_state = ElectronTraderState.CHECKING_BALANCE
        while (True):
            try:
                curr_state = self._trader_state_machine.process_and_transit(curr_state)
            except KeyboardInterrupt:
                raise
            except:
                print('Error occurred. Check the log for more details.')
                LOG.exception('Error happened when handling %s state.' % curr_state)
                curr_state = ElectronTraderState.CHECKING_BALANCE
