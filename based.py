import time
from ape import Contract, networks

context = networks.parse_network_choice('ethereum:mainnet')
context.__enter__()
steth = Contract("0xae7ab96520de3a18e5e111b5eaab095312d7fe84")
context = networks.parse_network_choice('ethereum:local:http://localhost:8545')
context.__enter__()
start_time = time.time()
events2 = steth.TokenRebased.query("*")
print(f"local node through ape took {time.time()-start_time:.2f} seconds for {len(events2)} events (events per second: {len(events2)/(time.time()-start_time):.2f})")