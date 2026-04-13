from collections import Counter
from tiles import (
    SANGENPAI, WINDS, WIND_TO_TILE, GREEN_TILES,
    is_yaochuuhai, is_jihai, is_chunchanpai, get_suit, get_number,
)


def is_hand_open(melds: list) -> bool:
    """チー・ポン・明槓があれば手を開いているとみなす（暗槓は門前扱い）"""
    return any(m["type"] in ("chi", "pon", "minkan") for m in melds)


def detect_yaku(pattern: dict, special_type, melds: list, win_tile: str, win_type: str, context, all_tiles: list) -> list:
    is_closed = not is_hand_open(melds)

    if special_type == "kokushi":
        # 十三面待ち判定: 和了牌を除いた13枚が么九牌13種を各1枚ずつなら十三面待ち
        tiles_13 = list(all_tiles)
        tiles_13.remove(win_tile)
        from tiles import KOKUSHI_TILES, sort_tiles
        is_juusanmen = sort_tiles(tiles_13) == sort_tiles(KOKUSHI_TILES)
        multiplier = 2 if is_juusanmen else 1
        return [{"name": "kokushi_musou", "han_closed": 13, "han_open": 0,
                 "is_yakuman": True, "yakuman_multiplier": multiplier}]

    yaku_list = []

    if special_type == "chiitoi":
        yaku_list.append({"name": "chiitoitsu", "han_closed": 2, "han_open": 0, "is_yakuman": False})
        _add_context_yaku(yaku_list, is_closed, win_type, context)
        _add_tanyao(yaku_list, all_tiles)
        _add_honitsu_chinitsu(yaku_list, all_tiles, melds)
        return yaku_list

    # 通常形
    all_mentsu = _build_all_mentsu(pattern, melds)

    # 役満チェック（役満のみ返す）
    yakuman = _check_yakuman(pattern, all_mentsu, melds, win_tile, win_type, all_tiles, is_closed)
    if yakuman:
        return yakuman

    _add_context_yaku(yaku_list, is_closed, win_type, context)
    _add_tanyao(yaku_list, all_tiles)
    _add_pinfu(yaku_list, pattern, melds, win_tile, context, is_closed)
    _add_peiko(yaku_list, pattern["mentsu"], is_closed)
    _add_sanshoku_doujun(yaku_list, all_mentsu)
    _add_sanshoku_doukou(yaku_list, all_mentsu)
    _add_ittsu(yaku_list, all_mentsu)
    _add_chanta_junchan(yaku_list, pattern, all_mentsu)
    _add_toitoi(yaku_list, all_mentsu)
    _add_sanankou(yaku_list, pattern["mentsu"], melds, win_tile, win_type)
    _add_shousangen(yaku_list, all_mentsu, pattern["jantai"])
    _add_honroutou(yaku_list, all_tiles)
    _add_yakuhai(yaku_list, all_mentsu, context)
    _add_honitsu_chinitsu(yaku_list, all_tiles, melds)

    return yaku_list


def _build_all_mentsu(pattern: dict, melds: list) -> list:
    closed_mentsu = [dict(m, is_open=False, is_kan=False) for m in pattern["mentsu"]]
    open_mentsu = [
        {
            "type": "shuntsu" if m["type"] == "chi" else "koutsu",
            "tiles": m["tiles"],
            "is_open": m["type"] != "ankan",   # 暗槓は門前扱い
            "is_kan": m["type"] in ("minkan", "ankan"),
            "is_ankan": m["type"] == "ankan",
        }
        for m in melds
    ]
    return closed_mentsu + open_mentsu


