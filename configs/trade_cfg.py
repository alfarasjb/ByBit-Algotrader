from dataclasses import dataclass

@dataclass 
class TradeConfig:
    symbol:str 
    interval:any 
    channel:str