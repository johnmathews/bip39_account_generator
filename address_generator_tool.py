import argparse
import json
import sqlite3
from datetime import datetime

import pytz
from mnemonic import Mnemonic

"""
17 Feb 2020, John Mathews
Built for Cardano

Mnemonic: https://github.com/trezor/python-mnemonic
Cardano API: https://input-output-hk.github.io/cardano-wallet/api/edge/#operation/postWallet

[x] Generate a json file that can be used by that cardano API
[ ] Track created addresses in a SQLite db. If a db doesn't exist, create it.

Inputs:
- account_name: choose a name for the new account (on chain)
- file_name: the file containing the json payload for the cardano API
- db_location: location of the sqlite db used to track generated accounts [*]
"""

PASSPHRASE = 'a very secure passphrase'
ADDRESS_POOL_GAP = 20
STRENGTH = 256

now = datetime.now(pytz.timezone("Europe/Amsterdam"))
now = now.strftime('%Y-%m-%d %H:%M:%S')

parser = argparse.ArgumentParser()
parser.add_argument(
    "--account",
    help="choose a name for your new account",
    type=str
)
parser.add_argument(
    "--file",
    help="the name of the json file containing the bip39 compliant account",
    type=str
)
parser.add_argument(
    "--db",
    help="the location of the sqlite database used to track generated accounts",
    type=str
)

args = parser.parse_args()
print(f"database name: {args.db = }")
print(f'account name: "{args.account}"')

# 1. GENERATE BIP39 address
mnemo = Mnemonic("english")
words = mnemo.generate(strength=STRENGTH)
print('bip39 mnemonic created')

# 2. CREATE JSON FILE FOR CARDANO WALLET API
file_content = {}
file_content['name'] = args.account
file_content['mnemonic_sentence'] = [word for word in words.split(' ')]
file_content['passphrase'] = PASSPHRASE
file_content['address_pool_gap'] = ADDRESS_POOL_GAP

with open(args.file, 'w') as fp:
    json.dump(file_content, fp)
    print(f'credentials written to file "{args.file}"')

# 3. ADD ACCOUNT TO DATABASE
conn = sqlite3.connect(args.db)  # will create the database if it doesn't exist
c = conn.cursor()

# check if the ADA_ACCOUNTS table already exists
c.execute("""SELECT count(name) FROM sqlite_master WHERE type='table' AND name='accounts'""")
table_exists = c.fetchone()[0]
if table_exists == 0:
    # create the ADA_ACCOUNT table if it does not exist
    c.execute('''
      CREATE TABLE accounts(created text, name text, mnemonic text, passphrase text, address_pool_gap integer)
    ''')


# write the new account to the db
c.execute(f"""
    INSERT INTO accounts VALUES('{now}', '{args.account}', '{words}', '{PASSPHRASE}', '{ADDRESS_POOL_GAP}')
""")


conn.commit()
conn.close()
print(f'credentials written to database "{args.db}"')
print('complete')
