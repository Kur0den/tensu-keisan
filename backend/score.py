import math
from models import ScoreResult, Payment

# 点数テーブル（子）
KO_TABLE = {
    "mangan":    8000,
    "haneman":   12000,
    "baiman":    16000,
    "sanbaiman": 24000,
    "yakuman":   32000,
}

# 点数テーブル（親）
OYA_TABLE = {
    "mangan":    12000,
    "haneman":   18000,
    "baiman":    24000,
    "sanbaiman": 36000,
    "yakuman":   48000,
}


def calculate_score(han: int, fu: int, win_type: str, is_dealer: bool) -> ScoreResult:
    basic_points = fu * (2 ** (han + 2))

    # カテゴリ判定
    if han >= 13:
        return _fixed_payment(OYA_TABLE["yakuman"] if is_dealer else KO_TABLE["yakuman"], win_type, is_dealer)
    elif han >= 11:
        return _fixed_payment(OYA_TABLE["sanbaiman"] if is_dealer else KO_TABLE["sanbaiman"], win_type, is_dealer)
    elif han >= 8:
        return _fixed_payment(OYA_TABLE["baiman"] if is_dealer else KO_TABLE["baiman"], win_type, is_dealer)
    elif han >= 6:
        return _fixed_payment(OYA_TABLE["haneman"] if is_dealer else KO_TABLE["haneman"], win_type, is_dealer)
    elif han >= 5 or basic_points >= 2000:
        # 切り上げ満貫も含む
        return _fixed_payment(OYA_TABLE["mangan"] if is_dealer else KO_TABLE["mangan"], win_type, is_dealer)
    else:
        return _normal_payment(basic_points, win_type, is_dealer)


def _normal_payment(basic_points: int, win_type: str, is_dealer: bool) -> ScoreResult:
    if win_type == "ron":
        multiplier = 6 if is_dealer else 4
        ron_total = _ceil100(basic_points * multiplier)
        return ScoreResult(basic_points=basic_points, payment=Payment(ron=ron_total))
    else:
        if is_dealer:
            # 全員が同額支払い
            per_player = _ceil100(basic_points * 2)
            return ScoreResult(basic_points=basic_points, payment=Payment(tsumo_non_dealer=per_player))
        else:
            dealer_pay = _ceil100(basic_points * 2)
            non_dealer_pay = _ceil100(basic_points * 1)
            return ScoreResult(basic_points=basic_points, payment=Payment(
                tsumo_dealer=dealer_pay,
                tsumo_non_dealer=non_dealer_pay
            ))


def _fixed_payment(total: int, win_type: str, is_dealer: bool) -> ScoreResult:
    if win_type == "ron":
        return ScoreResult(basic_points=0, payment=Payment(ron=total))
    else:
        if is_dealer:
            per_player = total // 3
            return ScoreResult(basic_points=0, payment=Payment(tsumo_non_dealer=per_player))
        else:
            dealer_pay = total // 2
            non_dealer_pay = total // 4
            return ScoreResult(basic_points=0, payment=Payment(
                tsumo_dealer=dealer_pay,
                tsumo_non_dealer=non_dealer_pay
            ))


def _ceil100(n: int) -> int:
    return math.ceil(n / 100) * 100
