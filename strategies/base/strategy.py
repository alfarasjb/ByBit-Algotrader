"""
This module contains the Strategy base class, which contains functions on order execution, 
as well as other generic functions required by strategies. 
"""
import logging
import pandas as pd
from pybit.unified_trading import HTTP
from typing import List, Optional

from configs.trade_cfg import TradeConfig
from api_secrets import api_secrets
from .risk import Risk
from templates import Side, Order, Position

_log = logging.getLogger(__name__)


class Strategy:

    def __init__(self, name: str, config: TradeConfig):
        # -------------------- Initializing member variables -------------------- #  
        # Strategy Name 
        self.name = name

        # Trading Configuration  
        self.trade_config = config

        # Session  

        self.session = HTTP(
            testnet=False,
            api_key=api_secrets.bybit_api_demo,
            api_secret=api_secrets.bybit_api_secret,
            demo=True)

    def log(self, message: str) -> None:
        # Strategy Logger
        if not isinstance(message, str):
            return None 
        
        _log.info(f"{self.trade_config.symbol} - {message}") 

    def info(self) -> None:
        # Prints symbol info 
        self.log(f"Instrument Configuration - Symbol: {self.trade_config.symbol}\
            Interval: {self.trade_config.interval.value} Channel: {self.trade_config.channel}")

    def send_market_order(self, side: Side) -> bool:
        # Sends market order 
        mark_price = self.__get_mark_price() 
        risk = Risk()
        tp_price, sl_price = risk.calculate(mark_price, side) 

        try:
            session_side = side.name.title()
            session_order = self.__get_order_type(Order.MARKET)

            self.log(f"Sending Market Order: Symbol: {self.trade_config.symbol} Side: {session_side} Order: \
                {session_order} Quantity: {risk.params.quantity} TP: {tp_price} SL: {sl_price}")

            trade_result = self.session.place_order(
                category=self.trade_config.channel, 
                symbol=self.trade_config.symbol,
                side=session_side, 
                orderType=session_order,
                qty=risk.params.quantity, 
                take_profit=str(tp_price),
                stop_loss=str(sl_price),
            )
            self.log(trade_result)
            
            if int(trade_result['retCode']) == 0: 
                self.log(f"Order Send Successful. ID: {trade_result['result']['orderId']}")

        except Exception as e:
            self.log(f"Order Send Failed. {e}")
            return False
        
        return True

    def close_opposite_order(self, side: Side) -> None:
        # Closes order opposite to specified order type
        print(f"Close Opposite Order of: {side.name}")

    def close_all_orders(self) -> None:
        # Closes all orders 
        print(f"Close All Orders")

    def close_all_open_positions(self) -> None: 
        # Closes all open positions 
        # Needs symbol, side
        positions_to_close = self.get_open_positions() 
        for p in positions_to_close: 
            side = self.__get_close_side(p.side)
            symbol = p.symbol
            qty = p.size
            
            trade_result = self.session.place_order(
                category=self.trade_config.channel,
                symbol=symbol,
                side=side,
                orderType=Order.MARKET.name.title(),
                qty=qty
            )

    def get_open_positions(self) -> List[Position]:
        # Needs: Symbol, side
        
        positions = self.session.get_positions(
            category=self.trade_config.channel, 
            symbol=self.trade_config.symbol
        )['result']['list']
        
        # convert to list of type Positions 
        open_positions = list()
        for p in positions:
            if float(p['size']) == 0:
                continue 
            
            open_positions.append(Position(
                symbol=p['symbol'],
                side=p['side'],
                size=p['size']
            ))

        return open_positions 

    @staticmethod
    def __get_close_side(side: str) -> str:
        if side == Side.BUY.name.title():
            return Side.SELL.name.title() 
        if side == Side.SELL.name.title():
            return Side.BUY.name.title() 

    def __get_mark_price(self) -> float:
        
        mark_price = self.session.get_tickers(
            category=self.trade_config.channel, 
            symbol=self.trade_config.symbol
        )['result']['list'][0]['markPrice']

        return float(mark_price)

    @staticmethod
    def __get_order_type(order: Order) -> str:
        if order == order.MARKET:
            return "Market"
        if order == order.LIMIT:
            return "Limit"
        else: 
            return ""

    def fetch(self, elements: int) -> Optional[pd.DataFrame]:
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
        df = df.set_index('Time', drop=True)
        # convert timestamp to datetime
        df.index = pd.to_datetime(df.index.astype('int64'), unit='ms')
        # sets values to float 
        df = df.astype(float)
        # inverts the dataframe 
        df = df[::-1] 
        # excludes last row since this is fresh candle, and is still open 
        df = df[:-1]  
        
        return df 

    @staticmethod
    def valid_columns(data: pd.DataFrame, columns: list) -> bool:
        
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Invalid type. Expecting DataFrame")
        
        for d in data.columns:
            if d not in columns:
                return False 
            
        return True

    @staticmethod
    def get_side(calc_side: int) -> Side:
        if calc_side == 1:
            return Side.BUY 
        if calc_side == -1:
            return Side.SELL 
        return Side.NEUTRAL
        