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
        print()
        logging.info("Running trade loop..")
        print()
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
        # ----- CONSTANTS (TEMP) ----- # 
        STRATS_CFG = os.path.join('strategies','strategies.ini')

        # ----- Initialize list of available strategies in strategies/strategies.ini ----- # 
        self.strategies_kv = generic.cfg_as_dict(STRATS_CFG) 
        self.available_strategies = list(self.strategies_kv.keys())
        print(self.strategies_kv)
        

    def select_strategy(self) -> list: 
        """
        Selects strategy from list of available strategies in the strategies.ini configuration file. 

        Configuration file must be formatted as `<strategy_name>=<class_name>`, to be parsed by the `cfg_as_dict()` function 

        Strategy logic must be contained in `strategies/<strategy_name>/<strategy_name>.py`
        """
        print("Make sure to add your strategy logic in the strategies directory, and add key-value pair in strategies/strategies.ini")
        print(f"Strategy options will not be displayed if installation is misconfigured")
        # Select strategy here 
        strategies_directory = 'strategies'
        contents = self.available_strategies

        paths=dict()
        # files to exclude
        exclude = ['base']
        for c in contents:
            path = os.path.join(strategies_directory, c)

            if not os.path.isdir(path):
                # Excludes strategy key if directory does not exist. 
                continue
            if path.__contains__('__'):
                continue
            if c in exclude:
                continue
            paths[c] = path
        
        selected_strategy = generic.get_string_value(
            source="Strategy",
            default=1,
            valid_values=list(paths.keys()),
            show_exit=False,
            use_str_input=False
        )

        #paths[value] = strategies\<strategy> 
        #value = <strategy>
        
        strategy_path = paths[selected_strategy]
        module_name = self.strategies_kv[selected_strategy]
        
        
        
        print(f"Selected Strategy: {selected_strategy}")
        print(f"Module Name: {module_name}")
        print(f"Path: {strategy_path}")

        return strategy_path, selected_strategy
    
    def select_strategy_config(self, directory:str=None) -> str:
        """
        Selects strategy configuration given a strategy directory, and returns selected configuration to be loaded as dictionary, 
        and unpacked into strategy arguments. 

        Strategy configuration files are found in `strategies/<strategy_name>/cfg`

        Parameters
        ----------
            directory:str=None
                Strategy directory in which config directory and files are found. 
                `strategies/<strategy_name>` 
        """

        config_folder = 'cfg'

        configs_directory = os.path.join(directory, config_folder) # strategies\<strategy_name>\cfg
        
        if not os.path.isdir(configs_directory):
            print(f"Error. {configs_directory} does not exist.")
            return None 
        
        # Receives list of configuration files in config directory 
        contents = generic.get_configuration_files(configs_directory)
        if contents is None:
            return None

        # Receives string value for config given a list of configuration files
        selected_config = generic.get_string_value(
            source="Strategy Config",
            default=1,
            valid_values=contents, 
            show_exit=False, 
            use_str_input=False
        )
        config_path = os.path.join(configs_directory, selected_config)

        print(f"Selected Config: {selected_config}")
        print(f"Path: {config_path}")
        print()

        return config_path
    
    
    

    def load_module(self, key:str=None):
        """
        Loads a strategy given a strategy key. Refer to strategies.ini for keys. 

        Parameters
        ----------
            key:str = None 
                Contains the strategy key specified in strategies.ini
        """ 
        module = generic.load_module(
            target_module="strategies",
            filename=key,
            class_name=self.strategies_kv[key]
        )
        
        return module 
    
    def get_config_dict(self, directory:str) -> dict: 
        """
        Converts a strategy configuration file as dictionary, to be unpacked as class arguments. 

        Parameters
        ----------
            directory: str
                Contains the directory of the selected strategy 
                `strategies/<strategy_name>`
        """
        
        config_path = self.select_strategy_config(directory)
        if config_path is None: 
            return None
        cfg = generic.cfg_as_dict(config_path)

        return cfg


                
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
    directory, strat_key = root.select_strategy()
    
    # Loads the user selected module using a strategy key, found in strategies.ini
    module = root.load_module(strat_key)

    # ----- Sets Strategy Configuration ----- # 
    config_dict = root.get_config_dict(directory)

    # ----- Sets Trade Configuration ----- #
    trade_config = configs.TradeConfig(symbol="BTCUSDT", interval=1, channel='linear')

    # Loads selected module
    strategy = module(
        config=trade_config, 
        strategy_config=config_dict
    )

    # ----- Creates instance of trade object ----- # 
    trade = TradeMain(
        config=trade_config,
        callback=strategy.stage        
    )

    # ----- Runs trading operations ----- # 
    print()
    inp = input("Press any key to begin trade loop, press 0 to exit. ")
    try:
        if int(inp) == 0:
            sys.exit(0)
    except Exception as e:
        print(e)
    
    trade.run()


    while True:
        if keyboard.read_key() == 'esc':
            #trade.terminate()
            pass
