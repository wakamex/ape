# %%
import time
from decimal import Decimal

import pandas as pd

from ape import Contract, networks
from dotenv import load_dotenv
from matplotlib import pyplot as plt

load_dotenv()

# %%
# context = networks.parse_network_choice('ethereum:mainnet:https://rpc.mevblocker.io')
# context.__enter__();
# connection = "local node through ape"
# context = networks.parse_network_choice('ethereum:local:http://localhost:8545')
connection = "alchemy through ape"
context = networks.parse_network_choice('ethereum:mainnet:alchemy')
# connection = "infura through ape"
# rpc_url = f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
# context = networks.parse_network_choice(f"ethereum:mainnet:{rpc_url}")
context.__enter__();
legacy_abi = '[{"anonymous": false,"inputs": [{ "indexed": false, "name": "postTotalPooledEther", "type": "uint256" },{ "indexed": false, "name": "preTotalPooledEther", "type": "uint256" },{ "indexed": false, "name": "timeElapsed", "type": "uint256" },{ "indexed": false, "name": "totalShares", "type": "uint256" }],"name": "PostTotalShares","type": "event"}]'
oracle1 = Contract("0x442af784A788A5bd6F42A01Ebe9F287a871243fb", abi=legacy_abi)  # steth legacy oracle
v2_abi = '[{"anonymous": false,"inputs": [{ "indexed": true, "name": "reportTimestamp", "type": "uint256" },{ "indexed": false, "name": "timeElapsed", "type": "uint256" },{ "indexed": false, "name": "preTotalShares", "type": "uint256" },{ "indexed": false, "name": "preTotalEther", "type": "uint256" },{ "indexed": false, "name": "postTotalShares", "type": "uint256" },{ "indexed": false, "name": "postTotalEther", "type": "uint256" },{ "indexed": false, "name": "sharesMintedAsFees", "type": "uint256" }],"name": "TokenRebased","type": "event"}]'
# oracle2 = Contract("0x852deD011285fe67063a08005c71a85690503Cee")  # steth accounting oracle (v2)
steth = Contract("0xae7ab96520de3a18e5e111b5eaab095312d7fe84",abi=v2_abi)  # Lido v2 main contract

# %%
# local node through ape took 41.28 seconds for 1011 events (events per second: 24.49)
# 250k block page size: alchemy through ape took 10.33 seconds for 1012 events (events per second: 97.95)
# 2.5m block page size: alchemy through ape took 1.60 seconds for 1012 events (events per second: 631.47)
# infura through ape took 9.62 seconds for 1012 events (events per second: 105.17)
start_time = time.time()
events = oracle1.PostTotalShares.query("*")
print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events)} events (events per second: {len(events)/(time.time()-start_time):.2f})")

# %%
# local node through ape took 69.69 seconds for 267 events (events per second: 3.83)
# 250k block page size: alchemy through ape took 11.92 seconds for 268 events (events per second: 22.48)
# 2.5m block page size: alchemy through ape took 1.34 seconds for 268 events (events per second: 200.64)
# infura through ape took 9.39 seconds for 268 events (events per second: 28.55)
start_time = time.time()
events2 = steth.TokenRebased.query("*")
print(f"{connection} took {time.time()-start_time:.2f} seconds for {len(events2)} events (events per second: {len(events2)/(time.time()-start_time):.2f})")

# %%
docs="""
Lido APR documentation
https://docs.lido.fi/contracts/legacy-oracle

Lido v1:
    protocolAPR = (postTotalPooledEther - preTotalPooledEther) * secondsInYear / (preTotalPooledEther * timeElapsed)
    lidoFeeAsFraction = lidoFee / basisPoint
    userAPR = protocolAPR * (1 - lidoFeeAsFraction)

Lido v2:
    userAPR =
        secondsInYear * (
            (postShareRate - preShareRate) / preShareRate
        ) / timeElapsed

constants:
    secondsInYear = 31557600
    secondsInDay = 86400
    lidoFeeAsFraction = lidoFee / basisPoint = 0.1
"""
# constants
secondsInYear = 31557600
lidoFeeAsFraction = 0.1
decimalOne = Decimal(1)
decimalSecondsInYear = Decimal(secondsInYear)
decimalLidoFeeAsFraction = Decimal(lidoFeeAsFraction)

