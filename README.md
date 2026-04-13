# 麻雀点数計算ツール

手牌・状況を入力すると、和了判定・役判定・点数計算を行うWebアプリケーション。

> [!WARNING]
> このプロジェクトはバイブコーディング（LLMに仕様を与えて実装を生成させる手法）で作成されました。
> コードの一部は自動生成されているため、エッジケースや細かいルールに誤りが含まれる可能性があります。
> 実際のゲームでの使用には十分ご注意ください。

---

## 機能

- 和了判定（通常形 / 七対子 / 国士無双）
- 役判定（立直・平和・一盃口・役満など30種以上）
- 符計算・点数計算（満貫・跳満・役満など）
- 副露（チー・ポン・カン）対応
- ドラ・裏ドラ対応

---

## 推奨ツール

| ツール | 用途 |
|--------|------|
| [uv](https://docs.astral.sh/uv/) | Python パッケージ管理・仮想環境 |
| Python 3.11 以上 | 動作確認済み |
| [FastAPI](https://fastapi.tiangolo.com/) | バックエンドフレームワーク |
| [uvicorn](https://www.uvicorn.org/) | ASGIサーバー |

---

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/Kur0den/tensu-keisan.git
cd tensu-keisan
```

### 2. 仮想環境を作成・依存関係をインストール

```bash
uv venv
uv pip install fastapi uvicorn
```

### 3. サーバーを起動

```bash
cd backend
uv run uvicorn main:app --reload
```

ブラウザで `http://localhost:8000` にアクセスするとUIが開きます。

---

## 使い方

### 基本的な流れ

1. **閉じた手牌** を入力する（副露を除いた13枚の手牌から和了牌を除いた部分）
2. **和了牌** を入力する
3. **和了方法**（ツモ / ロン）を選択する
4. 必要に応じて **副露・場況・ドラ** を設定する
5. **計算する** ボタンを押す

### 牌の入力形式

牌はスペース区切りで入力します。

| 種類 | 形式 | 例 |
|------|------|----|
| 萬子 | `{数字}m` | `1m` `5m` `9m` |
| 筒子 | `{数字}p` | `1p` `5p` `9p` |
| 索子 | `{数字}s` | `1s` `5s` `9s` |
| 字牌 | そのまま | `東` `南` `西` `北` `白` `發` `中` |

**入力例（平和イーペーコー）:**

```
閉じた手牌: 1m 2m 3m 1m 2m 3m 4p 5p 6p 7s 8s 東 東
和了牌:     9s
和了方法:   ツモ
```

### 副露の追加

「+ 追加」ボタンから副露を最大4つまで追加できます。

| 種別 | 説明 |
|------|------|
| チー | 左の人からの順子 |
| ポン | 刻子（3枚） |
| カン | 槓子（4枚）※すべて明槓として処理 |

### 場況の設定

| 項目 | 説明 |
|------|------|
| 自風 | 東=親、南・西・北=子 |
| 場風 | 現在の場（東場 / 南場など） |
| リーチ | リーチ宣言している場合にチェック |
| 一発 | 一発圏内の場合にチェック |
| 海底・河底・嶺上開花・槍槓 | 該当する場合にチェック |

### ドラの入力

ドラは**表示牌**（ドラそのものではなく、めくられた牌）を入力します。

```
例: ドラ表示牌が 5m → 入力は 5m（実際のドラは 6m）
```

---

## APIリファレンス

バックエンドは REST API として単体でも利用できます。
起動後 `http://localhost:8000/docs` で Swagger UI が確認できます。

### POST /calculate

**リクエスト例:**

```json
{
  "hand": {
    "closed": ["1m","2m","3m","4p","5p","6p","7s","8s","9s","東","東","白","白"],
    "melds": []
  },
  "win_tile": "白",
  "win_type": "tsumo",
  "context": {
    "seat_wind": "east",
    "round_wind": "east",
    "is_riichi": false,
    "dora": ["4p"]
  }
}
```

**レスポンス例:**

```json
{
  "is_agari": true,
  "yaku": [
    { "name": "menzen_tsumo", "han_closed": 1, "han_open": 0, "is_yakuman": false },
    { "name": "yakuhai_白",   "han_closed": 1, "han_open": 1, "is_yakuman": false }
  ],
  "han_total": 3,
  "fu_total": 40,
  "score": {
    "basic_points": 1280,
    "payment": {
      "tsumo_dealer": 0,
      "tsumo_non_dealer": 0,
      "ron": 0
    }
  }
}
```

---

## スコープ外（非対応ルール）

- 流し満貫
- 天和・地和
- ダブル役満の区別（すべて役満として計算）
- 暗槓・明槓の区別（すべて明槓として処理）
- 三人麻雀

---

## ディレクトリ構成

```
tensu-keisan/
├── README.md
├── agents.md          # 仕様書（LLMへの指示書）
├── backend/
│   ├── main.py        # FastAPI エントリポイント
│   ├── models.py      # リクエスト / レスポンスモデル
│   ├── tiles.py       # 牌のユーティリティ
│   ├── agari.py       # 和了判定
│   ├── yaku.py        # 役判定
│   ├── fu.py          # 符計算
│   ├── score.py       # 点数計算
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── main.js
```
