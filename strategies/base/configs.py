"""
Contains methods for working with strategy configuration files
"""

class Configs:
    
    def check_strategy(self, strategy_config:dict, strategy:object): 
        """
        Attempts to unpack the strategy configuration from .ini file, into config dataclass. 

        Sets the default values if strategy_config is None (when no config files are found in the config directory)
        """

        if strategy_config is None: 
             print(f"No strategy config found for {self.name}. Using defaults.")
             return strategy
        # Unppack Config
        return strategy(**strategy_config)
        
        
    @staticmethod 
    def get_default_strategy_config_values(strategy:object) -> list:
        """
        Returns default values of a strategy configuration as a list. 

        This is called when errors are raised while parsing input parameters from .ini file. 
        """
        return list(strategy().__dict__.values())