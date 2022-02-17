from dataclasses import dataclass
from decimal import Decimal
from mycrypto.covalent_client import CovalentClient
from mycrypto.web3_utils import get_web3_client
from web3 import Web3
import csv


class ElectronStakingStats:
    @dataclass
    class StakingStats:
        address: str
        deposit: Decimal
        withdraw: Decimal

    def __init__(self):
        self._dai_fission_pool = {
            'contract': '0x180b3622bcc123e900e5eb603066755418d0b4f5',
            'created_at': 28808405,
        }
        self._ftm_fission_pool = {
            'contract': '0x2b3cf543e80915f56e01797e383853d6d61fd235',
            'created_at': 30490103,
        }
        self._deposit_topic = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
        self._withdraw_topic = '0x884edad9ce6fa2440d8a54cc123490eb96d2768479d49ff9c7366125a9424364'
        self._address_to_staking_stats = {}
        self._covalent_client = CovalentClient()
        self._stats_csv_headers = ['Address', 'Staked ELCT', 'Staking Share', 'Total Deposit', 'Total Withdraw']

    def summarize(self):
        latest_block = get_web3_client().eth.get_block('latest').number

        print('Summarizing DAI fission pool...')
        self._summarize_fission_pool(contract=self._dai_fission_pool['contract'],
                                     from_block=self._dai_fission_pool['created_at'],
                                     to_block=latest_block)
        print('Summarizing FTM fission pool...')
        self._summarize_fission_pool(contract=self._ftm_fission_pool['contract'],
                                     from_block=self._ftm_fission_pool['created_at'],
                                     to_block=latest_block)

    def export(self, output_csv_path):
        stats_rows = self._get_stats_rows()
        with open(output_csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self._stats_csv_headers)
            for row in stats_rows:
                csv_writer.writerow(row)

    def _get_stats_rows(self):
        stats_list = list(self._address_to_staking_stats.values())
        stats_list.sort(key=lambda stats: stats.deposit - stats.withdraw, reverse=True)
        total_staked = sum((stats.deposit - stats.withdraw for stats in stats_list))

        for stats in stats_list:
            staked = stats.deposit - stats.withdraw
            staked_share = staked / total_staked
            yield (stats.address, float(staked), float(staked_share), float(stats.deposit), float(stats.withdraw))

    def _summarize_by_event(self, contract, event_topic, from_block, to_block):
        for event in self._covalent_client.retrieve_log_events_by_topic(topic=event_topic, address=contract,
                                                                        from_block=from_block, to_block=to_block):
            decoded_event_params = event['decoded']['params']
            wallet_address = decoded_event_params[0]['value']
            amount = Web3.fromWei(int(decoded_event_params[1]['value']), 'ether')

            if wallet_address not in self._address_to_staking_stats:
                self._address_to_staking_stats[wallet_address] = ElectronStakingStats.StakingStats(
                    address=wallet_address, deposit=Decimal(0), withdraw=Decimal(0))

            if event_topic == self._deposit_topic:
                self._address_to_staking_stats[wallet_address].deposit += amount
            else:
                self._address_to_staking_stats[wallet_address].withdraw += amount

    def _summarize_fission_pool(self, contract, from_block, to_block):
        print('Retrieving Deposit events...')
        self._summarize_by_event(contract, self._deposit_topic, from_block, to_block)
        print('Retrieving Withdraw events...')
        self._summarize_by_event(contract, self._withdraw_topic, from_block, to_block)
