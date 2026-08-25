const state = {
  tier: "pl",
  tierName: "Diamond I+",
  maps: [],
  owned: null,
  selectedMap: null,
  stats: null,
  statsMeta: null,
};

const $ = (id) => document.getElementById(id);

function fmt(v) {
  return v == null ? "—" : Number(v).toFixed(1);
}

async function api(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Ошибка ${res.status}`);
  return data;
}

async function loadMaps() {
  const grid = $("mapGrid");
  try {
    const data = await api(`/api/ranked-maps?tier=${encodeURIComponent(state.tier)}`);
    state.maps = data.maps || [];
    state.tierName = data.tierName || state.tier;
    if (!state.maps.length) {
      grid.className = "empty";
      grid.textContent = "Карты не найдены.";
      return;
    }
    renderMaps();
  } catch (e) {
    grid.className = "error";
    grid.textContent = "Не удалось загрузить карты: " + e.message;
  }
}

function renderMaps() {
  const q = $("mapSearch").value.trim().toLowerCase();
  const grid = $("mapGrid");
  grid.className = "";
  grid.innerHTML = "";
  const filtered = state.maps.filter(
    (m) => m.name.toLowerCase().includes(q) || m.mode.toLowerCase().includes(q)
  );
  if (!filtered.length) {
    grid.className = "empty";
    grid.textContent = "Ничего не найдено.";
    return;
  }
  const groups = [];
  for (const m of filtered) {
    const last = groups[groups.length - 1];
    if (last && last.mode === m.mode) last.maps.push(m);
    else groups.push({ mode: m.mode, icon: m.modeIcon, maps: [m] });
  }
  for (const g of groups) {
    const group = document.createElement("div");
    group.className = "mode-group";
    group.innerHTML = `
      <div class="mode-header">
        ${g.icon ? `<img src="${g.icon}" alt="" />` : ""}
        <span>${g.mode}</span>
      </div>
      <div class="mode-grid"></div>`;
    const cards = group.querySelector(".mode-grid");
    for (const m of g.maps) {
      const card = document.createElement("div");
      card.className = "map-card" + (state.selectedMap?.slug === m.slug ? " active" : "");
      card.innerHTML = `
        <img class="map-img" src="${m.image}" alt="${m.name}" loading="lazy" />
        <div class="map-name">${m.name}</div>`;
      card.onclick = () => selectMap(m);
      cards.appendChild(card);
    }
    grid.appendChild(group);
  }
}

async function selectMap(m) {
  state.selectedMap = m;
  renderMaps();
  const panel = $("recPanel");
  panel.hidden = false;
  $("recTitle").textContent = `3. Рекомендация — ${m.name} (${m.mode})`;
  const body = $("recBody");
  body.innerHTML = '<div class="loading">Загружаю статистику карты...</div>';
  try {
    const data = await api(
      `/api/map/${encodeURIComponent(m.slug)}/stats?tier=${encodeURIComponent(state.tier)}`
    );
    state.stats = data.individual || [];
    state.statsMeta = data;
    renderRecommendation();
  } catch (e) {
    body.innerHTML = `<div class="error">${e.message}</div>`;
  }
}

function renderRecommendation() {
  const body = $("recBody");
  if (!state.owned) {
    body.innerHTML =
      '<div class="empty">Сначала загрузи игрока в шаге 1, чтобы увидеть рекомендацию именно для твоих бойцов.</div>';
    return;
  }
  const minPower = state.tier === "pl" ? 9 : 11;
  const byName = {};
  for (const s of state.stats) byName[s.brawler.toUpperCase()] = s;

  const onlyMax = $("powerFilter") ? $("powerFilter").checked : true;
  const tmax = Math.max(...state.owned.brawlers.map((b) => b.trophies || 0), 1);
  const recs = [];
  for (const b of state.owned.brawlers) {
    const s = byName[b.name.toUpperCase()];
    if (!s) continue;
    if (onlyMax && b.power < minPower) continue;
    recs.push({
      ...b,
      ...s,
      tp: Math.min(((b.trophies || 0) / tmax) * 100, 100),
      wrAdj: 50 + ((s.winRate - 50) * s.pickRate) / (s.pickRate + 8),
    });
  }
  if (!recs.length) {
    body.innerHTML =
      '<div class="empty">Никто из твоих бойцов не попал в статистику этой карты.</div>';
    return;
  }

  const norm = (v, lo, hi) => (hi > lo ? ((v - lo) / (hi - lo)) * 100 : 50);
  const rng = (key) => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const r of recs) {
      lo = Math.min(lo, r[key]);
      hi = Math.max(hi, r[key]);
    }
    return [lo, hi];
  };
  const [wrLo, wrHi] = rng("wrAdj");
  const [tpLo, tpHi] = rng("tp");
  for (const r of recs) {
    r.score =
      0.7 * norm(r.wrAdj, wrLo, wrHi) +
      0.3 * norm(r.tp, tpLo, tpHi);
  }
  recs.sort((a, b) => b.score - a.score);

  const ownedCount = recs.length;
  const topWeak = recs[0].winRate < 50;
  const table = `
    <div class="pills">
      <span class="pill">Бойцов с данными на карте: <b>${ownedCount}</b></span>
      ${topWeak ? '<span class="pill warn-pill">Все твои бойцы на этой карте с винрейтом &lt; 50%. Лучший из доступных: <b>' + recs[0].name + "</b></span>" : ""}
      <span class="pill">Лучший выбор: <b>${recs[0].name}</b> (рейтинг ${recs[0].score.toFixed(1)})</span>
    </div>
    <label class="check">
      <input type="checkbox" id="powerFilter" ${onlyMax ? "checked" : ""} />
       Только бойцы с power ≥ ${minPower}
    </label>
    <table>
      <thead>
        <tr>
          <th>#</th><th>Боец</th><th class="num">Power</th>
          <th class="num">Винрейт</th>
          <th class="num">Пикрейт</th>
          <th class="num">Star player</th>
          <th class="num">Трофеи</th>
          <th class="num">Рейтинг</th>
        </tr>
      </thead>
      <tbody>
        ${recs
          .map(
            (r, i) => `
          <tr>
            <td><span class="rank-badge">${i + 1}</span></td>
            <td>
              <div class="brawler-cell">
                ${r.icon ? `<img src="${r.icon}" alt="${r.name}" />` : ""}
                <span>${r.name}</span>
              </div>
            </td>
            <td class="num">${r.power}</td>
            <td class="num${r.winRate < 50 ? " bad" : ""}">${fmt(r.winRate)}%</td>
            <td class="num">${fmt(r.pickRate)}%</td>
            <td class="num">${fmt(r.starRate)}%</td>
            <td class="num">${r.trophies}</td>
            <td class="num">${r.score.toFixed(1)}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
    <div class="note">
    Рейтинг = 0.7·винрейт + 0.3·наигранность (нормированы 0–100 по твоему пулу, ${state.statsMeta?.tierName || state.tierName}). Винрейт скорректирован по пикрейту: редкие пики тянутся к 50%. Винрейт ниже 50% подсвечен красным. Данные Brawl Planet.
    </div>`;

  body.innerHTML = table;
  $("powerFilter").onchange = renderRecommendation;
}

async function loadPlayer() {
  const info = $("playerInfo");
  const btn = $("loadBtn");
  const tag = $("tagInput").value.trim();
  if (!tag) {
    info.className = "error";
    info.textContent = "Введи тег игрока.";
    return;
  }
  btn.disabled = true;
  info.className = "loading";
  info.textContent = "Загружаю аккаунт...";
  try {
    state.owned = await api(`/api/player/${encodeURIComponent(tag)}`);
    const countBrawlersPower9Plus = state.owned.brawlers.filter((b) => b.power >= 9).length;
    const countBrawlersPower11 = state.owned.brawlers.filter((b) => b.power >= 11).length;
    info.className = "ok";
    info.textContent =
      `${state.owned.name || tag}: ${state.owned.brawlers.length} бойцов, ` +
      `${countBrawlersPower9Plus} с силой ≥ 9, ` +
      `${countBrawlersPower11} с силой 11.`;
    if (state.stats) renderRecommendation();
  } catch (e) {
    state.owned = null;
    info.className = "error";
    info.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
}

$("loadBtn").onclick = loadPlayer;
$("tagInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadPlayer();
});
$("mapSearch").addEventListener("input", renderMaps);
$("tierSelect").addEventListener("change", (e) => {
  state.tier = e.target.value;
  state.selectedMap = null;
  state.stats = null;
  state.statsMeta = null;
  const panel = $("recPanel");
  panel.hidden = true;
  const grid = $("mapGrid");
  grid.className = "loading";
  grid.textContent = "Загружаю карты...";
  loadMaps();
});

loadMaps();
