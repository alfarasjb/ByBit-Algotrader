

class Configs:

    def __init__(self):
        pass

    def check_strategy(self, strategy_config:dict, strategy:any): 
        """
        Attempts to unpack the strategy configuration from .ini file, into config dataclass. 

        Sets the default values if strategy_config is None (when no config files are found in the config directory)
        """

        if strategy_config is None: 
             print(f"No strategy config found for {self.name}. Using defaults.")
             return strategy
        # Unppack Config
        return strategy(**strategy_config)
        