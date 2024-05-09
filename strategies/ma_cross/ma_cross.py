"""
This module contains the main implementation of a generic Moving Average Crossover strategy. 
"""


from templates import * 
from configs import *
import pandas as pd 
from enum import Enum
from ..base import *
from dataclasses import dataclass
from backtest import *


class MAType(Enum):
    """ 
    Enum for holding MA Type
    
    1. Simple Moving Average
    2. Exponential Moving Average 
    """
    SIMPLE = 1 # Simple Moving Average
    EXPONENTIAL = 2 # Exponential Moving Average

@dataclass
class MACrossConfigs: 
    fast_ma_period:int=20 # Period of Fast MA
    slow_ma_period:int=100 # Period of Slow MA 
    ma_kind: MAType=MAType.SIMPLE # MAType: Simple/Exponential 

class MACross(Strategy):
    """
    Main class for Moving Average Crossover strategy, and inherits from Strategy base class. 

    Fetches candle data from ByBit, attaching necessary indicator values, given the input strategy configuration, and generates 
    trading signals accordingly. 

    Sends a long position if Fast MA crosses over Slow MA, and vice versa. 
    """
    def __init__(
            self, 
            config:TradeConfig, 
            strategy_config:dict
        ):
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
        
        super().__init__("MA Crossover",config)

        # -------------------- Initializing member variables -------------------- #  
        if strategy_config is None: 
            # strategy_config is None if no config files are found in config directory. 
            print(f"No Strategy config found. Using defaults.")
            #self.strategy = MACrossConfigs(fast_ma_period=20, slow_ma_period=100, ma_kind=MAType.SIMPLE)
            self.strategy=MACrossConfigs()
        else:
            self.strategy = MACrossConfigs(**strategy_config)
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
        self.log(f"Strategy: {self.name} Fast MA: {self.fast_ma_period} Slow MA: {self.slow_ma_period} Kind: {self.ma_kind.name}")


    # -------------------- Private Methods -------------------- #   
    def __set_strategy_configs(self, strategy:MACrossConfigs): 
        """
        Validates and sets the strategy configuration given a Config class. 

        If any value is invalid, defaults will be used. 
        
        Parameters
        ----------
            strategy: MACrossConfigs
                Config class for this strategy. Contains necessary information to process incoming data and generate trade signals. 
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
        fast = 20
        slow = 100 
        ma_kind = MAType.SIMPLE 

        return fast, slow, ma_kind

    
    @staticmethod
    def __select_ma_type(kind:str) -> MAType: 
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
        
    

    def __ma(self, data:pd.Series, length:int) -> pd.Series:
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
        

    # Note: This is currently not used 
    @staticmethod
    def get_side(fast:float, slow:float) -> Side: 
        """
        Determines side based on trade logic, and moving average values. 

        Parameters
        ----------
            fast: float 
                fast moving average 
            slow: float 
                slow moving average
        """
        
        if fast > slow: 
            return Side.LONG 
        if fast < slow:
            return Side.SHORT 
        return Side.NEUTRAL
    

    def crossover(self, data: pd.DataFrame) -> bool: 
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


    def attach_indicators(self, data:pd.DataFrame) -> pd.DataFrame:
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
        data.loc[long_ma, 'calculated_side'] = int(Side.LONG.value)
        data.loc[short_ma, 'calculated_side'] = int(Side.SHORT.value)

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
        #side = self.get_side(fast_ma, slow_ma) 
        side = Side.LONG if fast_ma > slow_ma else Side.SHORT if fast_ma < slow_ma else Side.NEUTRAL

        # General Logging 
        info = candle.info() + f" Crossover: {cross} Fast: {fast_ma:.2f} Slow: {slow_ma:.2f} Side: {side.name}"
        self.log(info)

        trade_result = False 
        if cross: 
            # Sends trade orders if MA Crossover is found
            self.close_all_orders()

            # Returns true if order was sent successfully. 
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