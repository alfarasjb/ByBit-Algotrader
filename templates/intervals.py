
from enum import Enum 


class Timeframes(Enum): 
    MIN_1 = 1 
    MIN_3 = 3 
    MIN_5 = 5
    MIN_15 = 15
    MIN_30 = 30 
    D_1 = "D"
    W_1 = "W"
    MN_1 = "M"

    @staticmethod
    def available_timeframes():
        return [t.name for t in Timeframes]
