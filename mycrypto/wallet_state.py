import csv

from collections import OrderedDict

import shutil
import os
import click
from eth_account import Account
import tempfile

# Initialize the wallet state fields within a ordered dict.
WALLET_STATE_FIELDS = OrderedDict()
WALLET_STATE_FIELDS['Name'] = 'name'
WALLET_STATE_FIELDS['Address'] = 'address'
WALLET_STATE_FIELDS['Private Key'] = 'private_key'
WALLET_STATE_FIELDS['Blockchain'] = 'blockchain'
WALLET_STATE_FIELDS['Scan Url'] = 'scan_url'
WALLET_STATE_FIELDS['Main'] = 'main'
WALLET_STATE_FIELDS['Token'] = 'token'
WALLET_STATE_FIELDS['Main Balance'] = 'main_balance'
WALLET_STATE_FIELDS['Token Balance'] = 'token_balance'
WALLET_STATE_FIELDS['Main Deposit Transaction'] = 'main_deposit_transaction'
WALLET_STATE_FIELDS['Token Deposit Transaction'] = 'token_deposit_transaction'
WALLET_STATE_FIELDS['Main Withdraw Transaction'] = 'main_withdraw_transaction'
WALLET_STATE_FIELDS['Token Withdraw Transaction'] = 'token_withdraw_transaction'
WALLET_STATE_FIELDS['Syrup Approve Transaction'] = 'syrup_approve_transaction'
WALLET_STATE_FIELDS['Syrup Stake Transaction'] = 'syrup_stake_transaction'
WALLET_STATE_FIELDS['Syrup Unstake Transaction'] = 'syrup_unstake_transaction'
WALLET_STATE_FIELDS['Rewards Token'] = 'rewards_token'
WALLET_STATE_FIELDS['Rewards Balance'] = 'rewards_balance'
WALLET_STATE_FIELDS['Rewards Withdraw Transaction'] = 'rewards_withdraw_transaction'

class WalletState:
    def __init__(self):
        self.name = ''
        self.address = ''
        self.private_key = ''
        self.blockchain = ''
        self.main = ''
        self.token = ''
        self.main_balance = ''
        self.token_balance = ''
        self.main_deposit_transaction = ''
        self.token_deposit_transaction = ''
        self.main_withdraw_transaction = ''
        self.token_withdraw_transaction = ''
        self.syrup_approve_transaction = ''
        self.syrup_stake_transaction = ''
        self.syrup_unstake_transaction = ''
        self.rewards_token = ''
        self.rewards_balance = ''
        self.rewards_withdraw_transaction = ''

    def to_csv_row(self):
        return [getattr(self, field_name) for field_name in WALLET_STATE_FIELDS.values()]

    @classmethod
    def from_state_row(cls, row):
        state = WalletState()
        for field_attr, field_value in zip(WALLET_STATE_FIELDS.values(), row):
            setattr(state, field_attr, field_value)
        return state

    def get_account_from_key(self):
        return Account.from_key(self.private_key)


class WalletStateStore:
    def __init__(self, states_data, state_csv_path, restored_from_file=False):
        self._states_data = states_data
        self._state_csv_path = state_csv_path
        self._states_by_name = {state.name: state for state in self._states_data}
        self._states_by_address = {state.address: state for state in self._states_data}
        self._restored_from_file = restored_from_file
        self._temp_state_csv_path = tempfile.mktemp()

        if self._restored_from_file:
            click.echo('Temp state file is located at: %s' % self._temp_state_csv_path)

        self._num_children_wallets = len(self._states_data)
        if self.has_master_wallet():
            self._num_children_wallets -= 1
        if self.has_test_wallet():
            self._num_children_wallets -= 1

        self.save()

    @classmethod
    def restore_from_state_file(cls, state_csv_path):
        with open(state_csv_path) as state_csv_file:
            csv_reader = csv.reader(state_csv_file)
            rows = [row for row in csv_reader]

        states_data = [WalletState.from_state_row(row) for row in rows[1:]]
        return WalletStateStore(states_data, state_csv_path, restored_from_file=True)

    def get_state_by_name(self, name):
        return self._states_by_name[name]

    def get_state_by_address(self, address):
        return self._states_by_address[address]

    def has_master_wallet(self):
        return 'master' in self._states_by_name

    def has_test_wallet(self):
        return 'test' in self._states_by_name

    def get_master_wallet_state(self):
        return self._states_by_name['master'] if self.has_master_wallet() else None

    def get_test_wallet_state(self):
        return self._states_by_name['test'] if self.has_test_wallet() else None

    def get_num_children_wallets(self):
        return self._num_children_wallets

    def get_child_wallet_state(self, index):
        start_index = len(self._states_data) - self._num_children_wallets
        return self._states_data[start_index + index]

    def get_states_data(self):
        return self._states_data

    def save(self):
        csv_path = self._temp_state_csv_path if self._restored_from_file else self._state_csv_path

        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(WALLET_STATE_FIELDS.keys())
            for state in self._states_data:
                csv_writer.writerow(state.to_csv_row())

    def finalize(self):
        if not self._restored_from_file:
            return

        print('temp file is %s' % self._temp_state_csv_path)
        print('state file is %s' % self._state_csv_path)

        shutil.copyfile(src=self._temp_state_csv_path, dst=self._state_csv_path)
        try:
            os.remove(self._temp_state_csv_path)
        except OSError:
            pass


class WalletStateReader:
    pass
