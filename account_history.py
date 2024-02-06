# %%
import time
from functools import partial

import chifralib
import pandas as pd
from ape import chain, networks
# from ape.contracts.base import ContractLog, LogFilter
from ape.api.query import extract_fields, validate_and_expand_columns, ReceiptAPI
from ape.managers.chain import AccountHistory
from ape.api.query import AccountTransactionQuery
from ape.types import AddressType
from dotenv import load_dotenv


load_dotenv()

for d in dir(chifralib):
    print(d)

 # %%
import importlib.util

if importlib.util.find_spec("chifra") is not None:
    print("Module 'chifra' is installed.")
else:
    print("Module 'chifra' is not installed.")

# %%
connection = "local node through ape"
context = networks.parse_network_choice('ethereum:local:http://localhost:8545')
context.__enter__();

# %%
# query chain
start_time = time.time()
chain.history["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"].query("value").sum()  # All value sent by this address
print(f"query finished in {time.time() - start_time} seconds")

# %%
# query AccountHistory
start_time = time.time()
# chain.history["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"].query("value").sum()  # All value sent by this address
account_history:AccountHistory = chain.history._get_account_history("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
query_results = account_history.query("value")
print(f"query finished in {time.time() - start_time} seconds")

# %%
# break down query
start_time = time.time()
provider = context.provider
columns = list(ReceiptAPI.model_fields)
columns = ["value"]
address = AddressType("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
start_nonce = 0
stop_nonce = provider.get_nonce(address)
engine_to_use = None
query = AccountTransactionQuery(
    columns=columns,
    account=address,
    start_nonce=start_nonce,
    stop_nonce=stop_nonce,
)
engines = chain.query_manager.engines
best_time = 2**32
engine_to_use = None
for engine in engines:
    est_time = engines[engine].estimate_query(query)
    print(f"{engine} estimate is {est_time} seconds")
    if est_time is not None and est_time < best_time:
        best_time = est_time
        engine_to_use = engine
print(f"{connection} chose {engine_to_use} with an estimate of {best_time} seconds")

# %%
txns = chain.query_manager.query(query, engine_to_use=engine_to_use)
columns = validate_and_expand_columns(columns, ReceiptAPI)  # type: ignore
extraction = partial(extract_fields, columns=columns)
data = map(lambda tx: extraction(tx), txns)
result_df = pd.DataFrame(columns=columns, data=data)

# %%

# %%`