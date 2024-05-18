"""
Registering a strategy: Allows the strategy to be selected by the user on the root screen

1. Create a directory in the `strategies` folder. Path: strategies/<strategy_name> 
    Example: strategies/mean_reversion 

2. Within the strategy folder, create the python file. Path: strategies/<strategy_name>/<strategy_name>.py 
    Note: strategy filename and folder must be the same. 
    Example: strategies/mean_reversion/mean_reversion.py 

3. Register strategy name in strategies/strategies.ini in the ff. format: <strategy_name>=<class_name> 
    Example: mean_reversion=MeanReversion 

4. Register strategy configuration files in a cfg folder. Path: strategies/<strategy_name>/cfg/ 
    Example: strategies/mean_reversion/cfg/

5. Strategy configuration files are structured in the ff. format: <property>=<value>.
    Example: mean_period=10 

6. Import the strategy in this __init__.py file. 

    
Creating a Strategy File: 

Required Elements: 
1. Strategy Configs dataclass - contains necessary properties for processing data (indicator values, etc)
2. Strategy Logic Class - contains main logic and execution, inherits from Strategy and Configs base class. 
    Strategy - Holds methods for sending orders 
    Configs - Holds methods for processing and validating strategy configuration


Strategy Logic:
Required Parameters:
1. TradeConfig - contains connection config (symbol, timeframe, channel)
2. StrategyConfig - contains strategy configuration processed from selected .ini file. This will be unpacked (dictionary unpacking) into the 
    previously specified Strategy Configs dataclass. 

Required Functions:
1. Stage - contains main logic processing, and trade execution (sending orders) on valid trade logic (depending on each strategy)
2. Backtest - generates a backtest of the strategy from the most recent data from ByBit
"""

# Note: Do not remove this
from .ma_cross.ma_cross import *
from .bbands.bbands import * 
from .mean_reversion.mean_reversion import * 
from .rsi.rsi import *
from .risk_premia.risk_premia import *
from .demo_strategy.demo_strategy import *