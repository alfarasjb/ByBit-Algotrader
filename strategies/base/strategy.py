from templates import * 
from configs import *
import logging 

from pybit.unified_trading import HTTP 

_log = logging.getLogger(__name__)



class Strategy:

    def __init__(self, name:str, config:TradeConfig):
        # -------------------- Initializing member variables -------------------- #  
        # Strategy Name 
        self.name = name

        # Trading Configuration  
        self.trade_config = config

        # Session  
        self.session = HTTP(testnet=True)


    def log(self, message:str) -> None: 
        # Strategy Logger
        if not isinstance(message, str):
            return None 
        
        _log.info(f"{self.trade_config.symbol} - {message}") 
        

    def info(self) -> None:
        # Prints symbol info 
        self.log(f"Instrument Configuration - Symbol: {self.trade_config.symbol} Interval: {self.trade_config.interval} Channel: {self.trade_config.channel}")

        

    def send_market_order(self, side:Side) -> bool:
        # Sends market order 
        print(f"Send Market Order. Side: {side.name}") 
        return True
        
    def close_opposite_order(self, side:Side) -> None:
        # Closes order opposite to specified order type
        print(f"Close Opposite Order of: {side.name}")
        
    def close_all_orders(self) -> None:
        # Closes all orders 
        print(f"Close All Orders")
