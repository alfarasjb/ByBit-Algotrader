from dataclasses import dataclass 
from templates import intervals
@dataclass 
class TradeConfig:
    """
    Holds information on trading config

    Parameters
    ----------
        symbol: str 
            Symbol 
        
        interval: str 
            Available Intervals: 
                1, 3, 5, 15, 30 (min)
                60, 120, 240, 360, 720 (min)
                D (day)
                W (week)
                M (month)
    """
    symbol:str # Symbol
    interval:intervals.Timeframes # Interval (See ByBit documentation for valid intervals)
    channel:str # Channel/Category (See ByBit documentation for valid values)

    