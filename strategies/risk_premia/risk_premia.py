

from templates import *
from backtest import Backtest 
from enum import Enum 
from ..base import * 
import pandas as pd 
from dataclasses import dataclass 
import numpy as np 


@dataclass
class RiskPremiaConfigs:
    skew_period:int=0 
    skew_threshold:float=0.6 

class RiskPremia(Strategy): 

    def __init__(
            self, 
            config:TradeConfig,
            strategy_config:dict
        ): 

        super().__init__("Risk Premia", config)

        if strategy_config is None:
            print(f"No strategy config found. Using defaults")
            self.strategy = RiskPremiaConfigs()
        else:
            self.strategy = RiskPremiaConfigs(**strategy_config)
        
        self.skew_period, self.upper_threshold, self.lower_threshold = self.__set_strategy_configs(self.strategy)


        if self.skew_period <=  0: 
            raise ValueError(f"Invalid inputs for skew period. Value must be greater than 0. Input: {self.skew_period}")
        
        self.info()


    def __set_strategy_configs(self, strategy:RiskPremiaConfigs): 

        try:
            period = int(strategy.skew_period) 
            upper = float(abs(strategy.skew_threshold))
            lower = -float(abs(strategy.skew_threshold))

            return period, upper, lower 
        
        except TypeError as t:
            print(t)
        except ValueError as v:
            print(v)

        print("Invalid config file. Setting Defaults.")
        period = 10 
        upper = 0.6
        lower = -0.6 

        return period, upper, lower
    
    def attach_indicators(self, data:pd.DataFrame) -> pd.DataFrame: 

        data['skew'] = data['Close'].rolling(self.skew_period).skew()

        data['calculated_side'] = 0 
        long_position = data['skew'] < self.lower_threshold 
        short_position = data['skew'] > self.upper_threshold 
        data.loc[long_position, 'calculated_side'] = int(Side.LONG.value)
        data.loc[short_position, 'calculated_side'] = int(Side.SHORT.value)
        """
        data['active_position'] = np.nan 
        traded = data['calculated_side'] != 0 
        data.loc[traded, 'active_position'] = data['calculated_side'].shift(1)
        data['active_position'] = data['active_position'].ffill() 
        """
        return data 
    
    def stage(self, candle:Candles) -> bool: 

        candles_to_fetch = self.skew_period * 2 
        df = self.fetch(candles_to_fetch) 

        df = self.attach_indicators(df)

        last = df.iloc[-1]

        skew = last['skew'].item()

        side = Side.LONG if skew < self.lower_threshold else Side.SHORT if skew > self.upper_threshold else Side.NEUTRAL 

        info = candle.info() + f" Skew: {skew} Side: {side.name}"
        self.log(info)

        trade_result = False 
        if side != Side.NEUTRAL: 
            self.close_all_orders()

            trade_result = self.send_market_order(side)

        return trade_result

    def backtest(self): 
        """
        Tests the strategy on historical data, and plots the equity curve. 
        """
        df = self.fetch(1000)

        df = self.attach_indicators(df)

        bt = Backtest(df)
        bt.plot_equity_curve()