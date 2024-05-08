from pybit.unified_trading import WebSocket, HTTP 
from time import sleep 
import configs 
import templates
import strategies
import keyboard
import generic 

import logging 
import sys, os 

class TradeMain:
    """ 
    Main execution class. 

    Handles websocket connection and data from ByBit.

    Triggers candle interval events. 

    Equivalent of MQL OnTick() function. 
    """

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
                Received JSON contents from bybit
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
                Contains the latest ticker information
        """
        # Callback function is the Stage function from each strategy 
        self.callback(candle)
        

    def run(self): 
        """
        Subscribes to Kline Stream 
        """
        try:
            self.ws.kline_stream(
                interval=self.config.interval, 
                symbol=self.config.symbol, 
                callback=self.handler
            )
        except self.ws.WebSocketConnectionClosedException as e: 
            logging.info(f"WebSocket Connection has Ended. Exception: {e}")
        
    def terminate(self):
        """
        Ends connection with WebSocket. Triggered by keyboard input.
        """
        
        self.ws.exit()
        

class Root:
    ## Configuration goes here 
    def __init__(self): 
        pass 

    def select_strategy(self) -> list: 
        
        strategies_directory = 'strategies'
        contents = os.listdir(strategies_directory)
        directories=list()
        strategies=list()
        for c in contents:
            path = os.path.join(strategies_directory, c)
            if not os.path.isdir(path):
                continue
            if path.__contains__('__'):
                continue
            directories.append(path)
            strategies.append(c)
                
        return directories

    def select_strategy_config(self, directory:str=None) -> str:
        config_folder = 'cfg'
        directory = self.select_strategy()[4] if directory is None else directory 
        configs_directory = os.path.join(directory, config_folder)
        if not os.path.isdir(configs_directory):
            return None 
        
        contents = os.listdir(configs_directory) 
        selected = os.path.join(configs_directory, contents[0])
        
        return selected 
    
    def process_config_ini(self, path:str) -> dict:

        config_dict=dict()
        with open(path) as f: 
            for line in f: 
                if not line.__contains__('='):
                    continue 
                key, value = line.split('=')
                config_dict[key] = value.rstrip() 
        

        return config_dict
                
if __name__ == "__main__": 

    # ----- Initialization ----- # 
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format = format, level = logging.INFO, datefmt="%H:%M:%S")
    print()
    print(" ==========================================  ")
    print(" ======= Launching ByBit-Algotrader ======= ")
    print(" ==========================================  ")
    print()

    # ----- Creates Root App ----- #
    root = Root()

    # ----- Select Strategy ----- # 
    

    # ----- Sets Trade Configuration ----- #
    trade_config = configs.TradeConfig(symbol="BTCUSDT", interval=1, channel='linear')

    # ----- Sets Strategy Configuration ----- # 
    config_dict = root.process_config_ini(root.select_strategy_config())
    
    # ----- Calls a strategy ----- # 
    #strategy = strategies.MACross(
    #    trade_config,
    #    fast_ma_period=20, 
    #    slow_ma_period=100,
    #    ma_kind=strategies.MAType.SIMPLE
    #) 
    #strategy = strategies.MACross(
    #    config=trade_config,
    #    strategy_config=config_dict
    #)
    strategy = strategies.RSI(
        config=trade_config,
        strategy_config=config_dict
    )

    # ----- Creates instance of trade object ----- # 
    trade = TradeMain(
        config=trade_config,
        callback=strategy.stage        
    )

    # ----- Runs trading operations ----- # 
    trade.run()


    while True:
        if keyboard.read_key() == 'esc':
            #trade.terminate()
            pass
