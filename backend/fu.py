from tiles import is_yaochuuhai, is_jihai, get_number, SANGENPAI, WIND_TO_TILE


def calculate_fu(pattern: dict, special_type, melds: list, win_tile: str, win_type: str, context) -> int:
    if special_type == "chiitoi":
        return 25
    if special_type == "kokushi":
        return 30

    jantai = pattern["jantai"]
    mentsu_list = pattern["mentsu"]
    # 暗槓は門前扱い（チー・ポン・明槓があるときのみ open）
    is_open = any(m["type"] in ("chi", "pon", "minkan") for m in melds)

    seat_wind = WIND_TO_TILE.get(context.seat_wind, "東")
    round_wind = WIND_TO_TILE.get(context.round_wind, "東")

    # 平和チェック
    all_shuntsu = all(m["type"] == "shuntsu" for m in mentsu_list)
    jantai_not_yakuhai = (
        jantai not in SANGENPAI
        and jantai != seat_wind
        and jantai != round_wind
    )
    wait_type = _get_wait_type(pattern, win_tile)
    is_pinfu = not is_open and all_shuntsu and jantai_not_yakuhai and wait_type == "ryanmen"

    if is_pinfu:
        return 20 if win_type == "tsumo" else 30

    # 基本符
    base_fu = 20 if is_open else 30

    # 面子符（手牌の暗面子）
    mentsu_fu = sum(_calc_mentsu_fu(m, win_tile, win_type, is_concealed=True) for m in mentsu_list)

    # 面子符（副露）
    for meld in melds:
        is_kan = meld["type"] in ("minkan", "ankan")
        is_concealed = meld["type"] == "ankan"   # 暗槓は暗刻扱い
        m = {"type": "shuntsu" if meld["type"] == "chi" else "koutsu", "tiles": meld["tiles"], "is_kan": is_kan}
        mentsu_fu += _calc_mentsu_fu(m, win_tile, win_type, is_concealed=is_concealed)

    # 雀頭符
    jantai_fu = 0
    if jantai in SANGENPAI:
        jantai_fu = 2
    elif jantai == seat_wind and jantai == round_wind:
        jantai_fu = 4
    elif jantai == seat_wind or jantai == round_wind:
        jantai_fu = 2

    # 待ち符
    wait_fu = 2 if wait_type in ("kanchan", "penchan", "tanki") else 0

    # ツモ符
    tsumo_fu = 2 if win_type == "tsumo" else 0

    total = base_fu + mentsu_fu + jantai_fu + wait_fu + tsumo_fu
    return ((total + 9) // 10) * 10


def _calc_mentsu_fu(m: dict, win_tile: str, win_type: str, is_concealed: bool) -> int:
    if m["type"] == "shuntsu":
        return 0

    tile = m["tiles"][0]
    is_yaochua = is_yaochuuhai(tile)
    is_kan = m.get("is_kan", False)

    # ロン和了で手牌の刻子に当たり牌が含まれる場合は明刻扱い
    if is_concealed and win_tile == tile and win_type == "ron" and not is_kan:
        is_concealed = False

    if is_concealed:
        base = 8 if is_yaochua else 4
    else:
        base = 4 if is_yaochua else 2

    if is_kan:
        base *= 4

    return base


def _get_wait_type(pattern: dict, win_tile: str) -> str:
    jantai = pattern["jantai"]
    mentsu_list = pattern["mentsu"]

    if win_tile == jantai:
        return "tanki"

    for m in mentsu_list:
        if win_tile not in m["tiles"]:
            continue
        if m["type"] == "koutsu":
            return "shanpon"
        # 順子: 待ちの種類を判定
        nums = sorted(int(t[0]) for t in m["tiles"])
        win_num = int(win_tile[0])
        if win_num == nums[1]:
            return "kanchan"
        if win_num == nums[0]:
            return "penchan" if nums[2] == 9 else "ryanmen"
        if win_num == nums[2]:
            return "penchan" if nums[0] == 1 else "ryanmen"

    return "tanki"
