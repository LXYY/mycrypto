import click
import os
import secrets
from decimal import Decimal
from web3 import Web3

from mycrypto.wallet_reader import WalletReader
from mycrypto.wallet_state import WalletStateStore
from mycrypto.wallet_writer import WalletWriter
from mycrypto.web3_utils import get_web3_client
from mycrypto.web3_utils import get_gas_fee
from mycrypto.wallet import create_new_wallet
from mycrypto.wallet import get_wallet_from_key
from mycrypto.currencies import get_currency_metadata
from mycrypto.blockchain_metadata import get_blockchain_metadata
from mycrypto.electron_trader import ElectronTrader
from mycrypto.electron_staking_stats import ElectronStakingStats
from mycrypto import token_utils
from mycrypto import staking_utils


def run_create_wallets_cmd(blockchain_name, num_wallets, csv_path, base_wallet_name, create_test, create_master, ):
    wallet_writer = WalletWriter(blockchain_name, csv_path)
    if create_test:
        click.echo('Creating test wallet...')
        wallet_writer.add_wallet('test', create_new_wallet())
    if create_master:
        click.echo('Creating master wallet...')
        wallet_writer.add_wallet('master', create_new_wallet())

    click.echo('Creating %d wallets...' % num_wallets)
    for i in range(num_wallets):
        name = '%s_%d' % (base_wallet_name, i)
        wallet_writer.add_wallet(name, create_new_wallet())

    wallet_writer.write()
    click.echo('Wallets are created at: %s.' % os.path.abspath(csv_path))


def run_split_master_cmd(input_csv_path, output_csv_path, blockchain_name, token_name, master_gas_reserve,
                         master_token_reserve, continue_splitting):
    def _deposit_to_child(child_wallet_state, per_child_main, per_child_token):
        web3_client = get_web3_client()

        def _print_status(child_name, currency, amount, txn_url):
            print('master (%s) ---%f %s---> %s (%s): %s' % (
                master_wallet_state.address, amount, currency, child_name, child_wallet_state.address, txn_url))

        def _run_deposit_transaction(currency, amount, balance_attr, deposit_txn_attr, txn_runner):
            balance = getattr(child_wallet_state, balance_attr)
            if balance != '' and balance != '0':
                click.echo('Skip depositing %s for %s (%s) as the balance is non-zero.' % (
                    currency, child_wallet_state.name, child_wallet_state.address))
                return
            txn_hash = txn_runner() if not dry_run else secrets.token_hex(32)
            txn_url = blockchain_metadata.get_transaction_url(txn_hash)
            _print_status(child_wallet_state.name, currency, amount, txn_url)
            setattr(child_wallet_state, deposit_txn_attr, txn_url)

            if not dry_run:
                receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash)
                assert receipt['status'], 'Transaction %s got reverted.' % txn_url

        child_wallet_state.main = blockchain_metadata.currency
        child_wallet_state.token = token_name

        _run_deposit_transaction(currency=blockchain_metadata.currency, amount=per_child_main,
                                 balance_attr='main_balance', deposit_txn_attr='main_deposit_transaction',
                                 txn_runner=lambda: token_utils.transfer_main_token(
                                     master_wallet_state.get_account_from_key(), child_wallet_state.address,
                                     per_child_main))

        _run_deposit_transaction(currency=token_metadata.name, amount=per_child_token, balance_attr='token_balance',
                                 deposit_txn_attr='token_deposit_transaction',
                                 txn_runner=lambda: token_utils.transfer_erc20_token(
                                     token_metadata.contract,
                                     master_wallet_state.get_account_from_key(),
                                     child_wallet_state.address,
                                     per_child_token))

    def _start_transactions():
        print('Start splitting master wallet funds...')

        if run_test:
            child_wallet_state = wallet_state_store.get_test_wallet_state()
            _deposit_to_child(child_wallet_state, per_child_main, per_child_token)
            wallet_state_store.save()
            return

        for child_index in range(num_children_wallets):
            child_wallet_state = wallet_state_store.get_child_wallet_state(child_index)
            _deposit_to_child(child_wallet_state, per_child_main, per_child_token)
            wallet_state_store.save()

    wallet_reader = WalletReader()
    wallet_state_store = (WalletStateStore.restore_from_state_file(input_csv_path)
                          if continue_splitting else wallet_reader.read_as_wallet_states_store(input_csv_path,
                                                                                               output_csv_path))
    wallet_state_store.save()
    blockchain_metadata = get_blockchain_metadata(blockchain_name)
    token_metadata = get_currency_metadata(token_name, blockchain_name)

    master_wallet_state = wallet_state_store.get_master_wallet_state()
    num_children_wallets = wallet_state_store.get_num_children_wallets()
    master_main_balance = token_utils.get_main_token_balance(master_wallet_state.address)
    master_token_balance = token_utils.get_erc20_token_balance(token_metadata.contract, master_wallet_state.address)
    num_children_without_main_balance = sum(
        [Decimal(state.main_balance) == 0 for state in wallet_state_store.get_states_data()])
    num_children_without_token_balance = sum(
        [Decimal(state.token_balance) == 0 for state in wallet_state_store.get_states_data()])

    print(num_children_without_main_balance)
    print(num_children_without_token_balance)

    per_child_main = (master_main_balance - Decimal(master_gas_reserve)) / Decimal(num_children_without_main_balance)
    per_child_token = (master_token_balance - Decimal(master_token_reserve)) / Decimal(
        num_children_without_token_balance)

    run_test = False
    dry_run = False

    _start_transactions()

    wallet_state_store.finalize()


