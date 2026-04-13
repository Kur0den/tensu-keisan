YAOCHUUHAI = frozenset(["1m","9m","1p","9p","1s","9s","東","南","西","北","白","發","中"])
SANGENPAI = frozenset(["白","發","中"])
WINDS = frozenset(["東","南","西","北"])
WIND_ORDER = ["東","南","西","北"]
WIND_TO_TILE = {"east": "東", "south": "南", "west": "西", "north": "北"}
GREEN_TILES = frozenset(["2s","3s","4s","6s","8s","發"])
KOKUSHI_TILES = ["1m","9m","1p","9p","1s","9s","東","南","西","北","白","發","中"]


RED_DORA_TILES = frozenset(["r5m", "r5p", "r5s"])


def normalize_tile(tile: str) -> str:
    """赤ドラ表記（r5m等）を通常の牌表記（5m等）に変換する"""
    if tile in RED_DORA_TILES:
        return tile[1:]  # "r5m" → "5m"
    return tile


def is_red_dora(tile: str) -> bool:
    return tile in RED_DORA_TILES


def normalize_tiles(tiles: list) -> list:
    return [normalize_tile(t) for t in tiles]


def is_jihai(tile: str) -> bool:
    return tile in WINDS | SANGENPAI


def is_yaochuuhai(tile: str) -> bool:
    return tile in YAOCHUUHAI


def is_chunchanpai(tile: str) -> bool:
    return not is_yaochuuhai(tile)


def get_suit(tile: str) -> str:
    return tile[-1] if tile[-1] in "mps" else "z"


def get_number(tile: str):
    return int(tile[0]) if tile[-1] in "mps" else None


def sort_tiles(tiles: list) -> list:
    suit_order = {"m": 0, "p": 1, "s": 2}
    honor_order = {"東": 0, "南": 1, "西": 2, "北": 3, "白": 4, "發": 5, "中": 6}

    def key(t):
        if t[-1] in "mps":
            return (suit_order[t[-1]], int(t[0]))
        return (3, honor_order.get(t, 99))

    return sorted(tiles, key=key)


def dora_from_indicator(indicator: str) -> str:
    if indicator[-1] in "mps":
        num = int(indicator[0])
        suit = indicator[-1]
        return f"{(num % 9) + 1}{suit}"
    elif indicator in WIND_ORDER:
        idx = WIND_ORDER.index(indicator)
        return WIND_ORDER[(idx + 1) % 4]
    elif indicator == "白":
        return "發"
    elif indicator == "發":
        return "中"
    elif indicator == "中":
        return "白"
    return indicator
