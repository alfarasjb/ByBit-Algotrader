"""
This module contains the main implementation of a generic Moving Average Crossover strategy. 
"""


import pandas as pd
from dataclasses import dataclass
from typing import Tuple, Union, Optional

from templates.indicator import MAType
from templates.side import Side
from templates.candles import Candles
from configs.trade_cfg import TradeConfig
from ..base.configs import Configs
from ..base.strategy import Strategy
from backtest.backtest import Backtest


@dataclass
class MACrossConfigs: 
    fast_ma_period: int = 20  # Period of Fast MA
    slow_ma_period: int = 100  # Period of Slow MA
    ma_kind: MAType = MAType.SIMPLE  # MAType: Simple/Exponential


class MACross(Strategy, Configs):
    """
    Main class for Moving Average Crossover strategy, and inherits from Strategy base class. 

    Fetches candle data from ByBit, attaching necessary indicator values, given the input strategy configuration, and\
     generates trading signals accordingly.

    Sends a long position if Fast MA crosses over Slow MA, and vice versa. 
    """
    def __init__(
            self, 
            config: TradeConfig,
            strategy_config: dict):
        """
        Parameter initialization
        
        Parameters
        ----------
            config: TradeConfig
                Stores main trading configuration. Contains Symbol, Timeframe, Channel/Category 
                
            strategy_config: dict 
                Dictionary of strategy config loaded from .ini file, and unpacked into the respective Config Class. 
                Contains strategy parameters for indicators, etc 
        """
        
        Strategy.__init__(self, name="MA Crossover", config=config)
        Configs.__init__(self)

        # -------------------- Initializing member variables -------------------- #  
        self.strategy = self.check_strategy(strategy_config, MACrossConfigs)
        self.fast_ma_period, self.slow_ma_period, self.ma_kind = self.__set_strategy_configs(self.strategy)
        # -------------------- Validate Inputs -------------------- #  
        # Fast ma must be less than slow ma 
        if self.fast_ma_period > self.slow_ma_period: 
            raise ValueError(f"Invalid Inputs for moving average period. \
                             Fast MA cannot be greater than Slow MA. Fast: \
                             {self.fast_ma_period} Slow: {self.slow_ma_period}")
        
        # ----- Prints Trading Info ----- #
        self.info()

        # ----- Prints Strategy Config ----- # 
        self.log(f"Strategy: {self.name} Fast MA: {self.fast_ma_period} Slow MA: {self.slow_ma_period} \
            Kind: {self.ma_kind.name}")

    # -------------------- Private Methods -------------------- #

    def __set_strategy_configs(self, strategy: MACrossConfigs) -> Tuple[int, int, MAType]:
        """
        Validates and sets the strategy configuration given a Config class. 

        If any value is invalid, defaults will be used. 
        
        Parameters
        ----------
            strategy: MACrossConfigs
                Config class for this strategy. Contains necessary information to process incoming data and generate \
                    trade signals.
        """
        try:
            fast = int(strategy.fast_ma_period)
            slow = int(strategy.slow_ma_period)
            # Selects the MA Type given a string input
            ma_kind = self.__select_ma_type(strategy.ma_kind)

            return fast, slow, ma_kind
        
        except TypeError as t:
            print(t)
        except ValueError as v:
            print(v)

        # If any errors are found, Defaults are used. 
        print("Invalid config file. Setting Defaults.")

        return self.get_default_strategy_config_values(MACrossConfigs)
    
    @staticmethod
    def __select_ma_type(kind: Union[str, MAType]) -> MAType:
        """
        Selects type of Moving Average to use based on string input from config file. 
        
        Raises ValueError if value in config file is invalid. 

        Parameters
        ----------
            kind: str 
                Type of moving average to use. Expected Values: SIMPLE, EXPONENTIAL 
        """
        if isinstance(kind, MAType):
            return kind
        if kind == MAType.SIMPLE.name: 
            return MAType.SIMPLE 
        if kind == MAType.EXPONENTIAL.name:
            return MAType.EXPONENTIAL 
        else:
            raise ValueError(f"Incorrect value for MA Type. Use: SIMPLE or EXPONENTIAL. Input: {kind}")

    def __ma(self, data: pd.Series, length: int) -> pd.Series:
        """ 
        Returns a pandas Series based on specified averaging type, and length. 

        Parameters
        ----------
            data: pd.Series 
                pandas Series of closing prices 
            
            length: int 
                rolling window for averaging
        """

        # Returns Moving average based on input type: Simple or Exponential 
        if self.ma_kind == MAType.SIMPLE:
            return data.rolling(length).mean()
        if self.ma_kind == MAType.EXPONENTIAL:
            return data.ewm(span=length).mean()

    def crossover(self, data: pd.DataFrame) -> Optional[bool]:
        """
        Determines if MA crossover is present. 

        Gets the last value, and the preceding value in order to check for crossover. 

        Parameters
        ----------
            data: pd.DataFrame
                Main data to process.
        """
        last, prev = data.iloc[-1], data.iloc[-2]

        # Returns None if Null values are found 
        if last.isna().sum() > 0 or prev.isna().sum() > 0: 
            self.log("Error. Null Values found.")
            return None                    

        last_side = last['calculated_side'].item()
        prev_side = prev['calculated_side'].item()

        # Returns None if no signal is found 
        if last_side == 0 or prev_side == 0:
            return None 
        
        # If returns True - Crossover is present, if last side, and previous side are different signals 
        return last_side != prev_side

    def attach_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Attaches necessary indicators, and trading signals. 

        Generates signals based on Alpha Model. 

        Parameters
        ----------
            data: pd.DataFrame
                Input dataframe containing OHLCV received from ByBit
        """
        # Attaches indicators 
        # Determines type of Moving Average depending on user input
        data['fast_ma'] = self.__ma(data=data['Close'], length=self.fast_ma_period)
        data['slow_ma'] = self.__ma(data=data['Close'], length=self.slow_ma_period)
        
        # build side as 1, -1, 0 
        data['calculated_side'] = 0 
        long_ma = data['fast_ma'] > data['slow_ma'] 
        short_ma = data['fast_ma'] < data['slow_ma']
        data.loc[long_ma, 'calculated_side'] = int(Side.BUY.value)
        data.loc[short_ma, 'calculated_side'] = int(Side.SELL.value)

        return data

    def stage(self, candle: Candles) -> bool:
        """
        Processes main trade logic 

        Sends orders if trading conditions are met. 

        Parameters:
        ----------
            candles: Candles 
                Contains latest ticker information 
        """

        # Fetch data to calculate indicators 
        candles_to_fetch = self.slow_ma_period * 2
        df = self.fetch(candles_to_fetch)

        # Attaches indicators based on input values 
        df = self.attach_indicators(df)

        # Check for crossover 
        cross = self.crossover(df)

        # Gets last value 
        last = df.iloc[-1]
        fast_ma = last['fast_ma'].item()
        slow_ma = last['slow_ma'].item()

        # Determines side: Long or Short 
        # side = self.get_side(fast_ma, slow_ma)
        side = Side.BUY if fast_ma > slow_ma else Side.SELL if fast_ma < slow_ma else Side.NEUTRAL

        # General Logging 
        info = candle.info() + f" Crossover: {cross} Fast: {fast_ma:.2f} Slow: {slow_ma:.2f} Side: {side.name}"
        self.log(info)

        trade_result = False 
        cross = True  # Temporary
        if cross: 
            # Sends trade orders if MA Crossover is found
            self.close_all_open_positions()

            # Returns true if order was sent successfully. 
            trade_result = self.send_market_order(side)

        return trade_result 

    def backtest(self) -> None:
        """
        Tests the strategy on historical data, and plots the equity curve. 
        """
        df = self.fetch(1000)

        df = self.attach_indicators(df)

        bt = Backtest(df)
        bt.plot_equity_curve()
