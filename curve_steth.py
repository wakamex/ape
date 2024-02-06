# %%
import os
import time
from functools import partial
from typing import Iterator

import pandas as pd
from ape import chain, Contract, networks
# from ape.contracts.base import ContractLog, LogFilter
from ape.api.query import ContractEventQuery, extract_fields, validate_and_expand_columns
from ape.types import ContractLog, LogFilter
from dotenv import load_dotenv


load_dotenv()

def test_query(chain, blocks_back_list):
    if not isinstance(blocks_back_list, list):
        blocks_back_list = [blocks_back_list]
    for blocks_back in blocks_back_list:
        start_time = time.time()
        start_block = chain.blocks[-1].number - int(blocks_back)
        print(f"{start_block=}")
        events = curve_steth.TokenExchange.query("*", start_block=start_block)
        print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events)} events (events per second: {len(events)/(time.time()-start_time):.2f})")
# BLOCK_LOOKBACK = [3000, 86400*11/12, 86400*365/12]
# BLOCK_LOOKBACK = 50_000
BLOCK_LOOKBACK = 86400*365/12
print(f"{BLOCK_LOOKBACK=:,.0f}")

# %%
# connection = "random node through ape"
# context = networks.parse_network_choice('ethereum:mainnet')
# context.__enter__()
# curve_steth = Contract("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")
# test_query(chain, BLOCK_LOOKBACK)

# %%
connection = "infura through ape"
rpc_url = f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
context = networks.parse_network_choice(f"ethereum:mainnet:{rpc_url}")
context.__enter__()
curve_steth = Contract("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")
test_query(chain, BLOCK_LOOKBACK)

# %%
connection = "alchemy through ape"
context = networks.parse_network_choice('ethereum:mainnet:alchemy')
context.__enter__()
test_query(chain, BLOCK_LOOKBACK)

# %%
# connection = "local node through ape"
# context = networks.parse_network_choice('ethereum:local:http://localhost:8545')
# context.__enter__()
# curve_steth = Contract("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")
# test_query(chain, BLOCK_LOOKBACK)

# %%
# break down query
connection = "local node through ape"
start_time = time.time()
columns = list(ContractLog.model_fields)
abi = curve_steth.TokenExchange.abi
start_block = chain.chain_manager.blocks.height - BLOCK_LOOKBACK
stop_block = chain.chain_manager.blocks.height
contract_address = curve_steth.address
step = 1
query = {
    "columns": columns,
    "event": abi,
    "start_block": start_block,
    "stop_block": stop_block,
    "step": step,
    "contract": contract_address
}
engine_to_use = None
contract_event_query = ContractEventQuery(**query)
provider = curve_steth.provider
def perform_contract_events_query(provider, query: ContractEventQuery) -> Iterator[ContractLog]:
    addresses = query.contract
    if not isinstance(addresses, list):
        addresses = [query.contract]  # type: ignore

    log_filter = LogFilter.from_event(
        event=query.event,
        search_topics=query.search_topics,
        addresses=addresses,
        start_block=query.start_block,
        stop_block=query.stop_block,
    )
    return provider.get_contract_logs(log_filter)
# contract_events =  chain.query_manager.query(contract_event_query, engine_to_use=engine_to_use)
contract_events = perform_contract_events_query(provider, contract_event_query)

columns_ls = validate_and_expand_columns(columns, ContractLog)
data = map(partial(extract_fields, columns=columns_ls), contract_events)
events = pd.DataFrame(columns=columns_ls, data=data)
print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events)} events (events per second: {len(events)/(time.time()-start_time):.2f})")

# %%`