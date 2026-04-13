const API_BASE = "";  // FastAPI経由で配信するので相対パスでOK

// 役名の日本語マッピング
const YAKU_NAMES = {
  riichi: "立直",
  ippatsu: "一発",
  menzen_tsumo: "門前清自摸和",
  haitei: "海底摸月",
  houtei: "河底撈魚",
  rinshan_kaihou: "嶺上開花",
  chankan: "槍槓",
  tanyao: "断幺九",
  pinfu: "平和",
  iipeiko: "一盃口",
  ryanpeiko: "二盃口",
  sanshoku_doujun: "三色同順",
  sanshoku_doukou: "三色同刻",
  ittsu: "一気通貫",
  chanta: "混全帯幺九",
  junchan: "純全帯幺九",
  toitoi: "対々和",
  sanankou: "三暗刻",
  shousangen: "小三元",
  honroutou: "混老頭",
  chiitoitsu: "七対子",
  honitsu: "混一色",
  chinitsu: "清一色",
  daisangen: "大三元",
  suuankou: "四暗刻",
  shousuushii: "小四喜",
  daisuushii: "大四喜",
  tsuuiisou: "字一色",
  ryuuiisou: "緑一色",
  chinroutou: "清老頭",
  chuurenpoutou: "九蓮宝燈",
  kokushi_musou: "国士無双",
  yakuhai_白: "役牌（白）",
  yakuhai_發: "役牌（發）",
  yakuhai_中: "役牌（中）",
  yakuhai_jikaze: "役牌（自風）",
  yakuhai_bakaze: "役牌（場風）",
};

const ERROR_MESSAGES = {
  not_agari: "和了形になっていません",
  no_yaku: "役がありません",
};

let meldCount = 0;

// 副露を追加
document.getElementById("add-meld").addEventListener("click", () => {
  if (meldCount >= 4) return;
  meldCount++;
  const id = meldCount;

  const div = document.createElement("div");
  div.className = "meld-item";
  div.dataset.meldId = id;
  div.innerHTML = `
    <div class="field" style="margin:0">
      <label>種別</label>
      <select data-role="meld-type">
        <option value="chi">チー</option>
        <option value="pon">ポン</option>
        <option value="kan">カン</option>
      </select>
    </div>
    <div class="field" style="margin:0">
      <label>牌（スペース区切り）</label>
      <input type="text" data-role="meld-tiles" placeholder="例: 3m 4m 5m" />
    </div>
    <button class="btn-danger" onclick="removeMeld(this)">削除</button>
  `;
  document.getElementById("melds-container").appendChild(div);
});

function removeMeld(btn) {
  btn.closest(".meld-item").remove();
}

