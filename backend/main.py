from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import CalculateRequest, CalculateResponse, YakuResult
from agari import check_agari
from yaku import detect_yaku
from fu import calculate_fu
from score import calculate_score
from tiles import (
    dora_from_indicator,
    normalize_tile,
    normalize_tiles,
    is_red_dora,
    is_valid_tile,
)

app = FastAPI(title="麻雀点数計算API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.post("/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest):
    _validate_request(req)

    # 赤ドラカウント（正規化前に数える）
    raw_closed = req.hand.closed + [req.win_tile]
    raw_meld_tiles = [t for m in req.hand.melds for t in m.tiles]
    red_dora_count = sum(1 for t in raw_closed + raw_meld_tiles if is_red_dora(t))

    # 手牌全体を構築（赤ドラを通常牌に正規化・副露を含む）
    closed_tiles = normalize_tiles(raw_closed)
    melds = [
        {**m.model_dump(), "tiles": normalize_tiles(m.tiles)}
        for m in req.hand.melds
    ]
    win_tile = normalize_tile(req.win_tile)
    all_tiles = closed_tiles + normalize_tiles(raw_meld_tiles)

    # 和了判定
    is_agari, patterns, special_type = check_agari(closed_tiles, melds, win_tile)
    if not is_agari:
        return CalculateResponse(is_agari=False, error="not_agari")

    is_dealer = req.context.seat_wind == "east"

    # ドラカウント（通常ドラ + 裏ドラ + 赤ドラ）
    dora_tiles = [dora_from_indicator(normalize_tile(d)) for d in req.context.dora]
    ura_dora_tiles = (
        [dora_from_indicator(normalize_tile(d)) for d in req.context.ura_dora]
        if req.context.is_riichi else []
    )
    dora_count = sum(all_tiles.count(d) for d in dora_tiles) + red_dora_count
    ura_dora_count = sum(all_tiles.count(d) for d in ura_dora_tiles)

    # 最高得点のパターンを探す
    best = None

    if special_type in ("kokushi", "chiitoi"):
        dummy_pattern = {"jantai": None, "mentsu": []}
        result = _evaluate(
            dummy_pattern, special_type, melds, win_tile, req.win_type,
            req.context, all_tiles, dora_count, ura_dora_count, is_dealer
        )
        if result:
            best = result
    else:
        for pattern in patterns:
            result = _evaluate(
                pattern, None, melds, win_tile, req.win_type,
                req.context, all_tiles, dora_count, ura_dora_count, is_dealer
            )
            if result and (best is None or _total_payment(result["score"]) > _total_payment(best["score"])):
                best = result

    if best is None:
        return CalculateResponse(is_agari=False, error="no_yaku")

    return CalculateResponse(
        is_agari=True,
        yaku=[YakuResult(**y) for y in best["yaku"]],
        han_total=best["han_total"],
        fu_total=best["fu_total"],
        score=best["score"],
    )


def _evaluate(pattern, special_type, melds, win_tile, win_type, context, all_tiles,
              dora_count, ura_dora_count, is_dealer):
    yaku_list = detect_yaku(pattern, special_type, melds, win_tile, win_type, context, all_tiles)
    if not yaku_list:
        return None

    fu = calculate_fu(pattern, special_type, melds, win_tile, win_type, context)
    # 暗槓は門前扱いのため、チー・ポン・明槓があるときのみ open
    is_open = any(m["type"] in ("chi", "pon", "minkan") for m in melds)
    has_yakuman = any(y["is_yakuman"] for y in yaku_list)

    if has_yakuman:
        # 役満倍率を合算（ダブル役満=2, トリプル=3...）
        total_multiplier = sum(y.get("yakuman_multiplier", 1) for y in yaku_list if y["is_yakuman"])
        han = 13 * total_multiplier
    else:
        han = sum(y["han_open"] if is_open else y["han_closed"] for y in yaku_list)
        han += dora_count + ura_dora_count

    if han == 0:
        return None

    score = calculate_score(han, fu, win_type, is_dealer)

    return {"yaku": yaku_list, "han_total": han, "fu_total": fu, "score": score}


def _total_payment(score) -> int:
    p = score.payment
    return p.ron + p.tsumo_dealer + p.tsumo_non_dealer


def _validate_request(req: CalculateRequest) -> None:
    raw_closed = req.hand.closed + [req.win_tile]
    raw_meld_tiles = [t for m in req.hand.melds for t in m.tiles]
    raw_all_tiles = raw_closed + raw_meld_tiles

    invalid_tiles = [t for t in raw_all_tiles + req.context.dora + req.context.ura_dora if not is_valid_tile(t)]
    if invalid_tiles:
        raise HTTPException(status_code=400, detail=f"invalid_tile: {invalid_tiles[0]}")

    if len(req.hand.melds) > 4:
        raise HTTPException(status_code=400, detail="too_many_melds")

    for meld in req.hand.melds:
        _validate_meld(meld.type, meld.tiles)

    expected_closed_with_win = 14 - (3 * len(req.hand.melds))
    if len(raw_closed) != expected_closed_with_win:
        raise HTTPException(status_code=400, detail="invalid_tile_count")

    from collections import Counter

    counts = Counter(normalize_tiles(raw_all_tiles))
    over_limit = [tile for tile, count in counts.items() if count > 4]
    if over_limit:
        raise HTTPException(status_code=400, detail=f"too_many_same_tile: {over_limit[0]}")

    if req.context.is_ippatsu and not req.context.is_riichi:
        raise HTTPException(status_code=400, detail="ippatsu_requires_riichi")
    if req.context.is_rinshan and req.win_type != "tsumo":
        raise HTTPException(status_code=400, detail="rinshan_requires_tsumo")
    if req.context.is_chankan and req.win_type != "ron":
        raise HTTPException(status_code=400, detail="chankan_requires_ron")
    if req.context.is_haitei and req.win_type != "tsumo":
        raise HTTPException(status_code=400, detail="haitei_requires_tsumo")
    if req.context.is_houtei and req.win_type != "ron":
        raise HTTPException(status_code=400, detail="houtei_requires_ron")
    if req.context.is_haitei and req.context.is_rinshan:
        raise HTTPException(status_code=400, detail="haitei_conflicts_with_rinshan")
    if req.context.is_houtei and req.context.is_chankan:
        raise HTTPException(status_code=400, detail="houtei_conflicts_with_chankan")


def _validate_meld(meld_type: str, tiles: list[str]) -> None:
    normalized = normalize_tiles(tiles)

    if meld_type == "chi":
        if len(normalized) != 3:
            raise HTTPException(status_code=400, detail="invalid_chi_tile_count")
        if not all(t[-1] in "mps" for t in normalized):
            raise HTTPException(status_code=400, detail="invalid_chi_tiles")
        suit = normalized[0][-1]
        numbers = sorted(int(t[0]) for t in normalized)
        if not all(t[-1] == suit for t in normalized) or numbers[1] != numbers[0] + 1 or numbers[2] != numbers[1] + 1:
            raise HTTPException(status_code=400, detail="invalid_chi_tiles")
        return

    expected_count = 4 if meld_type in ("minkan", "ankan") else 3
    if len(normalized) != expected_count:
        raise HTTPException(status_code=400, detail=f"invalid_{meld_type}_tile_count")
    if len(set(normalized)) != 1:
        raise HTTPException(status_code=400, detail=f"invalid_{meld_type}_tiles")


@app.get("/health")
def health():
    return {"status": "ok"}


# フロントエンドを静的ファイルとして配信
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
