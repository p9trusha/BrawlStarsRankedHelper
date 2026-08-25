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
  for (const m of filtered) {
    const card = document.createElement("div");
    card.className = "map-card" + (state.selectedMap?.slug === m.slug ? " active" : "");
    card.innerHTML = `
      <img class="map-img" src="${m.image}" alt="${m.name}" loading="lazy" />
      <div class="map-name">${m.name}</div>
      <div class="map-mode">${m.mode}</div>`;
    card.onclick = () => selectMap(m);
    grid.appendChild(card);
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
  const byName = {};
  for (const s of state.stats) byName[s.brawler.toUpperCase()] = s;

  const onlyMax = $("powerFilter") ? $("powerFilter").checked : false;
  const tmax = Math.max(...state.owned.brawlers.map((b) => b.trophies || 0), 1);
  const recs = [];
  for (const b of state.owned.brawlers) {
    const s = byName[b.name.toUpperCase()];
    if (!s) continue;
    if (onlyMax && b.power < 11) continue;
    const tp = Math.min(((b.trophies || 0) / tmax) * 100, 100);
    const score =
      0.5 * (s.winRate || 0) +
      0.25 * (s.pickRate || 0) +
      0.25 * tp;
    recs.push({ ...b, ...s, score });
  }
  recs.sort((a, b) => b.score - a.score);

  if (!recs.length) {
    body.innerHTML =
      '<div class="empty">Никто из твоих бойцов не попал в статистику этой карты.</div>';
    return;
  }

  const ownedCount = recs.length;
  const table = `
    <div class="pills">
      <span class="pill">Бойцов с данными на карте: <b>${ownedCount}</b></span>
      <span class="pill">Лучший выбор: <b>${recs[0].name}</b> (рейтинг ${recs[0].score.toFixed(1)})</span>
    </div>
    <label class="check">
      <input type="checkbox" id="powerFilter" ${onlyMax ? "checked" : ""} />
       Только бойцы с power ≥ 11 (подходят для ранга)
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
            <td class="num">${fmt(r.winRate)}%</td>
            <td class="num">${fmt(r.pickRate)}%</td>
            <td class="num">${fmt(r.starRate)}%</td>
            <td class="num">${fmt(r.trophies)}</td>
            <td class="num">${r.score.toFixed(1)}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
    <div class="note">Сортировка по рейтингу: 0.5·винрейт + 0.25·пикрейт + 0.25·наигранность (${state.statsMeta?.tierName || state.tierName}). Данные Brawl Planet.</div>`;

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