// 計算ボタン
document.getElementById("calculate-btn").addEventListener("click", async () => {
  const req = buildRequest();
  if (!req) return;

  const section = document.getElementById("result-section");
  const content = document.getElementById("result-content");

  section.classList.remove("hidden");
  content.innerHTML = `<div style="text-align:center;color:var(--text-muted)">計算中...</div>`;

  try {
    const res = await fetch(`${API_BASE}/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    const data = await res.json();
    renderResult(data, content);
  } catch (e) {
    content.innerHTML = `<div class="result-error">通信エラー: ${e.message}</div>`;
  }
});

function buildRequest() {
  const closedRaw = document.getElementById("closed-hand").value.trim();
  const winTile = document.getElementById("win-tile").value.trim();
  const winType = document.querySelector('input[name="win-type"]:checked').value;

  if (!closedRaw || !winTile) {
    alert("手牌と和了牌を入力してください");
    return null;
  }

  const closed = closedRaw.split(/\s+/).filter(Boolean);
  const melds = [];

  document.querySelectorAll(".meld-item").forEach((item) => {
    const type = item.querySelector('[data-role="meld-type"]').value;
    const tilesRaw = item.querySelector('[data-role="meld-tiles"]').value.trim();
    const tiles = tilesRaw.split(/\s+/).filter(Boolean);
    if (tiles.length > 0) {
      melds.push({ type, tiles });
    }
  });

  const doraRaw = document.getElementById("dora").value.trim();
  const uraDoraRaw = document.getElementById("ura-dora").value.trim();

  return {
    hand: { closed, melds },
    win_tile: winTile,
    win_type: winType,
    context: {
      seat_wind: document.getElementById("seat-wind").value,
      round_wind: document.getElementById("round-wind").value,
      is_riichi: document.getElementById("is-riichi").checked,
      is_ippatsu: document.getElementById("is-ippatsu").checked,
      is_haitei: document.getElementById("is-haitei").checked,
      is_houtei: document.getElementById("is-houtei").checked,
      is_rinshan: document.getElementById("is-rinshan").checked,
      is_chankan: document.getElementById("is-chankan").checked,
      dora: doraRaw ? doraRaw.split(/\s+/).filter(Boolean) : [],
      ura_dora: uraDoraRaw ? uraDoraRaw.split(/\s+/).filter(Boolean) : [],
    },
  };
}

function renderResult(data, container) {
  if (!data.is_agari) {
    container.innerHTML = `<div class="result-error">✗ ${ERROR_MESSAGES[data.error] || data.error}</div>`;
    return;
  }

  const isYakuman = data.yaku.some((y) => y.is_yakuman);

  // 役タグ
  const yakuHtml = data.yaku
    .map((y) => {
      const name = YAKU_NAMES[y.name] || y.name;
      const hanStr = y.is_yakuman ? "役満" : `${y.han_closed}翻`;
      const cls = y.is_yakuman ? "yaku-tag yakuman" : "yaku-tag";
      return `<span class="${cls}">${name}（${hanStr}）</span>`;
    })
    .join("");

  // 翻符
  const hanFuHtml = isYakuman
    ? `<div class="han-fu">役満</div>`
    : `<div class="han-fu"><span>${data.han_total}翻</span> ${data.fu_total}符</div>`;

  // 点数
  const payment = data.score.payment;
  let scoreHtml = "";

  if (payment.ron > 0) {
    scoreHtml = `
      <div class="score-grid">
        <div class="score-box ${isYakuman ? "highlight" : ""}">
          <div class="label">ロン</div>
          <div class="value">${payment.ron.toLocaleString()}</div>
        </div>
      </div>`;
  } else {
    const seatWind = document.getElementById("seat-wind").value;
    const isDealer = seatWind === "east";

    if (isDealer) {
      scoreHtml = `
        <div class="score-grid">
          <div class="score-box ${isYakuman ? "highlight" : ""}">
            <div class="label">ツモ（各自）</div>
            <div class="value">${payment.tsumo_non_dealer.toLocaleString()}</div>
          </div>
          <div class="score-box">
            <div class="label">合計</div>
            <div class="value">${(payment.tsumo_non_dealer * 3).toLocaleString()}</div>
          </div>
        </div>`;
    } else {
      scoreHtml = `
        <div class="score-grid">
          <div class="score-box ${isYakuman ? "highlight" : ""}">
            <div class="label">ツモ（親）</div>
            <div class="value">${payment.tsumo_dealer.toLocaleString()}</div>
          </div>
          <div class="score-box ${isYakuman ? "highlight" : ""}">
            <div class="label">ツモ（子）</div>
            <div class="value">${payment.tsumo_non_dealer.toLocaleString()}</div>
          </div>
          <div class="score-box">
            <div class="label">合計</div>
            <div class="value">${(payment.tsumo_dealer + payment.tsumo_non_dealer * 2).toLocaleString()}</div>
          </div>
        </div>`;
    }
  }

  container.innerHTML = `
    <div class="yaku-list">${yakuHtml}</div>
    ${hanFuHtml}
    ${scoreHtml}
  `;
}
