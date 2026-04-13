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
from tiles import dora_from_indicator, normalize_tile, normalize_tiles, is_red_dora

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
        han = 13
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


@app.get("/health")
def health():
    return {"status": "ok"}


# フロントエンドを静的ファイルとして配信
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
