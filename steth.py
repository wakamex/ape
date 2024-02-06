# %%
import time
from decimal import Decimal

import pandas as pd

from ape import chain, Contract, networks
from dotenv import load_dotenv

load_dotenv()

# %%
connection = "local node through ape"
context = networks.parse_network_choice('ethereum:mainnet')
context.__enter__()
oracle1 = Contract("0x442af784A788A5bd6F42A01Ebe9F287a871243fb")  # steth legacy oracle
oracle2 = Contract("0x852deD011285fe67063a08005c71a85690503Cee")  # steth accounting oracle (v2)
steth = Contract("0xae7ab96520de3a18e5e111b5eaab095312d7fe84")  # Lido v2 main contract
context = networks.parse_network_choice('ethereum:local:http://localhost:8545')
context.__enter__();

# %%
for d in dir(oracle1):
    if not d.startswith("_"):
        print(d)

# %%
# local node through ape took 41.28 seconds for 1011 events (events per second: 24.49)
start_time = time.time()
events = oracle1.PostTotalShares.query("*")
print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events)} events (events per second: {len(events)/(time.time()-start_time):.2f})")

# %%
# local node through ape took 69.69 seconds for 267 events (events per second: 3.83)
start_time = time.time()
events2 = steth.TokenRebased.query("*")
print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events2)} events (events per second: {len(events2)/(time.time()-start_time):.2f})")

# %%
start_time = time.time()
appearances = pd.read_csv("appearances.csv")
blocks = appearances["blockNumber"].unique()
block_data = [next(chain.provider.get_transactions_by_block(block)) for block in blocks]
print(f"took {time.time()-start_time:.2f} seconds")

# %%
for d in dir(chain.provider):
    if not d.startswith("_"):
        print(d)

# %%
# check calculation https://etherscan.io/tx/0xe54e20c06303a975264af1b0c0b48f5dd9d810e25a0c911acaa3fe51dd8ae80d#eventlog
# constants
secondsInYear = 31557600
lidoFeeAsFraction = 0.1

# v1 (event 17)
postTotalPooledEther=9474789017220376713210638
preTotalPooledEther=9492368209626147154837408
timeElapsed=86400
totalShares=8196353921985509597300504
protocolAPR = (postTotalPooledEther - preTotalPooledEther) * secondsInYear / (preTotalPooledEther * timeElapsed)
userAPR = protocolAPR * (1 - lidoFeeAsFraction)
print(f"{userAPR=}")

# v2 (event 18)
timeElapsed=86400
preTotalShares=8212257195589542864157695
preTotalEther=9492368209626147154837408
postTotalShares=8196353921985509597300504
postTotalEther=9474789017220376713210638
sharesMintedAsFees=77017274159689712195
preShareRate = preTotalEther * 1e27 / preTotalShares
postShareRate = postTotalEther * 1e27 / postTotalShares
userAPR = secondsInYear * (
    (postShareRate - preShareRate) / preShareRate
) / timeElapsed
print(f"{userAPR=}")
# now with Decimal
preTotalShares=Decimal(8212257195589542864157695)
preTotalEther=Decimal(9492368209626147154837408)
postTotalShares=Decimal(8196353921985509597300504)
postTotalEther=Decimal(9474789017220376713210638)
preShareRate = preTotalEther * Decimal(1e27) / preTotalShares
postShareRate = postTotalEther * Decimal(1e27) / postTotalShares
userAPR = secondsInYear * (
    (postShareRate - preShareRate) / preShareRate
) / timeElapsed
print(f"{userAPR=}")


# %%