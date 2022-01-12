import click
import os
import secrets
import time
from decimal import Decimal

from mycrypto.wallet_reader import WalletReader
from mycrypto.wallet_writer import WalletWriter
from mycrypto.wallet import create_new_wallet
from mycrypto.currencies import get_currency_metadata
from mycrypto.blockchain_metadata import get_blockchain_metadata
from mycrypto import token_utils


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
                         master_token_reserve):
    num_transactions = 0

    def _deposit_to_child(child_wallet_state, per_child_main, per_child_token, num_transactions):
        def _print_status(child_name, currency, amount, txn_url):
            print('master (%s) ---%f %s---> %s (%s): %s' % (
                master_wallet_state.address, amount, currency, child_name, child_wallet_state.address, txn_url))

        child_wallet_state.main = blockchain_metadata.currency
        child_wallet_state.token = token_name

        txn_url = (blockchain_metadata.get_transaction_url(
            token_utils.transfer_main_token(master_wallet_state.get_account_from_key(), child_wallet_state.address,
                                            per_child_main, nonce_delta=num_transactions))
                   if not dry_run else blockchain_metadata.get_transaction_url(secrets.token_hex(32)))
        print('nonce delta: %d' % num_transactions)
        _print_status(child_wallet_state.name, blockchain_metadata.currency, per_child_main, txn_url)
        child_wallet_state.main_deposit_transaction = str(txn_url)

        txn_url = (blockchain_metadata.get_transaction_url(
            token_utils.transfer_erc20_token(token_metadata.contract, master_wallet_state.get_account_from_key(),
                                             child_wallet_state.address,
                                             per_child_token, nonce_delta=num_transactions + 1)
        ) if not dry_run else blockchain_metadata.get_transaction_url(secrets.token_hex(32)))
        print('nonce delta: %d' % (num_transactions + 1))
        _print_status(child_wallet_state.name, token_metadata.name, per_child_token, txn_url)
        child_wallet_state.token_deposit_transaction = str(txn_url)

    def _start_transactions():
        print('Start splitting master wallet funds...')

        num_transactions = 0

        if run_test:
            child_wallet_state = wallet_state_store.get_test_wallet_state()
            _deposit_to_child(child_wallet_state, per_child_main, per_child_token, num_transactions)
            wallet_state_store.save()
            return

        for child_index in range(num_children_wallets):
            child_wallet_state = wallet_state_store.get_child_wallet_state(child_index)
            _deposit_to_child(child_wallet_state, per_child_main, per_child_token, num_transactions)
            num_transactions += 2
            wallet_state_store.save()
            if not dry_run:
                time.sleep(0.2)


    wallet_reader = WalletReader()
    wallet_state_store = wallet_reader.read_as_wallet_states_store(input_csv_path, output_csv_path)
    wallet_state_store.save()
    blockchain_metadata = get_blockchain_metadata(blockchain_name)
    token_metadata = get_currency_metadata(token_name)

    master_wallet_state = wallet_state_store.get_master_wallet_state()
    num_children_wallets = wallet_state_store.get_num_children_wallets()
    master_main_balance = token_utils.get_main_token_balance(master_wallet_state.address)
    master_token_balance = token_utils.get_erc20_token_balance(token_metadata.contract, master_wallet_state.address)
    per_child_main = (master_main_balance - Decimal(master_gas_reserve)) / Decimal(num_children_wallets)
    per_child_token = (master_token_balance - Decimal(master_token_reserve)) / Decimal(num_children_wallets)

    run_test = False
    dry_run = True

    _start_transactions()
