from pydantic import BaseModel
from typing import List, Optional, Literal


class Meld(BaseModel):
    type: Literal["chi", "pon", "kan"]
    tiles: List[str]


class Hand(BaseModel):
    closed: List[str]
    melds: List[Meld] = []


class Context(BaseModel):
    seat_wind: Literal["east", "south", "west", "north"] = "east"
    round_wind: Literal["east", "south", "west", "north"] = "east"
    is_riichi: bool = False
    is_ippatsu: bool = False
    is_rinshan: bool = False
    is_chankan: bool = False
    is_haitei: bool = False
    is_houtei: bool = False
    dora: List[str] = []
    ura_dora: List[str] = []


class CalculateRequest(BaseModel):
    hand: Hand
    win_tile: str
    win_type: Literal["tsumo", "ron"]
    context: Context = Context()


class YakuResult(BaseModel):
    name: str
    han_closed: int
    han_open: int
    is_yakuman: bool


class Payment(BaseModel):
    tsumo_dealer: int = 0
    tsumo_non_dealer: int = 0
    ron: int = 0


class ScoreResult(BaseModel):
    basic_points: int
    payment: Payment


class CalculateResponse(BaseModel):
    is_agari: bool
    yaku: Optional[List[YakuResult]] = None
    han_total: Optional[int] = None
    fu_total: Optional[int] = None
    score: Optional[ScoreResult] = None
    error: Optional[str] = None
