from templates import * 
from configs import *
import logging 
import os 
import pandas as pd
from pybit.unified_trading import HTTP 
from api_secrets import *
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
            quantity=0.001, 
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
        #self.session = HTTP(testnet=False, api_key = os.environ['BYBIT_API'], api_secret=os.environ['BYBIT_SECRET'])
        self.session = HTTP(testnet=False, api_key=api_secrets.bybit_api_demo, api_secret=api_secrets.bybit_api_secret,demo=True)

    def log(self, message:str) -> None: 
        # Strategy Logger
        if not isinstance(message, str):
            return None 
        
        _log.info(f"{self.trade_config.symbol} - {message}") 
        

    def info(self) -> None:
        # Prints symbol info 
        self.log(f"Instrument Configuration - Symbol: {self.trade_config.symbol} Interval: {self.trade_config.interval.value} Channel: {self.trade_config.channel}")

        

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
                #take_profit=tp_price,
                #stop_loss=sl_price,
                #tpTriggerBy=session_order,
                #slTriggerBy=session_order
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

    def close_all_open_positions(self) -> None: 
        # Closes all open positions 
        # Needs symbol, side
        print(f"Close All Open Positions")
        positions_to_close = self.get_open_positions()
        for p in positions_to_close: 
            side = self.__get_close_side(p.side)
            symbol=p.symbol
            qty=p.size 
            print(f"Closing {symbol} {p.side} {qty}")
            
            trade_result = self.session.place_order(
                category=self.trade_config.channel, 
                symbol=symbol, 
                side=side,
                orderType=Order.MARKET.name.title(), 
                qty=qty
            )





    def get_open_positions(self) -> list: 
        # Needs: Symbol, side
        
        positions = self.session.get_positions(
            category=self.trade_config.channel, 
            symbol=self.trade_config.symbol
        )['result']['list']
        
        # convert to list of type Positions 
        positions_to_close = list()
        for p in positions: 
            symbol=p['symbol']
            side = p['side']
            qty=p['size']
            
            if float(qty) == 0:
                continue
            position = Position(symbol, side, qty)
            
            positions_to_close.append(position)

        return positions_to_close 
    
    
    
    @staticmethod
    def __get_close_side(side:str):
        if side == "Buy":
            return "Sell"
        if side == "Sell":
            return "Buy"

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
            return "Sell"

    def __get_order_type(self, order:Order):
        if order == order.MARKET:
            return "Market"
        if order == order.LIMIT:
            return "Limit"
        else: 
            return ""

    def fetch(self, elements:int) -> pd.DataFrame: 
        """
        Fetches data from ByBit 

        """

        response = None 
        try: 
            response = self.session.get_kline(
                category=self.trade_config.channel, 
                symbol=self.trade_config.symbol,
                interval=self.trade_config.interval.value,
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
    

    def valid_columns(self, data:pd.DataFrame, columns:list) -> bool: 
        
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Invalid type. Expecting DataFrame")
        
        for d in data.columns:
            if d not in columns:
                return False 
            
        return True
    

    def get_side(self, calc_side:int) -> Side: 
        if calc_side == 1:
            return Side.LONG 
        if calc_side == -1:
            return Side.SHORT 
        return Side.NEUTRAL
        