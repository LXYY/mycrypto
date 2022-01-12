from mycrypto.token_utils import transfer_main_token
from mycrypto.wallet import get_wallet_from_key

if __name__ == '__main__':
    from_wallet = get_wallet_from_key('***')
    to_wallet = '***'

    print('Transferring %f BNB from %s to %s...' % (0.01, from_wallet.address, to_wallet))
    txn_hash = transfer_main_token(from_wallet, to_wallet, 0.01)
    print('Transaction Hash: %s' % txn_hash)
