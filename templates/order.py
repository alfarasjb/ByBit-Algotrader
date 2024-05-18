from enum import Enum 


class Order(Enum):
    """
    Enum for holding Order Types 

    1. Market Order
    2. Limit Order
    """
    MARKET = 1 
    LIMIT = 2
