import click
import logging
from mycrypto.commands import run_split_master_cmd
from mycrypto.commands import run_update_balance_cmd
from mycrypto.commands import run_create_wallets_cmd
from mycrypto.commands import run_approve_spending_cmd
from mycrypto.commands import run_stake_cmd
from mycrypto.commands import run_unstake_cmd
from mycrypto.commands import run_merge_to_master_cmd
from mycrypto.commands import run_merge_main_currency_to_master
from mycrypto.commands import run_auto_trade_elct_cmd
from mycrypto.commands import run_summarize_elct_staking_stats_cmd


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
@click.option('--rewards-token', help='The rewards token.')
def update_balance(wallet_state_csv_path, blockchain, token, rewards_token):
    return run_update_balance_cmd(wallet_state_csv_path=wallet_state_csv_path, blockchain=blockchain, token=token,
                                  rewards_token=rewards_token)


@cli.command('approve_spending', short_help='Approve contract to spend money for a currency.')
@click.argument('wallet_state_csv_path')
@click.option('--spender-contract')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
@click.option('--token', default='CAKE', help='The staking token.')
def approve_spending(wallet_state_csv_path, spender_contract, blockchain, token):
    return run_approve_spending_cmd(wallet_state_csv_path=wallet_state_csv_path, spender_contract=spender_contract,
                                    blockchain=blockchain, token=token)


@cli.command('stake', short_help='Stake into the syrup pool.')
@click.argument('wallet_state_csv_path')
@click.option('--syrup-pool-contract')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
@click.option('--token', default='CAKE', help='The staking token.')
def stake(wallet_state_csv_path, syrup_pool_contract, blockchain, token):
    return run_stake_cmd(wallet_state_csv_path=wallet_state_csv_path, syrup_pool_contract=syrup_pool_contract,
                         blockchain=blockchain, token=token)


@cli.command('unstake', short_help='Unstake the syrup pool.')
@click.argument('wallet_state_csv_path')
@click.option('--syrup-pool-contract')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
def unstake(wallet_state_csv_path, syrup_pool_contract, blockchain):
    return run_unstake_cmd(wallet_state_csv_path=wallet_state_csv_path, syrup_pool_contract=syrup_pool_contract,
                           blockchain=blockchain)


@cli.command('merge_to_master', short_help='Merge the funds into the master wallet.')
@click.argument('wallet_state_csv_path')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
@click.option('--token', default='CAKE', help='The staking token.')
@click.option('--rewards-token', help='The rewards token.')
def merge_to_master(wallet_state_csv_path, blockchain, token, rewards_token):
    """The merged funds doesn't include the main blockchain currency, as they need to be transferred in the end."""
    return run_merge_to_master_cmd(wallet_state_csv_path=wallet_state_csv_path, blockchain=blockchain, token=token,
                                   rewards_token=rewards_token)


@cli.command('merge_main_currency_to_master', short_help='Merge the main blockchain currency into the master wallet.')
@click.argument('wallet_state_csv_path')
@click.option('--blockchain', default='BSC', help='The blockchain name of the wallets.')
def merge_main_currency_to_master(wallet_state_csv_path, blockchain):
    """The merged funds doesn't include the main blockchain currency, as they need to be transferred in the end."""
    return run_merge_main_currency_to_master(wallet_state_csv_path=wallet_state_csv_path, blockchain=blockchain)


@cli.command('auto_trade_elct', short_help='An auto trader for monitor & trade ELCT from SpookySwap.')
@click.argument('key_file_path')
@click.option('--proto_price_gap', type=click.FLOAT, default=-0.15,
              help='The gap between ELCT and PROTO for triggering auto buy. E.g.: -0.1 will trigger auto-buy when the price of ELCT is at 90% of PROTO\'s.')
@click.option('--max_price_raise', type=click.FLOAT, default=0.04,
              help='The maximum allowed price raise rate caused by the purchase.')
@click.option('--max_slippage', type=click.FLOAT, default=0.02,
              help='Max allowed slippage rate on the non-exact token limit (+ for DAI, - for ELCT).')
@click.option('--poll_interval_ms', type=click.INT, default=500,
              help='The time interval (in ms) for polling ELCT price from SpookySwap.')
@click.option('--price_gap_increase_interval_sec', type=click.INT, default=7200,
              help='The time interval the price gap to increase when there are no transactions made for a while.')
@click.option('--log_file', help='The file path to keep the logs.')
def auto_trade_elct(key_file_path, proto_price_gap, max_price_raise, max_slippage, poll_interval_ms,
                    price_gap_increase_interval_sec, log_file):
    """Automatically monitor & buy ELCT with proper price (the ones are below or close to PROTO market price).

    KEY_FILE_PATH is the file for storing the private key of the wallet address.
    """
    logging.basicConfig(filename=log_file, filemode='a',
                        format='%(levelname)s %(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)
    return run_auto_trade_elct_cmd(key_file_path=key_file_path, proto_price_gap=proto_price_gap,
                                   max_price_raise=max_price_raise, max_slippage=max_slippage,
                                   poll_interval_ms=poll_interval_ms,
                                   price_gap_increase_interval_sec=price_gap_increase_interval_sec)


@cli.command('summarize_elct_staking_stats', short_help='Summarize the ELCT staking stats.')
@click.argument('output_csv_path')
def summarize_elct_staking_stats(output_csv_path):
    return run_summarize_elct_staking_stats_cmd(output_csv_path)


if __name__ == '__main__':
    cli()
