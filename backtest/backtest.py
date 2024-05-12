"""
This module contains the Backtest class, which is the primary class for holding methods and 
relevant information pertaining to backtesting strategies in the strategies module. 
"""

import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np 

class Backtest:

    def __init__(self, data:pd.DataFrame):
        # Validate columns first 
        # Required columns: calculated_side, close
        try:
            self.valid_columns(data.copy())

        except ValueError as e:
            print(f"Error: {e}")
        
        self.data = data 
        self.backtest_data = self.start(self.data.copy())

    @staticmethod
    def valid_columns(data):
        required_columns = ['calculated_side','close']
        data_columns = [c.lower() for c in data.columns]
        for r in required_columns: 
            if r not in data_columns:
                raise ValueError(f"Error. Missing column: {r}")


    def start(self, data:pd.DataFrame) -> pd.DataFrame:
        # Calculate returns 
        data.columns = [c.lower() for c in data.columns]
        
        if 'log_returns' not in data.columns: 
            data['log_returns'] = np.log(data['close']/data['close'].shift(1))
        
        if 'signal' not in data.columns: 
            data['signal'] = data['calculated_side'].shift(1)

        data['strategy_returns'] = data['signal'] * data['log_returns']
        data['cumm_returns'] = data['strategy_returns'].cumsum()
        return data 
        
    def plot_equity_curve(self, data:pd.DataFrame=None) -> None: 
        
        if data is None:
            data = self.backtest_data 
        
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Invalid type. DataFrame required")

        if 'cumm_returns' not in data.columns:
            raise ValueError("Strategy Returns not found in test dataframe.")
        
        data['cumm_returns'].plot(figsize=(12, 6))
        plt.title('Equity Curve')
        plt.ylabel('Strategy Returns')
        plt.show()

        