from enum import Enum 


class Side(Enum): 
    """
    Enum for holding Side 

    1 - Long Position
    -1 - Short Position
    0 - Neutral
    
    """
    BUY = 1
    SELL = -1 
    NEUTRAL = 0 