def _add_context_yaku(yaku_list, is_closed, win_type, context):
    if context.is_riichi and is_closed:
        yaku_list.append({"name": "riichi", "han_closed": 1, "han_open": 0, "is_yakuman": False})
    if context.is_ippatsu and is_closed:
        yaku_list.append({"name": "ippatsu", "han_closed": 1, "han_open": 0, "is_yakuman": False})
    if win_type == "tsumo" and is_closed:
        yaku_list.append({"name": "menzen_tsumo", "han_closed": 1, "han_open": 0, "is_yakuman": False})
    if context.is_haitei and win_type == "tsumo":
        yaku_list.append({"name": "haitei", "han_closed": 1, "han_open": 1, "is_yakuman": False})
    if context.is_houtei and win_type == "ron":
        yaku_list.append({"name": "houtei", "han_closed": 1, "han_open": 1, "is_yakuman": False})
    if context.is_rinshan:
        yaku_list.append({"name": "rinshan_kaihou", "han_closed": 1, "han_open": 1, "is_yakuman": False})
    if context.is_chankan:
        yaku_list.append({"name": "chankan", "han_closed": 1, "han_open": 1, "is_yakuman": False})


def _add_tanyao(yaku_list, all_tiles):
    if all(is_chunchanpai(t) for t in all_tiles):
        yaku_list.append({"name": "tanyao", "han_closed": 1, "han_open": 1, "is_yakuman": False})


def _add_pinfu(yaku_list, pattern, melds, win_tile, context, is_closed):
    if not is_closed:
        return
    seat_wind = WIND_TO_TILE.get(context.seat_wind, "東")
    round_wind = WIND_TO_TILE.get(context.round_wind, "東")
    jantai = pattern["jantai"]
    mentsu_list = pattern["mentsu"]

    if not all(m["type"] == "shuntsu" for m in mentsu_list):
        return
    if jantai in SANGENPAI or jantai == seat_wind or jantai == round_wind:
        return

    wait_type = _get_wait_type(pattern, win_tile)
    if wait_type == "ryanmen":
        yaku_list.append({"name": "pinfu", "han_closed": 1, "han_open": 0, "is_yakuman": False})


def _add_peiko(yaku_list, mentsu_list, is_closed):
    if not is_closed:
        return
    shuntsu_tuples = [tuple(m["tiles"]) for m in mentsu_list if m["type"] == "shuntsu"]
    counts = Counter(shuntsu_tuples)
    pairs = sum(1 for c in counts.values() if c >= 2)
    if pairs >= 2:
        yaku_list.append({"name": "ryanpeiko", "han_closed": 3, "han_open": 0, "is_yakuman": False})
    elif pairs == 1:
        yaku_list.append({"name": "iipeiko", "han_closed": 1, "han_open": 0, "is_yakuman": False})


def _add_sanshoku_doujun(yaku_list, all_mentsu):
    shuntsu = [m for m in all_mentsu if m["type"] == "shuntsu"]
    for m in shuntsu:
        num = get_number(m["tiles"][0])
        if num is None:
            continue
        suits = {get_suit(m2["tiles"][0]) for m2 in shuntsu if get_number(m2["tiles"][0]) == num}
        if {"m", "p", "s"} <= suits:
            yaku_list.append({"name": "sanshoku_doujun", "han_closed": 2, "han_open": 1, "is_yakuman": False})
            return


def _add_sanshoku_doukou(yaku_list, all_mentsu):
    koutsu = [m for m in all_mentsu if m["type"] == "koutsu"]
    for m in koutsu:
        num = get_number(m["tiles"][0])
        if num is None:
            continue
        suits = {get_suit(m2["tiles"][0]) for m2 in koutsu if get_number(m2["tiles"][0]) == num}
        if {"m", "p", "s"} <= suits:
            yaku_list.append({"name": "sanshoku_doukou", "han_closed": 2, "han_open": 2, "is_yakuman": False})
            return


def _add_ittsu(yaku_list, all_mentsu):
    shuntsu = [m for m in all_mentsu if m["type"] == "shuntsu"]
    for suit in "mps":
        starts = {get_number(m["tiles"][0]) for m in shuntsu if get_suit(m["tiles"][0]) == suit}
        if {1, 4, 7} <= starts:
            yaku_list.append({"name": "ittsu", "han_closed": 2, "han_open": 1, "is_yakuman": False})
            return


