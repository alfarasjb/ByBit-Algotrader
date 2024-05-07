
from templates import * 
from configs import *
import pandas as pd 
from enum import Enum
from .base import *


class MAType(Enum):
    SIMPLE = 1 # Simple Moving Average
    EXPONENTIAL = 2 # Exponential Moving Average

class MACross(Strategy):
    
    def __init__(
            self, 
            config:TradeConfig, 
            fast_ma_period:int, 
            slow_ma_period: int,
            ma_kind: MAType
        ):
        
        super().__init__("MA Crossover",config)

        # -------------------- Initializing member variables -------------------- #  
        self.fast_ma_period = fast_ma_period 
        self.slow_ma_period = slow_ma_period 
        self.ma_kind = ma_kind

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
     
    @staticmethod
    def __get_side(fast:float, slow:float) -> Side: 
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
    
    def __crossover(self, data: pd.DataFrame) -> bool: 
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


    def __fetch(self, elements:int) -> pd.DataFrame:
        """
        Fetches data from ByBit 

        Parameters
        ----------
            elements: int 
                number of candles to fetch 
        """
        response = None 
        try: 
            response = self.session.get_kline(
                category=self.trade_config.channel, 
                symbol=self.trade_config.symbol,
                interval=self.trade_config.interval,
                limit=elements+1
            )
        except Exception as e: 
            self.log(f"Error: {e}")
            return None 
        

        df = pd.DataFrame(response['result']['list'])
        
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
        df = df.set_index('Time',drop=True)
        # convert timestamp to datetime
        df.index = pd.to_datetime(df.index.astype('int64'), unit='ms')
        # sets values to float 
        df = df.astype(float)
        # inverts the dataframe 
        df = df[::-1] 
        # excludes last row since this is fresh candle, and is still open 
        df = df[:-1]  
        
        return df 
    
    


    def __attach_indicators(self, data:pd.DataFrame) -> pd.DataFrame:
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

    

    def stage(self, candle: Candles):
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
        df = self.__fetch(candles_to_fetch)

        # Attaches indicators based on input values 
        df = self.__attach_indicators(df)

        # Check for crossover 
        cross = self.__crossover(df)

        # Gets last value 
        last = df.iloc[-1]
        fast_ma = last['fast_ma'].item()
        slow_ma = last['slow_ma'].item()

        # Determines side: Long or Short 
        side = self.__get_side(fast_ma, slow_ma) 

        # General Logging 
        info = candle.info() + f" Crossover: {cross} Fast: {fast_ma:.2f} Slow: {slow_ma:.2f} Side: {side.name}"
        self.log(info)

        if cross: 
            # Sends trade orders if MA Crossover is found
            self.close_all_orders()
            self.send_market_order()


    