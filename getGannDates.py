import os
from pandas_datareader import data as wb
import pandas as pd
import math
from datetime import datetime, timedelta
from pprint import pprint
import sys

csvPath = os.path.join(os.path.dirname(__file__),'csvs')
#tickerList=['^NSEI']
def loadTickerDataToCsv(startDate, endDate,dataSource='yahoo'):

    for ticker in tickerList:
        tic_file = os.path.join(csvPath, ticker.lstrip('^') + '.csv')
        # .NS is for NSE exchange
        if not ticker.startswith('^'):
            ticker = ticker + '.NS'
        tic_data = wb.DataReader(ticker, data_source=dataSource, start=startDate, end=endDate).to_csv(tic_file)

def getHighLowPriceDate():
    high_low_inputs = {}
    for tic in tickerList:
        prices = pd.read_csv(os.path.join(csvPath, tic.lstrip('^') + '.csv'), index_col=0)

        # find min of low col and its corresponding date
        # find max of high col and its corresponding date
        lowPrice =  prices['Low'].min()
        highPrice = prices['High'].max()
        lowPriceDate = prices['Low'].idxmin()
        highPriceDate = prices['High'].idxmax()

        # cal_diff - calendar date difference
        # datetime. strptime(date_time_str, '%d/%m/%y %H:%M:%S')
        cal_diff = datetime.strptime(highPriceDate, '%Y-%m-%d')-datetime.strptime(lowPriceDate,'%Y-%m-%d')
        cal_diff = abs(cal_diff).days+1
        print('cal_diff: '+ str(cal_diff))
        # trade_diff - Trade date difference

        if datetime.strptime(highPriceDate, '%Y-%m-%d') > datetime.strptime(lowPriceDate,'%Y-%m-%d'):
            trade_diff = len(prices[lowPriceDate:highPriceDate])
        else:
            trade_diff = len(prices[highPriceDate:lowPriceDate])
        print('trade_Diff: '+str(trade_diff))

        high_low_inputs[tic] = [lowPrice, highPrice, cal_diff, trade_diff, lowPriceDate, highPriceDate]



        # Form the high_low_inputs of format ex { 'nifty': [<high>, <low>, <high date>, <low date>], ...}
    #print(high_low_inputs)
    return high_low_inputs

def convertToGannDegree(num):
    # =MOD(SQRT(G21)*180-225,360)
    deg = math.fmod((math.sqrt(num)*180 - 225), 360)
    return deg

def getNpoints(deg, N=3):
    cycle_list = []
    # =(2*N+(2*deg)/360+1.25)^2
    for i in range(1, N+1):
        cycle = (2*i+(2*deg)/360+1.25)**2
        cycle_list.append(cycle)
    return cycle_list

def getGannDates(high_low_inputs):
    # TR - Trend Reversal
    gannTRDates = {}
    for tic in high_low_inputs:
        gannTRDates[tic] = []
        high_date = datetime.strptime(high_low_inputs[tic][-1], '%Y-%m-%d')
        low_date = datetime.strptime(high_low_inputs[tic][-2], '%Y-%m-%d')
        gann_degrees = list(map(convertToGannDegree, high_low_inputs[tic][:-2]))
        min_deg = min(gann_degrees)
        max_deg = max(gann_degrees)
        min_cylce_list = getNpoints(min_deg)
        max_cycle_list = getNpoints(max_deg)
        for cycle in min_cylce_list:
            # Consider only cycle less than 50days, so that it may fall in next month
            if cycle > 50:
                continue
            tr_date = high_date + timedelta(days=math.ceil(cycle))
            tr_date = tr_date.strftime('%Y-%m-%d')
            gannTRDates[tic].append(tr_date)
            #print(cycle)
        for cycle in max_cycle_list:
            # Consider only cycle less than 50days, so that it may fall in next month
            if cycle > 50:
                continue
            tr_date = low_date + timedelta(days=math.ceil(cycle))
            tr_date = tr_date.strftime('%Y-%m-%d')
            gannTRDates[tic].append(tr_date)
            #print(cycle)
        #print(gannTRDates)
    return gannTRDates



if __name__ == '__main__':
    # ticket_list comma separated
    tickerList = sys.argv[1].split(',')
    startDate = sys.argv[2]
    endDate = sys.argv[3]
    #ticker_list = ['^NSEI', 'SBIN']
    #loadTickerDataToCsv('06-01-2021', '06-30-2021')
    loadTickerDataToCsv(startDate, endDate)
    high_low_inputs = getHighLowPriceDate()
    gann_dates = getGannDates(high_low_inputs)
    pprint(gann_dates)
    #deg = convertToGannDegree(10985.15)
    #print(deg)
    #deg = 315
    #cycle_list = getNpoints(deg)
    #print(cycle_list)

