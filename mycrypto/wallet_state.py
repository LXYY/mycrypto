import csv

from collections import OrderedDict
from eth_account import Account

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
WALLET_STATE_FIELDS['Awards Token'] = 'awards_token'
WALLET_STATE_FIELDS['Awards Balance'] = 'awards_balance'
WALLET_STATE_FIELDS['Awards Withdraw Transaction'] = 'awards_withdraw_transaction'

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
        self.awards_token = ''
        self.awards_balance = ''
        self.awards_withdraw_transaction = ''

    def to_csv_row(self):
        return [getattr(self, field_name) for field_name in WALLET_STATE_FIELDS.values()]

    def get_account_from_key(self):
        return Account.from_key(self.private_key)



class WalletStateStore:
    def __init__(self, states_data, state_csv_path):
        self._states_data = states_data
        self._state_csv_path = state_csv_path
        self._states_by_name = {state.name: state for state in self._states_data}
        self._states_by_address = {state.address: state for state in self._states_data}

        self._num_children_wallets = len(self._states_data)
        if self.has_master_wallet():
            self._num_children_wallets -= 1
        if self.has_test_wallet():
            self._num_children_wallets -= 1

        self.save()

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

    def save(self):
        with open(self._state_csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(WALLET_STATE_FIELDS.keys())
            for state in self._states_data:
                csv_writer.writerow(state.to_csv_row())

class WalletStateReader:
    pass
