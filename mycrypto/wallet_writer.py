import csv


class WalletWriter:
    def __init__(self, csv_path):
        self._csv_path = csv_path
        self._fields = ['Name', 'Blockchain', 'Address', 'Private Key', 'Scan Url']
        self._wallets = []

    def add_wallet(self, wallet):
        self._wallets.append(wallet)

    def write(self):
        with open(self._csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self._fields)

            for wallet in self._wallets:
                csv_writer.writerow(
                    [wallet.name, wallet.blockchain_metadata.type.name, wallet.address, wallet.private_key,
                     wallet.scan_url])
