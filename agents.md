# 麻雀点数計算ツール 仕様書

## 概要

手牌・状況を入力として受け取り、和了判定・役判定・点数計算を行うWEBアプリケーション。  
授業課題: LLMを活用した仕様駆動開発として作成。

---

## 技術スタック

| レイヤー | 技術 |
|----------|------|
| バックエンド | Python / FastAPI |
| フロントエンド | HTML + CSS + JavaScript |
| APIフォーマット | REST / JSON |

---

## ディレクトリ構成

```
tensu-keisan/
├── backend/
│   ├── main.py          # FastAPIエントリポイント
│   ├── models.py        # リクエスト/レスポンスのPydanticモデル
│   ├── agari.py         # 和了判定ロジック
│   ├── yaku.py          # 役判定ロジック
│   ├── fu.py            # 符計算ロジック
│   ├── score.py         # 点数計算ロジック
│   └── tests/
│       └── test_*.py    # 各モジュールのテスト
└── frontend/
    ├── index.html
    ├── style.css
    └── main.js
```

---

## スコープ

### 対象とするルール
- 4面子1雀頭形の和了
- 七対子
- 国士無双
- 副露あり（チー・ポン・明槓・暗槓）
- ツモ和了・ロン和了

### 対象外（簡略化）
- 流し満貫
- 天和・地和
- ダブル役満の区別（すべて役満として扱う）
- 三人麻雀

---

## データ仕様

### 牌の表現

```
数牌: {1-9}{m|p|s}
  例) 1m=一萬, 5p=五筒, 9s=九索

字牌: 東|南|西|北|白|發|中
```

### APIエンドポイント

```
POST /calculate
  手牌・状況を受け取り、点数計算結果を返す

GET /health
  サーバー死活確認用
```

### リクエスト仕様

```json
{
  "hand": {
    "closed": ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s", "2m", "3m"],
    "melds": [
      {
        "type": "chi | pon | minkan | ankan",
        "tiles": ["1m", "2m", "3m"]
      }
    ]
  },
  "win_tile": "1m",
  "win_type": "tsumo | ron",
  "context": {
    "seat_wind": "east | south | west | north",
    "round_wind": "east | south | west | north",
    "is_riichi": false,
    "is_ippatsu": false,
    "is_rinshan": false,
    "is_chankan": false,
    "is_haitei": false,
    "is_houtei": false,
    "dora": ["5m"],
    "ura_dora": ["3p"]
  }
}
```

### レスポンス仕様

```json
// 和了時
{
  "is_agari": true,
  "yaku": [
    {
      "name": "pinfu",
      "han_closed": 1,
      "han_open": 0,
      "is_yakuman": false
    }
  ],
  "han_total": 2,
  "fu_total": 20,
  "score": {
    "basic_points": 320,
    "payment": {
      "tsumo_dealer": 700,
      "tsumo_non_dealer": 400,
      "ron": 0
    }
  }
}

// 非和了時
{
  "is_agari": false,
  "error": "no_yaku | not_agari"
}
```

---

## 機能仕様

### 和了判定 (`agari.py`)

```
通常形:
  - 手牌全体が「4面子 + 1雀頭」に分割できること
  - 面子: 順子（連続する同種3枚）または刻子（同じ牌3枚）
  - 雀頭: 同じ牌2枚
  - 分割方法が複数ある場合はすべての解釈で役・符を計算し、最高得点を採用

七対子:
  - 7種類の対子で構成される14枚
  - 同じ牌4枚は対子2つとして扱わない

国士無双:
  - 1m9m1p9p1s9s東南西北白發中 を各1枚以上含み
  - そのうちいずれか1種を2枚持つ
```

### 役判定 (`yaku.py`)

