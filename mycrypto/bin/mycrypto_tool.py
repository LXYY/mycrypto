import click

from mycrypto.commands import run_create_wallets_cmd


@click.group()
def cli():
    pass


@cli.command('create_wallets', short_help='Create wallets.')
@click.option('--n', default=1, show_default=True, help='The number of wallets to create.')
@click.argument('blockchain')
@click.argument('csv_path')
@click.option('--base-wallet-name', default='wallet', help='The base name of the wallets.')
@click.option('--create-test/--no-create-test', default=False, help='Whether to create a test wallet.')
@click.option('--create-master/--no-create-master', default=False, help='Whether to create a master wallet.')
def create_wallets(n, blockchain, csv_path, base_wallet_name, create_test, create_master):
    """This command create wallets at specified BLOCKCHAIN, and writes the wallet data into the CSV_PATH."""
    return run_create_wallets_cmd(blockchain_name=blockchain, num_wallets=n, csv_path=csv_path,
                                  base_wallet_name=base_wallet_name, create_test=create_test,
                                  create_master=create_master)

if __name__ == '__main__':
    cli()