def run_update_balance_cmd(wallet_state_csv_path, blockchain, token, rewards_token):
    def _check_and_update_balance(wallet_state):
        wallet_state.main = blockchain_metadata.currency
        wallet_state.token = token_metadata.name
        wallet_state.rewards_token = rewards_token_metadata.name

        wallet_state.main_balance = token_utils.get_main_token_balance(wallet_state.address)
        wallet_state.token_balance = token_utils.get_erc20_token_balance(token_metadata.contract, wallet_state.address)
        wallet_state.rewards_balance = token_utils.get_erc20_token_balance(rewards_token_metadata.contract,
                                                                           wallet_state.address)

        balances = [
            (wallet_state.main, wallet_state.main_balance),
            (wallet_state.token, wallet_state.token_balance),
            (wallet_state.rewards_token, wallet_state.rewards_balance),
        ]

        balance_stats = ', '.join(['%s %s' % (balance, currency) for balance, currency in balances])
        click.echo('%s (%s) - %s' % (wallet_state.name, wallet_state.address, balance_stats))

        wallet_state_store.save()

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)
    token_metadata = get_currency_metadata(token, blockchain)
    rewards_token_metadata = get_currency_metadata(rewards_token, blockchain)

    click.echo('Checking & updating the wallet balances...')

    if wallet_state_store.has_master_wallet():
        _check_and_update_balance(wallet_state_store.get_master_wallet_state())

    if wallet_state_store.has_test_wallet():
        _check_and_update_balance(wallet_state_store.get_test_wallet_state())

    for idx in range(wallet_state_store.get_num_children_wallets()):
        _check_and_update_balance(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_approve_spending_cmd(wallet_state_csv_path, spender_contract, blockchain, token):
    def _approve_spending(wallet_state):

        web3_client = get_web3_client()
        txn_hash = token_utils.approve_token_spending(token_metadata.contract, wallet_state.get_account_from_key(),
                                                      spender_contract)
        txn_url = blockchain_metadata.get_transaction_url(txn_hash)

        click.echo('Approving for: %s (%s): %s' % (wallet_state.name, wallet_state.address, txn_url))
        receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash)
        assert receipt['status'], 'Transaction %s got reverted.' % txn_url
        wallet_state.syrup_approve_transaction = txn_url
        wallet_state_store.save()

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)
    token_metadata = get_currency_metadata(token, blockchain)

    click.echo('Approving %s spending for contract: %s ...' % (token_metadata.name, spender_contract))

    run_test = False

    if run_test and wallet_state_store.has_test_wallet():
        _approve_spending(wallet_state_store.get_test_wallet_state())
    else:
        for idx in range(wallet_state_store.get_num_children_wallets()):
            _approve_spending(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_stake_cmd(wallet_state_csv_path, syrup_pool_contract, blockchain, token):
    def _stake_max(wallet_state):
        if wallet_state.syrup_stake_transaction:
            click.echo('Skip staking for %s (%s) as a transaction exists.' % (wallet_state.name, wallet_state.address))
            return

        web3_client = get_web3_client()
        amount = token_utils.get_erc20_token_balance(token_metadata.contract, wallet_state.address)
        txn_hash = staking_utils.deposit(syrup_pool_contract, wallet_state.get_account_from_key(), amount)
        txn_url = blockchain_metadata.get_transaction_url(txn_hash)

        click.echo('Staking %s %s from %s (%s): %s ...' % (
            amount, token_metadata.name, wallet_state.name, wallet_state.address, txn_url))
        receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash, timeout=240, poll_latency=0.3)
        assert receipt['status'], 'Transaction %s got reverted.' % txn_url
        wallet_state.syrup_stake_transaction = txn_url
        wallet_state_store.save()

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)
    token_metadata = get_currency_metadata(token, blockchain)

    click.echo('Staking into the Syrup Pool (contract: %s)...' % syrup_pool_contract)

    run_test = False

    if run_test and wallet_state_store.has_test_wallet():
        _stake_max(wallet_state_store.get_test_wallet_state())
    else:
        for idx in range(wallet_state_store.get_num_children_wallets()):
            _stake_max(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_unstake_cmd(wallet_state_csv_path, syrup_pool_contract, blockchain):
    def _unstake(wallet_state):
        if wallet_state.syrup_unstake_transaction:
            click.echo(
                'Skip unstaking for %s (%s) as a transaction exists.' % (wallet_state.name, wallet_state.address))
            return

        web3_client = get_web3_client()
        staking_balance = Web3.fromWei(staking_utils.get_user_info(syrup_pool_contract, wallet_state.address)[0],
                                       'ether')
        txn_hash = staking_utils.withdraw(syrup_pool_contract, wallet_state.get_account_from_key(), staking_balance)
        txn_url = blockchain_metadata.get_transaction_url(txn_hash)

        click.echo('Unstaking all %s tokens into %s (%s): %s ...' % (
            staking_balance, wallet_state.name, wallet_state.address, txn_url))
        receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash, timeout=240, poll_latency=0.3)
        assert receipt['status'], 'Transaction %s got reverted.' % txn_url
        wallet_state.syrup_unstake_transaction = txn_url
        wallet_state_store.save()

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)

    click.echo('Unstaking all deposits from the Syrup Pool (contract: %s)...' % syrup_pool_contract)

    run_test = False

    if run_test and wallet_state_store.has_test_wallet():
        _unstake(wallet_state_store.get_test_wallet_state())
    else:
        for idx in range(wallet_state_store.get_num_children_wallets()):
            _unstake(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_merge_to_master_cmd(wallet_state_csv_path, blockchain, token, rewards_token):
    def _transfer_token_to_master(wallet_state, metadata, withdraw_txn_attr_name):
        if getattr(wallet_state, withdraw_txn_attr_name):
            click.echo(
                'Skip transferring %s from %s (%s) to master as a transaction exists.' % (
                    metadata.name, wallet_state.name, wallet_state.address))
            return

        web3_client = get_web3_client()
        balance = token_utils.get_erc20_token_balance(metadata.contract, wallet_state.address)
        txn_hash = token_utils.transfer_erc20_token(metadata.contract, wallet_state.get_account_from_key(),
                                                    master_address, balance)
        txn_url = blockchain_metadata.get_transaction_url(txn_hash)
        click.echo('Transferring all %s %s into %s (%s): %s ...' % (
            balance, metadata.name, wallet_state.name, wallet_state.address, txn_url))
        receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash, timeout=240, poll_latency=0.3)
        assert receipt['status'], 'Transaction %s got reverted.' % txn_url
        setattr(wallet_state, withdraw_txn_attr_name, txn_url)
        wallet_state_store.save()

    def _transfer_to_master(wallet_state):
        _transfer_token_to_master(wallet_state, token_metadata, 'token_withdraw_transaction')
        _transfer_token_to_master(wallet_state, rewards_token_metadata, 'rewards_withdraw_transaction')

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)
    token_metadata = get_currency_metadata(token, blockchain)
    rewards_token_metadata = get_currency_metadata(rewards_token, blockchain)
    master_address = wallet_state_store.get_master_wallet_state().address

    click.echo('Merging funds from child wallets into the master wallet (%s)...' % master_address)

    run_test = False

    if run_test and wallet_state_store.has_test_wallet():
        _transfer_to_master(wallet_state_store.get_test_wallet_state())
    else:
        for idx in range(wallet_state_store.get_num_children_wallets()):
            _transfer_to_master(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_merge_main_currency_to_master(wallet_state_csv_path, blockchain):
    def _transfer_main_currency_to_master(wallet_state):
        if wallet_state.main_withdraw_transaction:
            click.echo(
                'Skip transferring %s from %s (%s) to master as a transaction exists.' % (
                    blockchain_metadata.currency, wallet_state.name, wallet_state.address))
            return

        web3_client = get_web3_client()
        balance = token_utils.get_main_token_balance(wallet_state.address)
        gas_fee = get_gas_fee(21000)
        txn_hash = token_utils.transfer_main_token(wallet_state.get_account_from_key(), master_address,
                                                   balance - gas_fee)
        txn_url = blockchain_metadata.get_transaction_url(txn_hash)
        click.echo('Transferring all %s %s (gas fee: %s %s) into master from %s (%s): %s ...' % (
            balance - gas_fee, blockchain_metadata.currency, gas_fee, blockchain_metadata.currency, wallet_state.name,
            wallet_state.address, txn_url))
        receipt = web3_client.eth.wait_for_transaction_receipt(txn_hash, timeout=240, poll_latency=0.3)
        assert receipt['status'], 'Transaction %s got reverted.' % txn_url
        wallet_state.main_withdraw_transaction = txn_url
        wallet_state_store.save()

    wallet_state_store = WalletStateStore.restore_from_state_file(wallet_state_csv_path)
    blockchain_metadata = get_blockchain_metadata(blockchain)
    master_address = wallet_state_store.get_master_wallet_state().address

    click.echo('Merging %s from child wallets into the master wallet (%s)...' % (
        blockchain_metadata.currency, master_address))

    run_test = False

    if run_test and wallet_state_store.has_test_wallet():
        _transfer_main_currency_to_master(wallet_state_store.get_test_wallet_state())
    else:
        for idx in range(wallet_state_store.get_num_children_wallets()):
            _transfer_main_currency_to_master(wallet_state_store.get_child_wallet_state(idx))

    wallet_state_store.finalize()


def run_auto_trade_elct_cmd(key_file_path, proto_price_gap, max_price_raise, max_slippage, poll_interval_ms,
                            price_gap_increase_interval_sec):
    wallet = get_wallet_from_key(open(key_file_path).read().strip())
    electron_trader = ElectronTrader(wallet=wallet, proto_price_gap=proto_price_gap, max_price_raise=max_price_raise,
                                     max_slippage=max_slippage, poll_interval_ms=poll_interval_ms,
                                     price_gap_increase_interval_sec=price_gap_increase_interval_sec)
    electron_trader.run()


def run_summarize_elct_staking_stats_cmd(output_csv_path):
    stats = ElectronStakingStats()
    print('Summarizing ELCT staking stats...')
    stats.summarize()
    stats.export(output_csv_path)
    print('The full ELCT staking stats has been exported to: %s' % output_csv_path)
