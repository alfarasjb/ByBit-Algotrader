"""
Contains methods for working with strategy configuration files
"""
from typing import Dict, Optional, Any, Callable, List, Tuple, Union
from dataclasses import dataclass


class Configs:

    @staticmethod
    def check_strategy(strategy_config: Dict, strategy: dataclass) -> Optional[object]:
        # Revisit this method in the future for corrections on `typing`.
        """
        Attempts to unpack the strategy configuration from .ini file, into config dataclass. 

        Sets the default values if strategy_config is None (when no config files are found in the config directory)
        """

        if strategy_config is None: 
            print(f"No strategy config found. Using defaults.")
            return strategy
        # Unpack Config
        return strategy(**strategy_config)

    @staticmethod 
    def get_default_strategy_config_values(strategy: type) -> Union[Tuple[Any], Any]:
        """
        Returns default values of a strategy configuration as a list. 

        This is called when errors are raised while parsing input parameters from .ini file. 
        """
        return tuple(strategy().__dict__.values())
