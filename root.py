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
        
        
        if candles.confirm and self.running:
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
        #try:
        self.ws.kline_stream(
            interval=self.config.interval, 
            symbol=self.config.symbol, 
            callback=self.handler
        )
        
        # Main member variable to determine callback execution 
        self.running = True
        
        
    def terminate(self):
        """
        Ends connection with WebSocket. Triggered by keyboard input.

        Issue 1: 
            Thread from websocket throws an error (WebSocketConnectionClosed), but does not hinder functionality 

            Cause: `_send_initial_ping()` and `_send_custom_ping()` 

            Solution(Temporary): Modify Timer variable in `_send_custom_ping()` as class member variable (self.timer), and kill the 
            thread manually to silence the Exception. Also throws the same exception if `self.ws.exit()` is called prior to killing 
            the thread. Solution: kill the thread first, then exit. 

        Issue 2: 
            Callback function still executes after killing the timer thread and exit. 

            Solution(Temporary): Created a class member variable: `self.running` to determine if termination method is called, or if 
            subsription to WS is called. Is set to false when termination function is called, sets to true if subscription function 
            is called. 
        """
        logging.info("Terminating WebSocket Connection..")
        
        # Sets to false if termination is called, to disable on_new_candle function. See `handler()` method. 
        self.running = False

        # Note: Do not change the order 
        # Kill the thread first before calling exit. Reversing the order throws an exception
        self.ws.timer.join()
        self.ws.exit()
        logging.info("Connection Ended.")

class Root:
    """
    This module is the root class, and handles user interactions, setting configuration files, and other settings. 
    """
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



def main(): 
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
    try: 
        module = root.load_module(strat_key)
    except AttributeError: 
        print(f"Module {strat_key} not found. Make sure to add the strategy in the __init__.py file.")
        return main()
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

    # Check for presence of backtest function 
    try: 
        bt_func = strategy.backtest
    except AttributeError:
        print(f"Error. Backtest Function does not exist for: {strategy.name}")
        return main()

    # ----- Runs trading operations ----- # 
    while True:
        print()
        options = {
            "Exit" : sys.exit,
            "Execute" : trade.run, 
            "Backtest" : strategy.backtest, 
        }
        for i, j in enumerate(options.keys()):
            print(f"{i}. {j}")
            
        inp = input("Select Option: ")
        try:
            index = int(inp)
            key = list(options.keys())[index]

            # Run Function
            options[key]() 
            if key == "Execute":
                break
        except ValueError: 
            print("Invalid selection. Use index.")
            

    return trade



                
if __name__ == "__main__": 
    
    trade = main()


    while True:
        if keyboard.read_key() == 'esc':
            trade.terminate()
            trade = main()