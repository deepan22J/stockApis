import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    def __init__(self, tickerList=[], weightList=[], startDate='', endDate=''):
        self.csvPath = os.path.join(os.path.dirname(__file__),'csvs')
        self.tickerList = tickerList
        self.weightList = np.array(weightList)
        self.startDate = startDate
        self.endDate = endDate
        if len(tickerList) != len(weightList):
            raise ValueError("no. of tickers not matching weights")
        self.closePriceData = pd.DataFrame()
        for tic in tickerList:
            self.closePriceData[tic] = pd.read_csv(os.path.join(self.csvPath, tic.lstrip('^')+'.csv'), index_col=0)['Adj Close']

        # Filter closing price to only for the selected date, by default both are empty, all data in the csv are included.
        self.closePriceData = self.closePriceData.loc[startDate:endDate]

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


    def calcMarcowitzEfficientFrontier(self, dataPoints=1000, to_csv=None):
        '''
        This returns a numpy array of size dataPoints contains the expected portfolio returns for a set weights and its
        standard deviations plotting this with standard deviation in x and portfolio returns in y will give Marcowitz efficient Frontier.
        :return:
        '''
        log_returns = np.log(self.closePriceData/self.closePriceData.shift(1))
        pfolio_returns = []
        pfolio_volatilities = []
        pfolio_weight_list = []
        pfolio_names = []
        num_assets = len(self.tickerList)
        for x in range(dataPoints):
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            pfolio_returns.append(np.sum(weights*log_returns.mean())*250)
            pfolio_volatilities.append(np.sqrt(np.dot(weights.T,np.dot(log_returns.cov()*250,weights))))
            weights = np.around(weights*100,decimals=2)
            weights = ':'.join(map(str, list(weights)))
            pfolio_weight_list.append(weights)
            pfolio_names.append('pfolio_'+str(x))
        pfolio_returns = np.array(pfolio_returns)
        pfolio_volatilities = np.array(pfolio_volatilities)
        pfolio_weight_list = np.array(pfolio_weight_list)
        pfolio_names = np.array(pfolio_names)
        d = np.array([pfolio_names,pfolio_volatilities, pfolio_returns,pfolio_weight_list])
        if to_csv:
            df = pd.DataFrame(d).T
            df.rename(columns={0:'Portfolio Name', 1:'Portfolio Volatility', 2:'PortFolio Returns', 3:'Portfolio WeightList'}, inplace=True)
            #print(df.info())
            df.to_csv(to_csv)
        return d





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
    statsObj = portFolioStats(tickerList=ticker_list, weightList=weight_list, endDate='2020-03-19')
    statsObj.getPortfolioRetuns()
    statsObj.getPortfolioRisks()
    statsObj.calcMarcowitzEfficientFrontier(to_csv='mwef.csv')


    #statsObj_index = portFolioStats(tickerList=index_list, weightList=[1.0], endDate='2020-03-19')
    #statsObj_index.getPortfolioRetuns()
    #statsObj_index.getPortfolioRisks()

