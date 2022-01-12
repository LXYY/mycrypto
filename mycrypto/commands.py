import click
import os

from mycrypto.blockchain_metadata import BlockchainType
from mycrypto.wallet_writer import WalletWriter
from mycrypto.wallet import Wallet

def run_create_wallets_cmd(blockchain_name, num_wallets, csv_path, base_wallet_name, create_test, create_master, ):
    blockchain_type = BlockchainType[blockchain_name]
    wallet_writer = WalletWriter(csv_path)
    if create_test:
        click.echo('Creating test wallet...')
        wallet_writer.add_wallet(Wallet.create('test', blockchain_type))
    if create_master:
        click.echo('Creating master wallet...')
        wallet_writer.add_wallet(Wallet.create('master', blockchain_type))

    click.echo('Creating %d wallets...' % num_wallets)
    for i in range(num_wallets):
        name = '%s_%d' % (base_wallet_name, i)
        wallet_writer.add_wallet(Wallet.create(name, blockchain_type))

    wallet_writer.write()
    click.echo('Wallets are created at: %s.' % os.path.abspath(csv_path))
