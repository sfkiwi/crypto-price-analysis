'''Backtest the Pantera strategy where you buy
when price crosses a long MA (200 day) and then hold
for a long period (1 year)
'''
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import MA

class PanteraBacktester(MA.MABacktester):
    '''Backtest the Pantera strategy
    series: Pandas Series containing a list of closing prices by date
    ms: int, short moving average (default 1)
    ml: int, long moving average (default 200)
    hold: int, how many days you hold before selling
    '''

    def __init__(self, series, ms=1, ml=200, hold = 365, ema = False):
        self._df = series.to_frame().dropna()
        self._df.columns = ['last']
        self._ms = ms
        self._ml = ml
        self._hold = hold
        self._ema = ema
        self._results = {}
        self._has_run = False
        self._long_only = True

    def __str__(self):
        start_date = self._df.index[0].strftime('%Y-%m-%d')
        end_date = self._df.index[-1].strftime('%Y-%m-%d')
        return "Pantera Backtest Strategy (ms=%d, ml=%d, hold=%d, ema=%s, start=%s, end=%s)" % (
            self._ms, self._ml, self._hold, str(self._ema), str(start_date), str(end_date))


    def _trade_logic(self):
        '''Implements the trade logic in order to come up with
        a set of stances
        '''

        if self._ema:
            self._df['ms'] = np.round(self._df['last'].ewm(span=self._ms, adjust=False).mean(),8)
            self._df['ml'] = np.round(self._df['last'].ewm(span=self._ml, adjust=False).mean(),8)
        else:
            self._df['ms'] = np.round(self._df['last'].rolling(window=self._ms).mean(), 8)
            self._df['ml'] = np.round(self._df['last'].rolling(window=self._ml).mean(), 8)

        self._df['mdiff'] = self._df['ms'] - self._df['ml']
        self._df['stance'] = np.where(self._df['mdiff'] >= 0, 1, 0)

        if not self._long_only:
            self._df['stance'] = np.where(self._df['mdiff'] < 0, -1, self._df['stance'])
            self._df['stance'].replace(to_replace=0, method='ffill').values

        # Logic for holding period
        self._df['stance2'] = 0 
        
        end = len(self._df)
        reached_the_end = False;

        crossovers = np.where((self._df['stance'] ==1) & (self._df['stance'].shift(1) == 0))
        for i in crossovers[0]: # for some reason crossovers is a tuple
            if self._df['stance2'].iloc[i] == 0: # make sure we are not long already
                j = i+self._hold + 1 # adding 1 here since dates go from close to close
                if j > end:
                    j = end
                    reached_the_end = True
                self._df['stance2'].iloc[i:j-1] = 1
                if not reached_the_end: self._df['stance2'].iloc[j] = 0

        
        self._df['stance'] =  self._df['stance2'] # easier than making lots of changes below


    