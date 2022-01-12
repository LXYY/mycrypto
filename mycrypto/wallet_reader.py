import csv

from mycrypto.wallet_state import WalletState
from mycrypto.wallet_state import WALLET_STATE_FIELDS
from mycrypto.wallet_state import WalletStateStore

class WalletReader:
    def __init__(self):
        pass

    def read_as_wallet_states_store(self, input_csv_path, output_state_csv_path):
        with open(input_csv_path) as csv_file:
            reader = csv.reader(csv_file)
            rows = [row for  row in reader]
            headers = rows[0]
            rows = rows[1:]

        wallet_states_data = self._to_wallet_states(headers, rows)
        return WalletStateStore(wallet_states_data, output_state_csv_path)


    def _to_wallet_states(self, headers, rows):
        wallet_states = []
        for row in rows:
            state = WalletState()
            for col_name, col_value in zip(headers, row):
                field_name = WALLET_STATE_FIELDS[col_name]
                setattr(state, field_name, col_value)
            wallet_states.append(state)

        return wallet_states
