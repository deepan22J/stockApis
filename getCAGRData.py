import os
import sys
import re
import pandas as pd
import argparse
from stockStats import updateStockData, portFolioStats, nseStocks


parser = argparse.ArgumentParser(description="Tool to generate the CAGR for nifty50/niftymidcap.  The CSV contains Stocks, Sector, CAGR, Standard Deviation, Risk Adjusted CAGR")
parser.add_argument('--index', dest='nseindex', help="Index name.  Value can be nifty50/nfitymidcap50", choices=['nifty50','niftymidcap50'])
parser.add_argument('--tocsv', dest='tocsv', help="Where to store the CSV file")
parser.add_argument('--updateData', dest='updateData', default=False, help="Updates the stock pricess from yahoo finance",type=bool)
args = parser.parse_args()
nseindex = args.nseindex
tocsv = args.tocsv
updateData = args.updateData

nseObj = nseStocks()
ticker_list = list(nseObj.getTickers(index=nseindex))
ticker_list.insert(0,'^NSEI')
if updateData:
    stkUpdater = updateStockData(ticker_list)
    stkUpdater.loadTickerDataToCsv(startDate='2000-01-01')
statsObj = portFolioStats(tickerList=ticker_list,startDate=None, endDate=None)
cagr_df = statsObj.getCAGR(since=10)
allTickers = nseObj.getAllData(index=nseindex)
allTickers.loc['^NSEI'] = ['Nify50', 'Index']
print(allTickers)
result = pd.concat([allTickers,cagr_df], axis=1, sort=False)
result.to_csv(tocsv)