# %%
def calc_legacy_apr(series) -> Decimal:
    record = series.event_arguments
    protocolAPR = (Decimal(record["postTotalPooledEther"]) - Decimal(record["preTotalPooledEther"])) * decimalSecondsInYear / (Decimal(record["preTotalPooledEther"]) * Decimal(record["timeElapsed"]))
    return protocolAPR * (decimalOne - decimalLidoFeeAsFraction)

events["userAPR"] = events.apply(calc_legacy_apr,axis=1)
display(events["userAPR"])

# %%
def calc_v2_apr(series) -> Decimal:
    record = series.event_arguments
    timeElapsed = Decimal(record["timeElapsed"])
    preTotalShares = Decimal(record["preTotalShares"])
    preTotalEther = Decimal(record["preTotalEther"])
    postTotalShares = Decimal(record["postTotalShares"])
    postTotalEther = Decimal(record["postTotalEther"])
    preShareRate = preTotalEther * Decimal(1e27) / preTotalShares
    postShareRate = postTotalEther * Decimal(1e27) / postTotalShares
    return (decimalSecondsInYear * ((postShareRate - preShareRate) / preShareRate) / timeElapsed)

events2["userAPR2"] = events2.apply(calc_v2_apr,axis=1)
display(events2["userAPR2"])

# %%
apr_data = events[["block_number","userAPR"]]
apr_data = pd.merge(apr_data,events2[["block_number","userAPR2"]],on="block_number",how="left")
apr_data["apr"] = apr_data["userAPR"]
idx = apr_data["userAPR2"].notna()
apr_data.loc[idx,"apr"] = apr_data.loc[idx,"userAPR2"]
display(apr_data)

# %%
merge_block = 15_537_393
# pre-merge
# plt.scatter(apr_data["block_number"],apr_data["apr"],s=1)
idx = apr_data["block_number"] < merge_block
plt.scatter(apr_data.loc[idx,["block_number"]],apr_data.loc[idx, ["apr"]],s=1,label="pre-merge")
# post-merge
idx = apr_data["block_number"] >= merge_block
plt.scatter(apr_data.loc[idx,["block_number"]],apr_data.loc[idx, ["apr"]],s=1,label="post-merge")
plt.ylim(0.02,0.1)
plt.title("stEth daily APR")
plt.xlabel("block number")
plt.ylabel("APR")
plt.legend()
plt.show()

# %%
# plot rolling average
plt.plot(apr_data["block_number"],apr_data["apr"].rolling(365).mean(), label="mean")
ax1 = plt.gca()
plotcolor = ax1.lines[0].get_color()
plt.xlabel("block number")
plt.ylabel("mean", color=plotcolor)
plt.gca().spines['left'].set_color(plotcolor)
plt.gca().tick_params(axis='y', color=plotcolor, labelcolor=plotcolor)
# plot standard deviation
ax2 = plt.twinx()
ax2.spines['right'].set_color("red")
ax2.tick_params(axis='y', color='red', labelcolor='red')
ax2.plot(apr_data["block_number"],apr_data["apr"].rolling(365).std(), color="red",label="standard deviation (RHS)")
ax2.set_ylabel("standard deviation", color="red")
# plt.ylim(0.02,0.1)
plt.title("Mean and standard deviation of stEth daily APR\n365-day rolling average, since the merge")
combined_legend = [ax1.lines[0],ax2.lines[0]]
combined_labels = [ax1.get_lines()[0].get_label(),ax2.get_lines()[0].get_label()]
plt.legend(combined_legend, combined_labels, loc="upper left")
plt.show()

# %%
# display a clean table
display(apr_data.head(5).style.hide(axis="index").hide(axis="columns",subset=["userAPR","userAPR2"]))

# %%