| 役名 | 門前 | 副露 | 判定条件 |
|------|------|------|----------|
| 立直 | 1翻 | - | is_riichi=true |
| 一発 | 1翻 | - | is_ippatsu=true |
| 門前清自摸和 | 1翻 | - | win_type=tsumo かつ 副露なし |
| 海底摸月 | 1翻 | 1翻 | is_haitei=true |
| 河底撈魚 | 1翻 | 1翻 | is_houtei=true |
| 嶺上開花 | 1翻 | 1翻 | is_rinshan=true |
| 槍槓 | 1翻 | 1翻 | is_chankan=true |
| 断幺九 | 1翻 | 1翻 | 手牌・副露に1・9・字牌が含まれない |
| 平和 | 1翻 | - | 全面子が順子・雀頭が役牌以外・両面待ち |
| 一盃口 | 1翻 | - | 同じ順子が2組 |
| 二盃口 | 3翻 | - | 同じ順子が2組×2（一盃口と複合しない）|
| 三色同順 | 2翻 | 1翻 | 萬・筒・索で同じ数の順子 |
| 三色同刻 | 2翻 | 2翻 | 萬・筒・索で同じ数の刻子 |
| 一気通貫 | 2翻 | 1翻 | 同種で123・456・789の順子 |
| 混全帯幺九 | 2翻 | 1翻 | 全面子と雀頭に1・9・字牌を含む |
| 純全帯幺九 | 3翻 | 2翻 | 全面子と雀頭に1・9のみを含む（字牌なし）|
| 混老頭 | 2翻 | 2翻 | 全牌が1・9・字牌のみ |
| 清老頭 | 役満 | 役満 | 全牌が1・9のみ |
| 対々和 | 2翻 | 2翻 | 全面子が刻子 |
| 三暗刻 | 2翻 | 2翻 | 暗刻が3組 |
| 四暗刻 | 役満 | - | 暗刻が4組（ロン和了は対々和＋三暗刻）|
| 小三元 | 2翻 | 2翻 | 白・發・中のうち2種を刻子、1種を雀頭 |
| 大三元 | 役満 | 役満 | 白・發・中をすべて刻子 |
| 混一色 | 3翻 | 2翻 | 1種の数牌＋字牌のみ |
| 清一色 | 6翻 | 5翻 | 1種の数牌のみ |
| 小四喜 | 役満 | 役満 | 東南西北のうち3種を刻子、1種を雀頭 |
| 大四喜 | 役満 | 役満 | 東南西北をすべて刻子 |
| 字一色 | 役満 | 役満 | 全牌が字牌のみ |
| 緑一色 | 役満 | 役満 | 2s3s4s6s8s發のみで構成 |
| 九蓮宝燈 | 役満 | - | 同種で1112345678999＋任意1枚 |
| 国士無双 | 役満 | - | 上記参照 |
| 七対子 | 2翻(25符固定) | - | 上記参照 |
| 役牌（自風）| 1翻 | 1翻 | 自風牌の刻子 |
| 役牌（場風）| 1翻 | 1翻 | 場風牌の刻子 |
| 役牌（三元）| 1翻 | 1翻 | 白・發・中の刻子（各1翻）|

### 符計算 (`fu.py`)

```
基本符:
  通常形:     30符
  平和ロン:   30符
  平和ツモ:   20符
  副露形:     20符
  七対子:     25符（固定）

面子符:
  順子:           0符
  明刻（中張牌）: 2符
  明刻（么九牌）: 4符
  暗刻（中張牌）: 4符
  暗刻（么九牌）: 8符
  明槓（中張牌）: 8符
  明槓（么九牌）: 16符
  暗槓（中張牌）: 16符
  暗槓（么九牌）: 32符

雀頭符:
  数牌・客風牌:         0符
  場風牌 または 自風牌: 2符
  場風牌 かつ 自風牌:   4符
  三元牌:               2符

待ち符:
  両面待ち: 0符
  嵌張待ち: 2符
  辺張待ち: 2符
  単騎待ち: 2符
  双碰待ち: 0符

ツモ符:
  ツモ和了（平和以外）: 2符

合計: 10符単位で切り上げ
```

### 点数計算 (`score.py`)

```
基本点 = 符 × 2^(翻数+2)

親の得点:
  ロン:  基本点 × 6（100点単位で切り上げ）
  ツモ:  基本点 × 2（100点単位で切り上げ）× 3人

子の得点:
  ロン:      基本点 × 4（100点単位で切り上げ）
  ツモ親払い: 基本点 × 2（100点単位で切り上げ）
  ツモ子払い: 基本点 × 1（100点単位で切り上げ）

満貫以上（翻数での判定）:
  満貫:   5翻       →  8000点（親12000点）
  跳満:   6-7翻     → 12000点（親18000点）
  倍満:   8-10翻    → 16000点（親24000点）
  三倍満: 11-12翻   → 24000点（親36000点）
  役満:   13翻以上 or 役満役 → 32000点（親48000点）

切り上げ満貫:
  翻数が5未満でも 符×翻数の計算結果が満貫点数を超える場合は満貫として扱う
```

---

## テストケース

```yaml
# ケース1: 平和ツモ
request:
  hand: { closed: [1m, 2m, 3m, 4p, 5p, 6p, 7s, 8s, 9s, 2m, 3m] }
  win_tile: 1m
  win_type: tsumo
  context: { seat_wind: east, round_wind: east, is_riichi: false }
expected:
  is_agari: true
  yaku: [menzen_tsumo, pinfu]
  han_total: 2
  fu_total: 20

# ケース2: リーチ一発ツモ
request:
  hand: { closed: [1m, 2m, 3m, 1p, 1p, 1p, 1s, 2s, 3s, 4s, 5s] }
  win_tile: 6s
  win_type: tsumo
  context: { is_riichi: true, is_ippatsu: true }
expected:
  is_agari: true
  yaku: [riichi, ippatsu, menzen_tsumo, tanyao]
  han_total: 4
  fu_total: 30

# ケース3: 役なし（和了不可）
request:
  hand: { closed: [1m, 2m, 3m, 5p, 6p, 7p, 2s, 3s, 4s, 9m, 9m] }
  win_tile: 9p
  win_type: ron
  context: { is_riichi: false }
expected:
  is_agari: false
  error: no_yaku

# ケース4: 大三元
request:
  hand: { closed: [白, 白, 白, 發, 發, 發, 中, 中, 中, 1m, 1m] }
  win_tile: 1m
  win_type: ron
expected:
  is_agari: true
  yaku: [daisangen]
  is_yakuman: true
  score: { payment: { ron: 48000 } }
```