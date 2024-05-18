from dataclasses import dataclass 


@dataclass
class TradeResult:
    code: int
    order_id: str  # temporary
    timestamp: int  # unix time
