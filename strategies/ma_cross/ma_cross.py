
from templates import * 
from configs import *
import pandas as pd 
from enum import Enum
from ..base import *
from dataclasses import dataclass


class MAType(Enum):
    SIMPLE = 1 # Simple Moving Average
    EXPONENTIAL = 2 # Exponential Moving Average

@dataclass
class MACrossConfigs: 
    fast_ma_period:int
    slow_ma_period:int 
    ma_kind: MAType

class MACross(Strategy):
    
    def __init__(
            self, 
            config:TradeConfig, 
            #fast_ma_period:int, 
            #slow_ma_period: int,
            #ma_kind: MAType
            strategy_config:dict
        ):
        
        super().__init__("MA Crossover",config)

        # -------------------- Initializing member variables -------------------- #  
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
        Sets strategy configuration given Config Class 
        """
        try:
            fast = int(strategy.fast_ma_period)
            slow = int(strategy.slow_ma_period)
            ma_kind = self.__select_ma_type(strategy.ma_kind)

            return fast, slow, ma_kind
        
        except TypeError as t:
            print(t)
        except ValueError as v:
            print(v)

        # If invalid, set hard-coded defaults
        print("Invalid config file. Setting Defaults.")
        fast = 20
        slow = 100 
        ma_kind = MAType.SIMPLE 

        return fast, slow, ma_kind

    
    @staticmethod
    def __select_ma_type(kind:str) -> MAType: 
        """
        Selects MAType based on config file
        """
        if kind == MAType.SIMPLE.name: 
            return MAType.SIMPLE 
        if kind == MAType.EXPONENTIAL.name:
            return MAType.EXPONENTIAL 
        else:
            raise ValueError("Incorrect value for MA Type. Use: SIMPLE or EXPONENTIAL")
        
    

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

        Parameters
        ----------
            data: pd.DataFrame
                data to process 
        """
        last, prev = data.iloc[-1], data.iloc[-2]

        if last.isna().sum() > 0 or prev.isna().sum() > 0: 
            self.log("Error. Null Values found.")
            return None                    
        
        
        last_side = last['side'].item()
        prev_side = prev['side'].item()

        if last_side == 0 or prev_side == 0:
            return None 
        
        return last_side != prev_side 


    def attach_indicators(self, data:pd.DataFrame) -> pd.DataFrame:
        """
        Attaches indicators and generates side 

        Parameters
        ----------
            data: pd.DataFrame
                input dataframe containing OHLCV received from ByBit
        """
        # Attaches indicators 
        # Determines type of Moving Average depending on user input
        data['fast_ma'] = self.__ma(data=data['Close'], length=self.fast_ma_period)
        data['slow_ma'] = self.__ma(data=data['Close'], length=self.slow_ma_period)
        
        # build side as 1, -1, 0 
        data['side'] = 0 
        long_ma = data['fast_ma'] > data['slow_ma'] 
        short_ma = data['fast_ma'] < data['slow_ma']
        data.loc[long_ma, 'side'] = int(Side.LONG.value)
        data.loc[short_ma, 'side'] = int(Side.SHORT.value)

        return data


    def stage(self, candle: Candles) -> bool:
        """
        Processes main trade logic 

        Sends orders if trading conditions are met. 

        Parameters:
        ----------
            candles: Candles 
                contains latest ticker information 
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
        side = self.get_side(fast_ma, slow_ma) 

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

    
    