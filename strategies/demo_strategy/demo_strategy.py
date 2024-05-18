"""
This is a demo strategy. This is only meant to test the functionality of the code, and does not contain
any trading logic meant for live funds.  


"""

import pandas as pd

from ..base.strategy import Strategy
from ..base.configs import Configs 
from templates.side import Side 
from templates.candles import Candles 
from configs.trade_cfg import TradeConfig


class Demo(Strategy, Configs): 

    def __init__(
            self,
            config:TradeConfig,
            strategy_config:dict
        ):
        
        Strategy.__init__(self, name="Demo Strategy", config=config)
        Configs.__init__(self) 

        self.info()

    def build(self, data:pd.DataFrame) -> pd.DataFrame:
        
        data['change'] = data['Close'] - data['Open']
        data['calculated_side'] = 0 
        long = data['change'] > 0 
        short = data['change'] < 0 
        data.loc[long, 'calculated_side'] = int(Side.BUY.value)
        data.loc[short, 'calculated_side'] = int(Side.SELL.value)

        return data 


    def stage(self, candle: Candles) -> bool:
        candles_to_fetch = 5 
        df = self.fetch(candles_to_fetch)

        df = self.build(df) 

        last = df.iloc[-1]
        calculated_side = last['calculated_side'].item()

        side = self.get_side(calculated_side) 
        
        info = candle.info() + f" Side: {side.name}"
        self.log(info)

        if side == Side.NEUTRAL:
            return False 

        trade_result=False 
        
        self.close_all_open_positions() 

        trade_result = self.send_market_order(side)

        return trade_result


    def backtest(self):
        pass


