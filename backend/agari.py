from tiles import sort_tiles, is_yaochuuhai, KOKUSHI_TILES


def check_agari(closed_tiles: list, melds: list, win_tile: str):
    """
    和了判定。closed_tilesはwin_tileを含む。
    Returns: (is_agari, patterns, special_type)
      special_type: None | "chiitoi" | "kokushi"
    """
    n_melds = len(melds)

    if n_melds == 0:
        if _is_kokushi(closed_tiles):
            return True, [], "kokushi"
        if _is_chiitoi(closed_tiles):
            return True, [], "chiitoi"

    n_mentsu_needed = 4 - n_melds
    patterns = _find_patterns(closed_tiles, n_mentsu_needed)

    if patterns:
        return True, patterns, None

    return False, [], None


def _is_chiitoi(tiles: list) -> bool:
    if len(tiles) != 14:
        return False
    from collections import Counter
    counts = Counter(tiles)
    pairs = [t for t, c in counts.items() if c == 2]
    return len(pairs) == 7


def _is_kokushi(tiles: list) -> bool:
    if len(tiles) != 14:
        return False
    from collections import Counter
    counts = Counter(tiles)
    has_all = all(t in counts for t in KOKUSHI_TILES)
    has_pair = any(counts.get(t, 0) >= 2 for t in KOKUSHI_TILES)
    only_kokushi = all(t in KOKUSHI_TILES for t in tiles)
    return has_all and has_pair and only_kokushi


def _find_patterns(tiles: list, n_mentsu: int) -> list:
    """全ての（雀頭 + n面子）の分割を列挙する"""
    results = []
    sorted_t = sort_tiles(tiles)

    for pair_tile in set(sorted_t):
        if sorted_t.count(pair_tile) >= 2:
            remaining = list(sorted_t)
            remaining.remove(pair_tile)
            remaining.remove(pair_tile)

            for mp in _find_mentsu_n(remaining, n_mentsu):
                results.append({"jantai": pair_tile, "mentsu": mp})

    return results


def _find_mentsu_n(tiles: list, n: int) -> list:
    """tiles から n 個の面子を作る全ての方法を返す"""
    if n == 0:
        return [[]] if not tiles else []
    if not tiles:
        return []

    results = []
    tile = tiles[0]

    # 刻子を試みる
    if tiles.count(tile) >= 3:
        remaining = list(tiles)
        for _ in range(3):
            remaining.remove(tile)
        for sub in _find_mentsu_n(remaining, n - 1):
            results.append([{"type": "koutsu", "tiles": [tile, tile, tile]}] + sub)

    # 順子を試みる（数牌のみ）
    if tile[-1] in "mps":
        num = int(tile[0])
        suit = tile[-1]
        if num <= 7:
            t2 = f"{num + 1}{suit}"
            t3 = f"{num + 2}{suit}"
            remaining = list(tiles)
            remaining.remove(tile)
            if t2 in remaining:
                remaining.remove(t2)
                if t3 in remaining:
                    remaining.remove(t3)
                    for sub in _find_mentsu_n(remaining, n - 1):
                        results.append([{"type": "shuntsu", "tiles": [tile, t2, t3]}] + sub)

    return results
