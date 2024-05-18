
import pandas_ta as ta 
import pandas as pd 
from dataclasses import dataclass
from typing import Tuple

from backtest.backtest import Backtest
from ..base.strategy import Strategy 
from configs.trade_cfg import TradeConfig 
from templates.side import Side 
from templates.candles import Candles


@dataclass 
class RSIConfigs:
    period: int
    overbought: int
    oversold: int


class RSI(Strategy):

    def __init__(
            self,
            config: TradeConfig,
            strategy_config: dict):

        super().__init__("RSI", config) 

        # -------------------- Initializing member variables -------------------- #  
        self.strategy = RSIConfigs(**strategy_config)
        self.period, self.overbought, self.oversold = self.__set_strategy_configs(self.strategy) 

        # -------------------- Validate Inputs -------------------- #  
        if self.period <= 0 or self.overbought <= 0 or self.oversold <= 0:
            raise ValueError(f"Invalid inputs. Values must be positive. Period: {self.period} Overbought: \
                {self.overbought} Oversold: {self.oversold}")
        
        if self.period < 2: 
            raise ValueError(f"Invalid period value. Period must be greater than 2. Input: {self.period}")

        if self.oversold > self.overbought: 
            raise ValueError(f"Invalid values. Overbought cannot be less than Oversold. Overbought: {self.overbought}\
                Oversold: {self.oversold}")

        self.info()

        # ----- Prints Strategy Config ----- # 
        self.log(f"Strategy: {self.name} Period: {self.period} Overbought: {self.overbought} Oversold: {self.oversold}")

    # -------------------- Private Methods -------------------- #
    @staticmethod
    def __set_strategy_configs(strategy: RSIConfigs) -> Tuple[int, int, int]:
        try:
            period = int(strategy.period)
            overbought = int(strategy.overbought)
            oversold = int(strategy.oversold) 
            return period, overbought, oversold 
        except TypeError as t: 
            print(t)

        print("Invalid config file. Setting Defaults")
        period = 14 
        overbought = 70
        oversold = 30 
        return period, overbought, oversold
    
    def attach_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        
        data['rsi'] = ta.rsi(data['Close'], self.period)

        # Build side as 1, -1, 0 
        data['calculated_side'] = 0 
        overbought = data['rsi'] > self.overbought 
        oversold = data['rsi'] < self.oversold
        # Sell if overbought
        data.loc[overbought, 'calculated_side'] = int(Side.SELL.value)
        # Buy if oversold 
        data.loc[oversold, 'calculated_side'] = int(Side.BUY.value)

        return data

    @staticmethod
    def is_trade_valid(data: pd.DataFrame) -> bool:
        last = data.iloc[-1]

        side = last['calculated_side'].item()

        return side != 0

    def get_side(self, calc_side: int) -> Side:
        if calc_side == 1:
            return Side.BUY
        if calc_side == -1:
            return Side.SELL
        return Side.NEUTRAL

    def stage(self, candle: Candles) -> bool:

        candles_to_fetch = self.period * 2
        df = self.fetch(candles_to_fetch)

        # Attach indicators 
        df = self.attach_indicators(df)
    
        # Check for overbought/oversold 
        valid = self.is_trade_valid(df)

        # Get Last 
        last = df.iloc[-1]
        rsi = last['rsi'].item()
        calculated_side = last['calculated_side'].item()

        # Get Side 
        side = self.get_side(calculated_side)

        # General Logging 
        info = candle.info() + f" Trade Valid: {valid} RSI: {rsi:.2f}"
        self.log(info) 

        trade_result = False
        if valid:
            # Sends trade orders if RSI is overbought or oversold 
            self.close_all_orders()

            # Returns true if order was sent successfully 
            trade_result = self.send_market_order(side) 
        
        return trade_result 

    def backtest(self) -> None:
        df = self.fetch(1000)

        df = self.attach_indicators(df)

        bt = Backtest(df)
        bt.plot_equity_curve()
