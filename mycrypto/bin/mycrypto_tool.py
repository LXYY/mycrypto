import click

from mycrypto.commands import run_split_master_cmd
from mycrypto.commands import run_update_balance_cmd
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


@cli.command('split_master', short_help='Split master wallet evenly across children.')
@click.argument('input_csv_path')
@click.argument('output_csv_path', default='')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
@click.option('--token', default='CAKE', help='The currency token to split.')
@click.option('--master-gas-reserve', type=click.FLOAT,
              help='The amount of main currency to reserve in the master wallet for gas fee.')
@click.option('--master-token-reserve', type=click.FLOAT, default=0,
              help='The amount of splited token to reserve in the master wallet.')
@click.option('--continue-splitting/--no-continue-splitting', default=False,
              help='Whether to continue splitting from a previous state.')
def split_master(input_csv_path, output_csv_path, blockchain, token, master_gas_reserve, master_token_reserve,
                 continue_splitting):
    """Split funds evenly across individual children wallets.

    All of the wallet addresses are kept within INPUT_CSV_PATH, and all of the outputs wil be saved at OUTPUT_CSV_PATH.

    OUTPUT_CSV_PATH is unnecessary when --continue is set. In this case there will be an in-place update at the input
    state file.
    """
    return run_split_master_cmd(input_csv_path=input_csv_path, output_csv_path=output_csv_path,
                                blockchain_name=blockchain, token_name=token, master_gas_reserve=master_gas_reserve,
                                master_token_reserve=master_token_reserve, continue_splitting=continue_splitting)


@cli.command('update_balance', short_help='Check & update the balance of wallets.')
@click.argument('wallet_state_csv_path')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
@click.option('--token', default='CAKE', help='The staking token.')
@click.option('--rewards_token', help='The rewards token.')
def update_balance(wallet_state_csv_path, blockchain, token, rewards_token):
    return run_update_balance_cmd(wallet_state_csv_path=wallet_state_csv_path, blockchain=blockchain, token=token,
                                  rewards_token=rewards_token)


if __name__ == '__main__':
    cli()
