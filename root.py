from pybit.unified_trading import WebSocket, HTTP 

from time import sleep 
import configs 
import templates
import strategies

import logging 


class TradeMain:

    def __init__(self, config:configs.TradeConfig, callback):

        # -------------------- Initializing member variables -------------------- #  
        self.config = config 
        self.ws = WebSocket(testnet=True, channel_type=config.channel)
        self.callback = callback 


    def handler(self, contents:dict) -> None:
        """
        Handler for ByBit Websocket 

        Runs new candle callback 

        Parameters
        ----------
            contents: dict 
                received contents from bybit
        """
        data = contents['data'][0]
        candles = templates.Candles(self.config.symbol, **data)
        
        if candles.confirm:
            # New candle event handler 
            self.on_new_candle(candles)

    def on_new_candle(self, candle:templates.Candles) -> None: 
        """
        Calls the strategy stage function

        Parameters
        ----------
            candle: templates.Candles
                latest ticker information
        """
        # Callback function is the Stage function from each strategy 
        self.callback(candle)
        

    def run(self): 
        """
        Subscribes to Kline Stream 
        """
        self.ws.kline_stream(
            interval=self.config.interval, 
            symbol=self.config.symbol, 
            callback=self.handler
        )


if __name__ == "__main__": 

    # ----- Initialization ----- # 
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format = format, level = logging.INFO, datefmt="%H:%M:%S")
    logging.info(" ==========================================  ")
    logging.info(" ======= Launching ByBit-Algotrader ======= ")
    logging.info(" ==========================================  ")

    # ----- Sets Trade Configuration ----- #
    trade_config = configs.TradeConfig(symbol="BTCUSDT", interval=1, channel='linear')
    
    # ----- Calls a strategy ----- # 
    strategy = strategies.MACross(
        trade_config,
        fast_ma_period=20, 
        slow_ma_period=100,
        ma_kind=strategies.MAType.SIMPLE
    ) 

    # ----- Creates instance of trade object ----- # 
    trade = TradeMain(
        config=trade_config,
        callback=strategy.stage        
    )

    # ----- Runs trading operations ----- # 
    trade.run()

    while True:
        sleep(1)