def _add_chanta_junchan(yaku_list, pattern, all_mentsu):
    jantai = pattern["jantai"]

    # 雀頭が么九牌でなければ両方とも不成立
    if not is_yaochuuhai(jantai):
        return

    # 全面子が么九牌を含むか
    for m in all_mentsu:
        if not any(is_yaochuuhai(t) for t in m["tiles"]):
            return

    # 字牌が含まれるか
    has_jihai = is_jihai(jantai) or any(is_jihai(m["tiles"][0]) for m in all_mentsu if m["type"] == "koutsu")

    if not has_jihai:
        # 純全帯幺九（字牌なし）
        yaku_list.append({"name": "junchan", "han_closed": 3, "han_open": 2, "is_yakuman": False})
    else:
        # 混全帯幺九
        yaku_list.append({"name": "chanta", "han_closed": 2, "han_open": 1, "is_yakuman": False})


def _add_toitoi(yaku_list, all_mentsu):
    if all(m["type"] == "koutsu" for m in all_mentsu):
        yaku_list.append({"name": "toitoi", "han_closed": 2, "han_open": 2, "is_yakuman": False})


def _add_sanankou(yaku_list, mentsu_list, melds, win_tile, win_type):
    concealed_koutsu = 0
    for m in mentsu_list:
        if m["type"] != "koutsu":
            continue
        # ロンで当たり牌が含まれる刻子は明刻扱い
        if win_tile in m["tiles"] and win_type == "ron":
            continue
        concealed_koutsu += 1
    # 暗槓も暗刻としてカウント
    concealed_koutsu += sum(1 for m in melds if m["type"] == "ankan")
    if concealed_koutsu >= 3:
        yaku_list.append({"name": "sanankou", "han_closed": 2, "han_open": 2, "is_yakuman": False})


def _add_shousangen(yaku_list, all_mentsu, jantai):
    if jantai not in SANGENPAI:
        return
    sangen_koutsu = sum(1 for m in all_mentsu if m["type"] == "koutsu" and m["tiles"][0] in SANGENPAI)
    if sangen_koutsu == 2:
        yaku_list.append({"name": "shousangen", "han_closed": 2, "han_open": 2, "is_yakuman": False})


def _add_honroutou(yaku_list, all_tiles):
    if all(is_yaochuuhai(t) for t in all_tiles):
        yaku_list.append({"name": "honroutou", "han_closed": 2, "han_open": 2, "is_yakuman": False})


def _add_yakuhai(yaku_list, all_mentsu, context):
    seat_wind = WIND_TO_TILE.get(context.seat_wind, "東")
    round_wind = WIND_TO_TILE.get(context.round_wind, "東")
    for m in all_mentsu:
        if m["type"] != "koutsu":
            continue
        tile = m["tiles"][0]
        if tile in SANGENPAI:
            yaku_list.append({"name": f"yakuhai_{tile}", "han_closed": 1, "han_open": 1, "is_yakuman": False})
        if tile == seat_wind:
            yaku_list.append({"name": "yakuhai_jikaze", "han_closed": 1, "han_open": 1, "is_yakuman": False})
        if tile == round_wind and round_wind != seat_wind:
            yaku_list.append({"name": "yakuhai_bakaze", "han_closed": 1, "han_open": 1, "is_yakuman": False})


def _add_honitsu_chinitsu(yaku_list, all_tiles, melds):
    suits = set()
    has_jihai = False
    for t in all_tiles:
        if is_jihai(t):
            has_jihai = True
        else:
            suits.add(get_suit(t))
    if len(suits) == 1:
        if has_jihai:
            yaku_list.append({"name": "honitsu", "han_closed": 3, "han_open": 2, "is_yakuman": False})
        else:
            yaku_list.append({"name": "chinitsu", "han_closed": 6, "han_open": 5, "is_yakuman": False})


