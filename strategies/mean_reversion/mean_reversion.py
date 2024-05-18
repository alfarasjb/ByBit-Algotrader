import pandas as pd 
from dataclasses import dataclass
from typing import Union, Tuple, Optional

from ..base.strategy import Strategy 
from ..base.configs import Configs 
from configs.trade_cfg import TradeConfig 
from templates.indicator import MAType 
from templates.side import Side 
from templates.candles import Candles


@dataclass 
class MeanReversionConfigs: 
    mean_period: int = 20  # Rolling mean to measure spread
    spread_mean_period: int = 10  # Rolling spread mean to calculate Rolling z-score
    spread_sdev_period: int = 10  # Rolling spread standard deviation to calculate Rolling z-score
    threshold: float = 1.0  # Thresholds for buy and sell signals
    ma_kind: MAType = MAType.SIMPLE  # Moving average type


class MeanReversion(Strategy, Configs):
    def __init__(
            self,
            config: TradeConfig,
            strategy_config: dict):
        
        Strategy.__init__(self, name="Mean Reversion", config=config)
        Configs.__init__(self)

        self.strategy = self.check_strategy(strategy_config, MeanReversionConfigs)
        self.mean_period, self.spread_mean_period, self.spread_sdev_period, self.threshold, self.ma_kind = \
            self.__set_strategy_configs(self.strategy)
        self.upper_threshold = abs(self.threshold)
        self.lower_threshold = -abs(self.threshold)

    def __set_strategy_configs(
            self,
            strategy: Optional[Union[object, MeanReversionConfigs]]) -> Tuple[int, int, int, float, MAType]:
        try:
            mean_period = int(strategy.mean_period)
            spread_mean_period = int(strategy.spread_mean_period)
            spread_sdev_period = int(strategy.spread_sdev_period)
            threshold = float(strategy.threshold)
            ma_kind = self.__select_ma_type(strategy.ma_kind)
            
            return mean_period, spread_mean_period, spread_sdev_period, threshold, ma_kind 
        except Exception as e:
            print(f"Invalid config file. Setting Defaults. Exception: {e}")
            return self.get_default_strategy_config_values(MeanReversionConfigs)

    @staticmethod 
    def __select_ma_type(kind: Union[str, MAType]) -> MAType:

        if isinstance(kind, MAType):
            return kind 
        if kind == MAType.SIMPLE.name:
            return MAType.SIMPLE 
        if kind == MAType.EXPONENTIAL.name:
            return MAType.EXPONENTIAL 
        else:
            raise ValueError(f"Incorrect value for MA Type. Use: SIMPLE or EXPONENTIAL. Input: {kind}")
    
    def __ma(self, data: pd.Series, length: int) -> pd.Series:

        if self.ma_kind == MAType.SIMPLE:
            return data.rolling(length).mean()
        if self.ma_kind == MAType.EXPONENTIAL:
            return data.ewm(span=length).mean()
    
    def attach_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        
        data['mean'] = self.__ma(data=data['Close'], length=self.mean_period)
        data['spread'] = data['Close'] - data['mean']
        data['spread_mean'] = self.__ma(data=data['spread'], length=self.spread_mean_period)
        data['spread_sdev'] = data['spread'].rolling(self.spread_sdev_period).std()
        data['z_score'] = (data['spread'] - data['spread_mean']) / data['spread_sdev']

        data['calculated_side'] = 0 
        long_signal = data['z_score'] <= self.lower_threshold 
        short_signal = data['z_score'] >= self.upper_threshold 
        data.loc[long_signal, 'calculated_side'] = int(Side.BUY.value)
        data.loc[short_signal, 'calculated_side'] = int(Side.SELL.value)

        return data 

    def get_side(self, calc_side: int) -> Side:
        if calc_side == 1:
            return Side.BUY
        if calc_side == -1:
            return Side.SELL
        return Side.NEUTRAL
        
    def stage(self, candle: Candles) -> bool:

        candles_to_fetch = max(self.mean_period, self.spread_mean_period, self.spread_sdev_period) * 2 
        df = self.fetch(candles_to_fetch)

        df = self.attach_indicators(df)

        last = df.iloc[-1]
        z_score = last['z_score'].item()
        calculated_side = last['calculated_side'].item()
        side = self.get_side(calculated_side)
        valid = side != Side.NEUTRAL

        # General Logging 
        info = candle.info() + f" Trade Valid: {valid} RSI: {z_score:.2f}"
        self.log(info) 

        trade_result = False
        if valid: 
            self.close_all_orders() 

            trade_result = self.send_market_order(side)

        return trade_result
