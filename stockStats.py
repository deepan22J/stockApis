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
        if len(tickerList) != len(weightList):
            print("no. of tickers not matching weights, making equal weights")
            self.weightList = np.full(len(tickerList),round(1/len(tickerList),5))
        else:
            self.weightList = np.array(weightList)
        self.startDate = startDate
        self.endDate = endDate

        self.closePriceData = pd.DataFrame()
        for tic in tickerList:
            self.closePriceData[tic] = pd.read_csv(os.path.join(self.csvPath, tic.lstrip('^')+'.csv'), index_col=0)['Adj Close']

        # Filter closing price to only for the selected date, by default both are empty, all data in the csv are included.
        self.closePriceData = self.closePriceData.loc[startDate:endDate]

        #print(self.closePriceData.tail())

    def getCAGR(self, since=10, to_csv=None):
        '''

        :param since: its year from current date. say since 1 yr, since 5 yrs, since 10ys.  1 yr is 250 working days.
        :return:
        '''
        current_price = self.closePriceData.iloc[-1]
        try:
            first_price = self.closePriceData.iloc[-since*250]
        except IndexError as e:
            raise ValueError("No data available to calculate CAGR for {0} years".format(since))
        cagr = (current_price/first_price)**(1.0/since)-1
        # Risk adjusted CAGR
        daily_returns = (self.closePriceData / self.closePriceData.shift(1)) - 1
        stddev = (daily_returns.var()*250)**0.5
        ra_cagr = cagr*(1-stddev)
        cagr_df = pd.DataFrame({'CAGR':cagr, 'STDDEV':stddev, 'RiskAdj_CAGR':ra_cagr})
        print(cagr_df)
        if to_csv:
            cagr_df.to_csv(to_csv)
        return cagr_df

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
            pfolio_names.append(':'.join(self.tickerList))
        pfolio_returns = np.array(pfolio_returns)
        pfolio_volatilities = np.array(pfolio_volatilities)
        pfolio_weight_list = np.array(pfolio_weight_list)
        pfolio_names = np.array(pfolio_names)
        d = np.array([pfolio_names,pfolio_weight_list, pfolio_volatilities, pfolio_returns])
        if to_csv:
            df = pd.DataFrame(d).T
            df.rename(columns={0:'Portfolio Name', 1:'Portfolio WeightList', 2:'Portfolio Volatility', 3:'PortFolio Returns' }, inplace=True)
            #print(df.info())
            df.to_csv(to_csv)
        return df

class nseStocks:
    def __init__(self):
        self.nifty50_csv_path = os.path.join(os.path.dirname(__file__),'inputs','nifty50.csv')
        self.niftymidcap50_csv_path = os.path.join(os.path.dirname(__file__), 'inputs', 'niftymidcap50.csv')
        self.nifty50 = pd.read_csv(self.nifty50_csv_path)
        self.niftymidcap50 = pd.read_csv(self.niftymidcap50_csv_path)

    def getTickers(self, index='nifty50', sectors=[]):
        stocks = self.nifty50
        if index == 'niftymidcap50':
            stocks = self.niftymidcap50
        # if sectors is empty list, will give all stocks
        bool_list = []
        for ind in stocks.Industry:
            if ind in sectors:
                bool_list.append(True)
            else:
                bool_list.append(False)
        sectorFilter = pd.Series(bool_list)
        if len(sectors) == 0:
            return stocks['Symbol']
        else:
            return stocks[sectorFilter]['Symbol']

    def getSectorList(self, index='nifty50'):
        stocks = self.nifty50
        if index == 'niftymidcap50':
            stocks = self.niftymidcap50
        return pd.Series(list(set(stocks.Industry)))

    def getAllData(self, index='nifty50'):
        stocks = self.nifty50
        if index == 'niftymidcap50':
            stocks = self.niftymidcap50
        df = stocks[['Symbol','Company Name', 'Industry']]
        df.set_index('Symbol', inplace=True)
        return df

if __name__ == '__main__':
    start_date = '2000-01-01'
    end_date = None

    #ticker_list = ['INFY', 'BAJFINANCE','BERGEPAINT', 'INDUSINDBK', 'GODREJCP','KAJARIACER','MARICO','MINDTREE','NATCOPHARM','PIDILITIND','SUPREMEIND','VAKRANGEE','ZEEL']
    #weight_list = [0.14,0.0125,0.1116,0.01286,0.0561,0.0352,0.0866,0.191,0.1087,0.0851,0.009,0.0483,0.1011]
    ticker_list = ['INFY', 'BAJFINANCE', 'GODREJCP', 'BERGEPAINT', 'NATCOPHARM']
    weight_list = [0.14,0.0125,0.1116,0.01286,0.0561,0.0866,0.191,0.0851,0.009]
    index_list = ['^NSEI']
    #stkUpdater = updateStockData(ticker_list)
    #stkUpdater.loadTickerDataToCsv(startDate='2000-01-01',endDate=end_date)
    #stkUpdater = updateStockData(index_list)
    #stkUpdater.loadTickerDataToCsv(startDate='2000-01-01', endDate=end_date)
    #statsObj = portFolioStats(tickerList=ticker_list, weightList=weight_list, startDate='2010-01-01', endDate='2020-03-19')
    #statsObj.getCAGR(to_csv='outputs/cagr.csv')
    #statsObj.getPortfolioRetuns()
    #statsObj.getPortfolioRisks()
    #statsObj.calcMarcowitzEfficientFrontier(to_csv='mwef_myportfolio.csv', dataPoints=100)


    #statsObj_index = portFolioStats(tickerList=index_list, weightList=[1.0], endDate='2020-03-19')
    #statsObj_index.getPortfolioRetuns()
    #statsObj_index.getPortfolioRisks()

    nseObj = nseStocks()
    tickers = nseObj.getTickers(index='niftymidcap50')

    #sector_list = nseObj.getSectorList(index='niftymidcap50')
    allData = nseObj.getAllData()
    print(allData)


