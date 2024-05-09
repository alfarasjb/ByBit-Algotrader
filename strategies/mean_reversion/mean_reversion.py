
from templates import * 
from configs import *
import pandas as pd 
from enum import Enum
from ..base import *
from dataclasses import dataclass

class MeanReversion(Strategy):
    def __init__(
            self,
            config:TradeConfig, 
            strategy_config:dict
        ):
        super().__init__("Mean Reversion", config)

    def stage(self, candles:Candles):
        print(candles.symbol)