def _check_yakuman(pattern, all_mentsu, melds, win_tile, win_type, all_tiles, is_closed) -> list:
    yakuman = []
    jantai = pattern["jantai"]
    mentsu_list = pattern["mentsu"]

    # 大三元
    sangen_koutsu = [m for m in all_mentsu if m["type"] == "koutsu" and m["tiles"][0] in SANGENPAI]
    if len(sangen_koutsu) == 3:
        yakuman.append({"name": "daisangen", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 四暗刻（チー・ポン・明槓がない場合）
    if not any(m["type"] in ("chi", "pon", "minkan") for m in melds):
        concealed_koutsu = sum(
            1 for m in mentsu_list
            if m["type"] == "koutsu" and not (win_tile in m["tiles"] and win_type == "ron")
        )
        ankan_count = sum(1 for m in melds if m["type"] == "ankan")
        if concealed_koutsu + ankan_count == 4:
            # 四暗刻単騎待ちはダブル役満
            wait_type = _get_wait_type(pattern, win_tile)
            multiplier = 2 if wait_type == "tanki" else 1
            yakuman.append({"name": "suuankou", "han_closed": 13, "han_open": 0,
                            "is_yakuman": True, "yakuman_multiplier": multiplier})

    # 小四喜・大四喜
    wind_koutsu = [m for m in all_mentsu if m["type"] == "koutsu" and m["tiles"][0] in WINDS]
    if len(wind_koutsu) == 4:
        # 大四喜はダブル役満
        yakuman.append({"name": "daisuushii", "han_closed": 13, "han_open": 13,
                        "is_yakuman": True, "yakuman_multiplier": 2})
    elif len(wind_koutsu) == 3 and jantai in WINDS:
        yakuman.append({"name": "shousuushii", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 字一色
    if all(is_jihai(t) for t in all_tiles):
        yakuman.append({"name": "tsuuiisou", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 緑一色
    if all(t in GREEN_TILES for t in all_tiles):
        yakuman.append({"name": "ryuuiisou", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 清老頭
    if all(is_yaochuuhai(t) and not is_jihai(t) for t in all_tiles):
        yakuman.append({"name": "chinroutou", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 四槓子
    kan_count = sum(1 for m in melds if m["type"] in ("minkan", "ankan"))
    if kan_count == 4:
        yakuman.append({"name": "suukantsu", "han_closed": 13, "han_open": 13, "is_yakuman": True})

    # 九蓮宝燈（門前のみ）
    if is_closed:
        suits = {get_suit(t) for t in all_tiles}
        if len(suits) == 1 and list(suits)[0] in "mps":
            suit = list(suits)[0]
            base = (
                [f"1{suit}"] * 3
                + [f"{n}{suit}" for n in range(2, 9)]
                + [f"9{suit}"] * 3
            )
            remaining = list(all_tiles)
            ok = True
            for t in base:
                if t in remaining:
                    remaining.remove(t)
                else:
                    ok = False
                    break
            if ok and len(remaining) == 1:
                # 純正九蓮宝燈: 和了牌を除いた13枚がちょうど1112345678999ならダブル役満
                tiles_13 = list(all_tiles)
                tiles_13.remove(win_tile)
                from tiles import sort_tiles
                is_junsei = sort_tiles(tiles_13) == sort_tiles(base)
                multiplier = 2 if is_junsei else 1
                yakuman.append({"name": "chuurenpoutou", "han_closed": 13, "han_open": 0,
                                "is_yakuman": True, "yakuman_multiplier": multiplier})

    return yakuman or None


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
        nums = sorted(int(t[0]) for t in m["tiles"])
        win_num = int(win_tile[0])
        if win_num == nums[1]:
            return "kanchan"
        if win_num == nums[0]:
            return "penchan" if nums[2] == 9 else "ryanmen"
        if win_num == nums[2]:
            return "penchan" if nums[0] == 1 else "ryanmen"

    return "tanki"
