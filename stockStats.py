import os
import numpy as np
import pandas as pd

from pandas_datareader import data as wb

#pg = wb.DataReader('PG', data_source='yahoo', start='2000-01-01')
#print(pg.head())

class updateStockData:
    '''
    This class can be initiated as service to run daily to update the csv files and other stock process classes can use
    this csvs to load and process stock data as it allows offline processing.
    #TODO updatestockdata should be written in such a way that it will update only the differences.
    '''
    def __init__(self, tickerList=[]):
        self.tickerList = tickerList
        self.csvPath = os.path.join(os.path.dirname(__file__),'csvs')
        if not os.path.exists(self.csvPath):
            os.makedirs(self.csvPath)

    def loadTickerDataToCsv(self, startDate, tickerList=None, endDate=None, dataSource='yahoo'):
        if not tickerList:
            tickerList = self.tickerList
        for ticker in tickerList:
            tic_file = os.path.join(self.csvPath, ticker.lstrip('^')+'.csv')
            # .NS is for NSE exchange
            if not ticker.startswith('^'):
                ticker = ticker+'.NS'
            tic_data = wb.DataReader(ticker, data_source=dataSource, start=startDate, end=endDate).to_csv(tic_file)



class portFolioStats:
    def __init__(self, tickerList=[], weightList=[]):
        self.csvPath = os.path.join(os.path.dirname(__file__),'csvs')
        self.tickerList = tickerList
        self.weightList = np.array(weightList)
        if len(tickerList) != len(weightList):
            raise ValueError("no. of tickers not matching weights")
        self.closePriceData = pd.DataFrame()
        for tic in tickerList:
            self.closePriceData[tic] = pd.read_csv(os.path.join(self.csvPath, tic.lstrip('^')+'.csv'), index_col=0)['Adj Close']
        #print(self.closePriceData.tail())

    def getPortfolioRetuns(self):
        self.daily_returns = (self.closePriceData/self.closePriceData.shift(1))-1
        self.annual_returns = self.daily_returns.mean()*250
        print("Annual Returns: \n{0}".format(self.annual_returns))
        self.pfolio_returns = np.dot(self.annual_returns, self.weightList)
        print("Portfolio Returns: {0}".format(str(round(self.pfolio_returns*100,3))+'%'))

    def getPortfolioRisks(self):
        self.pfolio_var = np.dot(self.weightList.T, np.dot(self.daily_returns.cov()*250, self.weightList))
        print("Portfolio Variance: {0}".format(round(self.pfolio_var,5)))
        self.pfolio_volatility = self.pfolio_var**0.5
        print("Portfolio Volatility: {0}".format(str(round(self.pfolio_volatility*100,3))+'%'))
        # Risk is divided into two parts - Systematic (Undiversifiable - unpredictable events like war, crash) and Unsystematic (Diversifiable - depends on company performance)\
        # Undiversifiable Risk = Portfolio Variance - Diverisfiable Risk
        # Diversifiable Risk = Portfolio Variance - (sum of weighted annual variance of each stocks in the portfolio. This is nothing but Undiversifiable Risk)
        annualWeightedVariance = self.calcWeightedAnnualVariance()
        self.undiversifiableRisk = annualWeightedVariance
        self.diversifiableRisk = self.pfolio_var - self.undiversifiableRisk
        print("Diversifiable Risk: {0}".format(str(round(self.diversifiableRisk*100,3))+'%'))
        print("Undiversifiable Risk: {0}".format(str(round(self.undiversifiableRisk * 100, 3)) + '%'))


    def calcWeightedAnnualVariance(self):
        '''
        This is nothing but the undiversifiable risk
        :return:
        '''
        weightedAnnualVariance = 0.0
        for tic,w in zip(self.tickerList,self.weightList):
            var = self.daily_returns[tic].var()*250
            weightedAnnualVariance += w**2*var
        return weightedAnnualVariance




if __name__ == '__main__':
    start_date = '2000-01-01'
    end_date = None

    ticker_list = ['TCS', 'INFY']
    weight_list = [0.5,0.5]
    index_list = ['^NSEI']
    #stkUpdater = updateStockData(ticker_list)
    #stkUpdater.loadTickerDataToCsv(startDate='2000-01-01',endDate=end_date)
    #stkUpdater = updateStockData(index_list)
    #stkUpdater.loadTickerDataToCsv(startDate='2000-01-01', endDate=end_date)
    statsObj = portFolioStats(tickerList=ticker_list, weightList=weight_list)
    statsObj.getPortfolioRetuns()
    statsObj.getPortfolioRisks()
    statsObj_index = portFolioStats(tickerList=index_list, weightList=[1.0])
    statsObj_index.getPortfolioRetuns()
    statsObj_index.getPortfolioRisks()
