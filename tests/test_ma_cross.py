"""
Tests the functions in the MACross module. 
"""

import unittest
import numpy as np
import pandas as pd

from strategies import MACross, MAType
from configs.trade_cfg import TradeConfig
from templates.side import Side
from templates.intervals import Timeframes
from constants import constants


class TestMACrossStrategy(unittest.TestCase): 
    """
    Tests the Moving Average Crossover strategy 
    """
    def setUp(self) -> None:
        """
        Sets up the parameters for testing 
        """
        long_data = {"Close": np.arange(0, 150)}
        self.long_price_series = pd.DataFrame(long_data)

        self.short_price_series = self.long_price_series[::-1].reset_index(drop=True)

        self.trade_config = TradeConfig(symbol=constants.SYMBOL, interval=Timeframes.MIN_1, channel=constants.CHANNEL)
        self.strategy_config_dict = {"fast_ma_period": "20", "slow_ma_period": "100", "ma_kind": "SIMPLE"}
        self.strategy = MACross(
            config=self.trade_config,
            strategy_config=self.strategy_config_dict
        )

    def test_faulty_strat_config(self) -> None:
        """ 
        
        """
        strategy_config = {"fast_ma_period": "20", "slow_ma_period": "wrong_value", "ma_kind": "invalid"}
        strategy = MACross(
            config=self.trade_config,
            strategy_config=strategy_config
        )

    def test_long_crossover(self) -> None:
        """
        Unit tests for determining crossovers
        """
        long_df = self.strategy.attach_indicators(self.long_price_series)     
        last_row = long_df.index == (len(long_df)-1) 
        long_df.loc[last_row, ['fast_ma', 'calculated_side']] = [0, -1]
        crossover = self.strategy.crossover(long_df)
        self.assertTrue(crossover)

    def test_short_crossover(self) -> None:
        """
        Unit tests for determining crossovers
        """
        short_df = self.strategy.attach_indicators(self.short_price_series)
        last_row = short_df.index == (len(short_df)-1)
        short_df.loc[last_row, ['fast_ma', 'calculated_side']] = [100000, 1]
        crossover = self.strategy.crossover(short_df)
        self.assertTrue(crossover)
    