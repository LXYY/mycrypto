from enum import Enum
import time
import logging
from dataclasses import dataclass
from decimal import Decimal

from mycrypto.uniswap_utils import get_amounts_out
from mycrypto.uniswap_utils import get_amounts_in
from mycrypto.uniswap_utils import swap_exact_tokens_for_eth
from mycrypto.uniswap_utils import swap_tokens_for_exact_tokens
from mycrypto.uniswap_utils import swap_exact_tokens_for_tokens
from mycrypto.web3_utils import get_web3_client

LOG = logging.getLogger(__name__)


class ElectronTraderState(Enum):
    CHECKING_BALANCE = 'CHECKING_BALANCE'
    WAITING_FOR_FUNDS = 'WAIT_FOR_FUNDS'
    IDLE = 'IDLE'
    REFILLING_GAS = 'REFILLING_GAS'
    TRADING = 'TRADING'
    QUOTING = 'QUOTING'


class ElectronTraderStateMachine:
    @dataclass
    class Context:
        proto_price: Decimal = None
        elct_price: Decimal = None
        dai_balance: Decimal = None

    def __init__(self, trader):
        self._trader = trader
        self._trader_config = trader.get_config()
        self._state_handlers = {
            ElectronTraderState.CHECKING_BALANCE: self._handle_checking_balance_state,
            ElectronTraderState.WAITING_FOR_FUNDS: self._handle_waiting_for_funds_state,
            ElectronTraderState.IDLE: self._handle_idle_state,
            ElectronTraderState.REFILLING_GAS: self._handle_refilling_gas_state,
            ElectronTraderState.TRADING: self._handle_trading_state,
            ElectronTraderState.QUOTING: self._handle_quoting_state,
        }
        self._state_transitions = {
            ElectronTraderState.CHECKING_BALANCE: {ElectronTraderState.WAITING_FOR_FUNDS,
                                                   ElectronTraderState.REFILLING_GAS, ElectronTraderState.QUOTING},
            ElectronTraderState.WAITING_FOR_FUNDS: {ElectronTraderState.QUOTING},
            ElectronTraderState.REFILLING_GAS: {ElectronTraderState.WAITING_FOR_FUNDS, ElectronTraderState.QUOTING},
            ElectronTraderState.QUOTING: {ElectronTraderState.IDLE, ElectronTraderState.TRADING},
            ElectronTraderState.IDLE: {ElectronTraderState.CHECKING_BALANCE},
            ElectronTraderState.TRADING: {ElectronTraderState.IDLE},
        }
        self._context = ElectronTraderStateMachine.Context()
        self._previous_price_gap_adjustment_time = time.time()

    def process_and_transit(self, current_state):
        return self._state_handlers[current_state]()

    def set_context(self, **kwargs):
        self._context = ElectronTraderStateMachine.Context(**kwargs)

    def _should_increase_price_gap(self):
        time_since_last_update = Decimal(time.time() - self._previous_price_gap_adjustment_time)
        return time_since_last_update > self._trader_config.price_gap_increase_interval_sec

    def _increase_price_gap(self):
        old_price_gap = self._trader_config.proto_price_gap
        new_price_gap = self._trader_config.proto_price_gap + self._trader_config.price_gap_increase_amount
        print('No trade & gap change for at least %d seconds. Increasing proto price gap from %.3f -> %.3f' % (
            self._trader_config.price_gap_increase_interval_sec, old_price_gap, new_price_gap))
        LOG.info('[Price Gap Increase] %.3f -> %.3f', old_price_gap, new_price_gap)
        self._trader_config.proto_price_gap = new_price_gap
        self._previous_price_gap_adjustment_time = time.time()

    def _decrease_price_gap(self):
        old_price_gap = self._trader_config.proto_price_gap
        new_price_gap = self._trader_config.proto_price_gap - self._trader_config.price_gap_decrease_amount
        print('Just finished a trade. Decreasing proto price gap from %.3f -> %.3f' % (old_price_gap, new_price_gap))
        LOG.info('[Price Gap Decrease] %.3f -> %.3f', old_price_gap, new_price_gap)
        self._trader_config.proto_price_gap -= self._trader_config.price_gap_decrease_amount
        self._previous_price_gap_adjustment_time = time.time()

    def _get_dai_amount_for_elct(self, elct_amount):
        dai_amount = get_amounts_in(elct_amount, ['DAI', 'WFTM', 'ELCT'], 'SPOOKY_SWAP', 'FANTOM')
        return dai_amount, dai_amount / elct_amount

    def _get_elct_amount_for_dai(self, dai_amount):
        elct_amount = get_amounts_out(dai_amount, ['DAI', 'WFTM', 'ELCT'], 'SPOOKY_SWAP', 'FANTOM')
        return elct_amount, dai_amount / elct_amount

    def _buy_with_exact_elct(self, elct_amount, max_dai_amount):
        print('Buying %s $ELCT with maximum %s $DAI...' % (elct_amount, max_dai_amount))
        result = swap_tokens_for_exact_tokens(
            elct_amount, max_dai_amount, ['DAI', 'WFTM', 'ELCT'], self._trader.get_wallet(), 'SPOOKY_SWAP', 'FANTOM')
        print(result)
        LOG.info('[Trade] %s', result)

    def _buy_with_exact_dai(self, dai_amount, min_elct_amount):
        print('Buying minimum %s $ELCT with %s $DAI...' % (min_elct_amount, dai_amount))
        result = swap_exact_tokens_for_tokens(
            dai_amount, min_elct_amount, ['DAI', 'WFTM', 'ELCT'], self._trader.get_wallet(), 'SPOOKY_SWAP', 'FANTOM')
        print(result)
        LOG.info('[Trade] %s', result)

    # State handlers.

    def _handle_checking_balance_state(self):
        dai_balance = self._trader.get_dai_balance()
        if dai_balance == 0:
            return ElectronTraderState.WAITING_FOR_FUNDS

        ftm_balance = self._trader.get_ftm_balance()
        if ftm_balance < self._trader_config.min_ftm_reserve:
            self.set_context(dai_balance=dai_balance)
            return ElectronTraderState.REFILLING_GAS

        return ElectronTraderState.QUOTING

    def _handle_waiting_for_funds_state(self):
        print('Waiting for new DAI funds to be transferred in...')
        web3_client = get_web3_client()
        # The event filter for capturing new incoming DAI.
        dai_transfer_event_filter = web3_client.eth.filter({
            # Only check new blocks.
            'fromBlock': 'latest',
            # The contract of DAI token.
            'address': web3_client.toChecksumAddress('0x8d11ec38a3eb5e956b052f67da8bdc9bef8abf3e'),
            'topics': [
                # Transfer(address,address,uint256).
                '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
                # Match any.
                None,
                # Transfer to current wallet (padded with extra 00 on the left to make it have 32 bytes).
                '0x%s%s' % ('00' * 12, self._trader.get_wallet().address[2:]),
            ],
        })

        while True:
            for _ in dai_transfer_event_filter.get_new_entries():
                print('New DAI are transferred in.')
                LOG.info('[DAI Deposit] %f', self._trader.get_dai_balance())
                # Typically the DAI refill interval maybe long. Reset the price gap adjustment time in this case.
                self._previous_price_gap_adjustment_time = time.time()
                return ElectronTraderState.QUOTING

            time.sleep(3)

    def _handle_refilling_gas_state(self):
        dai_required = get_amounts_in(self._trader_config.ftm_refill_amount, ['DAI', 'WFTM'], 'SPOOKY_SWAP', 'FANTOM')
        dai_amount = min(dai_required, self._context.dai_balance)
        estimated_ftm_amount = get_amounts_out(dai_amount, ['DAI', 'WFTM'], 'SPOOKY_SWAP', 'FANTOM')
        print('Refilling gas fee...')
        print('Transferring %s DAI into FTM...' % dai_amount)
        # It's OK to have large variance when swapping for gas fees.
        result = swap_exact_tokens_for_eth(dai_amount, estimated_ftm_amount * Decimal(0.5), ['DAI', 'WFTM'],
                                           self._trader.get_wallet(), 'SPOOKY_SWAP', 'FANTOM')
        print(result)
        LOG.info('[Gas Refill] %s', result)

        if (dai_amount == self._context.dai_balance):
            return ElectronTraderState.WAITING_FOR_FUNDS

        return ElectronTraderState.QUOTING

    def _handle_idle_state(self):
        time.sleep(self._trader_config.poll_interval_ms / 1000.0)
        return ElectronTraderState.CHECKING_BALANCE

    def _handle_quoting_state(self):
        proto_price = self._trader.get_proto_price()
        elct_price = self._trader.get_elct_price()

        if self._should_increase_price_gap():
            self._increase_price_gap()

        target_elct_price = proto_price * (Decimal(1.0) + self._trader_config.proto_price_gap)

        if (elct_price > target_elct_price):
            return ElectronTraderState.IDLE

        print('[$PROTO price]: $%s, [$ELCT price]: $%s, [Target $ELCT Price]: $%s' % (
            proto_price, elct_price, target_elct_price))
        self.set_context(proto_price=proto_price, elct_price=elct_price)
        return ElectronTraderState.TRADING

    def _handle_trading_state(self):
        print('$ELCT price <= Target price, try trading.')

        elct_price = self._context.elct_price
        max_slippage = self._trader_config.max_slippage
        max_elct_price = elct_price * (Decimal(1.0) + self._trader_config.max_price_raise)

        elct_amount = Decimal(0)
        max_dai_amount = Decimal(0)
        elct_trade_batch = Decimal(self._trader_config.elct_trade_batch)
        dai_balance = self._trader.get_dai_balance()

        while True:
            elct_amount += elct_trade_batch
            curr_dai_amount, curr_elct_price = self._get_dai_amount_for_elct(elct_amount)

            if curr_elct_price > max_elct_price or curr_dai_amount > dai_balance:
                elct_amount -= elct_trade_batch
                break

            max_dai_amount = curr_dai_amount

        # case 1. When the DAI balance can buy >= 1 batches, buy together.
        if elct_amount:
            max_dai_amount = min(dai_balance, max_dai_amount * (Decimal(1.0) + max_slippage))
            self._buy_with_exact_elct(elct_amount, max_dai_amount)
            self._decrease_price_gap()
        # case 2. When the DAI balance are insufficient for buying 1 batch, use up all the DAI balance to buy ELCT.
        else:
            min_elct_amount, elct_price_if_all_sold = self._get_elct_amount_for_dai(dai_balance)
            if elct_price_if_all_sold <= max_elct_price:
                self._buy_with_exact_dai(dai_balance, min_elct_amount * (Decimal(1.0) - max_slippage))
                self._decrease_price_gap()
        return ElectronTraderState.IDLE
