from dataclasses import dataclass 


@dataclass 
class Candles:
    symbol:str 
    start: int 
    end: int 
    interval: str 
    open: float 
    close: float 
    high: float 
    low: float 
    volume: float 
    turnover: float 
    confirm: bool 
    timestamp: int 

    def info(self):
        message = f"{self.symbol} Open: {self.open} High: {self.high} Low: {self.low} Close: {self.close} Volume: {self.volume}"
        return message


