import click
import os

from mycrypto.wallet_writer import WalletWriter
from mycrypto.wallet import create_new_wallet

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
