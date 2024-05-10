
from templates import * 
from configs import *
import pandas as pd 
from enum import Enum
from ..base import *
from dataclasses import dataclass



@dataclass 
class MeanReversionConfigs: 
    mean_period:int=20 # Rolling mean to measure spread
    spread_mean_period:int=10 # Rolling spread mean to calculate Rolling z-score 
    spread_sdev_period:int=10 # Rolling spread standard deviation to calculate Rolling z-score
    threshold:float=1.0 # Thresholds for buy and sell signals 
    ma_kind:MAType=MAType.SIMPLE # Moving average type 


class MeanReversion(Strategy):
    def __init__(
            self,
            config:TradeConfig, 
            strategy_config:dict
        ):
        super().__init__("Mean Reversion", config)


        self.strategy=self.check_strategy(strategy_config, MeanReversionConfigs)
        

    def __set_strategy_configs(self, strategy:MeanReversionConfigs): 
        try:
            pass
        except:
            pass 
            

    @staticmethod 
    def __select_ma_type(kind:str) -> MAType: 

        if isinstance(kind, MAType):
            return kind 
        if kind == MAType.SIMPLE.name:
            return MAType.SIMPLE 
        if kind == MAType.EXPONENTIAL.name:
            return MAType.EXPONENTIAL 
        else:
            raise ValueError(f"Incorrect value for MA Type. Use: SIMPLE or EXPONENTIAL. Input: {kind}")
    

    def stage(self, candles:Candles):
        
        pass 