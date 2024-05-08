from dataclasses import dataclass

@dataclass 
class TradeConfig:
    """
    Holds information on trading config
    """
    symbol:str # Symbol
    interval:any # Interval (See ByBit documentation for valid intervals)
    channel:str # Channel/Category (See ByBit documentation for valid values)