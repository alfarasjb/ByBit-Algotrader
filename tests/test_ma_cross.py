"""
Tests the functions in the MACross module. 
"""

from strategies import MACross, MAType 
from configs import TradeConfig 
from templates import Side, Timeframes

import unittest 
import numpy as np
import pandas as pd

class TestMACrossStrategy(unittest.TestCase): 
    """
    Tests the Moving Average Crossover strategy 
    """
    def setUp(self): 
        """
        Sets up the parameters for testing 
        """
        long_data = {"Close" : np.arange(0,150)}
        self.long_price_series = pd.DataFrame(long_data)

        self.short_price_series = self.long_price_series[::-1].reset_index(drop=True)

        self.trade_config = TradeConfig(symbol="BTCUSDT", interval=Timeframes.MIN_1, channel='linear')
        self.strategy_config_dict = {"fast_ma_period" : "20", "slow_ma_period" : "100", "ma_kind" : "SIMPLE"} 
        self.strategy = MACross(
            config=self.trade_config,
            strategy_config=self.strategy_config_dict
        )


        
    def test_side(self): 
        """
        Unit tests for the get_side() function
        """
        # prices of moving averages
        # test short 
        fast_ma = 10.50 
        slow_ma = 12.50 

        side_result = self.strategy.get_side(fast = fast_ma, slow = slow_ma)
        self.assertEqual(side_result, Side.SHORT)

        # test long 
        fast_ma = 12.50 
        slow_ma = 10.50 

        side_result = self.strategy.get_side(fast=fast_ma, slow=slow_ma)
        self.assertEqual(side_result, Side.LONG)

        # test neutral 
        fast_ma = slow_ma = 10.50 
        side_result = self.strategy.get_side(fast=fast_ma, slow=slow_ma)
        self.assertEqual(side_result, Side.NEUTRAL)

    def test_long_crossover(self):
        """
        Unit tests for determining crossovers
        """
        long_df = self.strategy.attach_indicators(self.long_price_series)     
        last_row = long_df.index == (len(long_df)-1) 
        long_df.loc[last_row, ['fast_ma','calculated_side']] = [0, -1]
        crossover = self.strategy.crossover(long_df)
        self.assertTrue(crossover)

    def test_short_crossover(self):
        """
        Unit tests for determining crossovers
        """
        short_df = self.strategy.attach_indicators(self.short_price_series)
        last_row = short_df.index == (len(short_df)-1)
        short_df.loc[last_row, ['fast_ma','calculated_side']] = [100000, 1]
        crossover = self.strategy.crossover(short_df)
        self.assertTrue(crossover)

 
        
    