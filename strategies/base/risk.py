
from dataclasses import dataclass
from typing import Tuple

from templates import Side

# Temporary. Migrate to Templates in the future 
# Load config from .ini 
@dataclass 
class RiskParams:
    quantity:int 
    take_profit:float 
    stop_loss:float 
    leverage:int 

class Risk: 

    def __init__(self):
        # Temporary
        self.params = RiskParams(
            quantity=0.001, 
            take_profit=0.012, 
            stop_loss=0.009, 
            leverage=10
        )

    def calculate(self, mark_price:float, side:Side) -> Tuple[float, float]:
        # Calculate SL TP 
        digits = 2 # Temporary
        if side == Side.BUY: 
            tp_price = round(mark_price + (mark_price*self.params.take_profit), digits)
            sl_price = round(mark_price - (mark_price*self.params.stop_loss), digits)
            return tp_price, sl_price 
        if side == Side.SELL:
            tp_price = round(mark_price - (mark_price*self.params.take_profit), digits)
            sl_price = round(mark_price + (mark_price*self.params.stop_loss), digits)
            return tp_price, sl_price
        else:
            return 0.0, 0.0
