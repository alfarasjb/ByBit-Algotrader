from templates import * 
from configs import *
import logging 
import os 

from pybit.unified_trading import HTTP 

_log = logging.getLogger(__name__)


from dataclasses import dataclass 

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
        self.params = RiskParams(
            quantity=10, 
            take_profit=0.012, 
            stop_loss=0.009, 
            leverage=10
        )

    def calculate(self, mark_price:float, side:Side):
        # Calculate SL TP 
        digits = 2 # Temporary
        if side == Side.LONG: 
            tp_price = round(mark_price + (mark_price*self.params.take_profit), digits)
            sl_price = round(mark_price - (mark_price*self.params.stop_loss), digits)
            return tp_price, sl_price 
        if side == Side.SHORT:
            tp_price = round(mark_price - (mark_price*self.params.take_profit), digits)
            sl_price = round(mark_price + (mark_price*self.params.stop_loss), digits)
            return tp_price, sl_price
        else:
            return 0, 0


class Strategy:

    def __init__(self, name:str, config:TradeConfig):
        # -------------------- Initializing member variables -------------------- #  
        # Strategy Name 
        self.name = name

        # Trading Configuration  
        self.trade_config = config

        # Session  
        self.session = HTTP(testnet=True, api_key = os.environ['BYBIT_API'], api_secret=os.environ['BYBIT_SECRET'])


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
        mark_price = self.__get_mark_price() 
        risk = Risk()
        tp_price, sl_price = risk.calculate(mark_price, side) 

        try:
            session_side = self.__get_side(side) 
            session_order = self.__get_order_type(Order.MARKET)

            self.log(f"Sending Market Order: Symbol: {self.trade_config.symbol} Side: {session_side} Order: {session_order} Quantity: {risk.params.quantity} TP: {tp_price} SL: {sl_price}")

            trade_result = self.session.place_order(
                category=self.trade_config.channel, 
                symbol=self.trade_config.symbol,
                side=session_side, 
                orderType=session_order,
                qty=risk.params.quantity, 
                take_profit=tp_price,
                stop_loss=sl_price,
                tpTriggerBy=session_order,
                slTriggerBy=session_order
            )
            self.log(trade_result)
        except Exception as e:
            self.log(f"Order Send Failed. {e}")
            return False

        return True
        
    def close_opposite_order(self, side:Side) -> None:
        # Closes order opposite to specified order type
        print(f"Close Opposite Order of: {side.name}")
        
    def close_all_orders(self) -> None:
        # Closes all orders 
        print(f"Close All Orders")

    def __get_mark_price(self): 
        
        mark_price = self.session.get_tickers(
            category=self.trade_config.channel, 
            symbol=self.trade_config.symbol
        )['result']['list'][0]['markPrice']

        return float(mark_price)
    
    def __get_side(self, side:Side): 
        # returns side string 
        if side == side.LONG:
            return "Buy"
        if side == side.SHORT:
            return "Sell"
        else:
            return ""

    def __get_order_type(self, order:Order):
        if order == order.MARKET:
            return "Market"
        if order == order.LIMIT:
            return "Limit"
        else: 
            return ""
