const state = {
  tier: "pl",
  tierName: "Diamond I+",
  leagues: [],
  maps: [],
  owned: null,
  tag: "",
  selectedMap: null,
  recs: null,
  onlyMax: true,
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
    const data = await api(
      `/api/ranked-maps?tier=${encodeURIComponent(state.tier)}`,
    );
    state.maps = data.maps || [];
    state.leagues = data.leagues || [];
    state.tierName = data.tierName || state.tier;
    renderTierDropdown();
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
    (m) => m.name.toLowerCase().includes(q) || m.mode.toLowerCase().includes(q),
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
      card.className =
        "map-card" + (state.selectedMap?.slug === m.slug ? " active" : "");
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
  loadRecommendation();
}

async function loadRecommendation() {
  const body = $("recBody");
  if (!state.owned || !state.selectedMap) {
    body.innerHTML =
      '<div class="empty">Сначала загрузи игрока в шаге 1, чтобы увидеть рекомендацию именно для твоих бойцов.</div>';
    return;
  }
  body.innerHTML = '<div class="loading">Считаю рейтинг...</div>';
  const params = new URLSearchParams({
    tag: state.tag,
    map: state.selectedMap.slug,
    tier: state.tier,
    onlyMax: state.onlyMax ? "1" : "0",
  });
  try {
    const data = await api(`/api/recommend?${params}`);
    state.recs = data;
    renderRecommendation();
  } catch (e) {
    body.innerHTML = `<div class="error">${e.message}</div>`;
  }
}

function renderRecommendation() {
  const body = $("recBody");
  if (!state.recs) {
    body.innerHTML =
      '<div class="empty">Сначала загрузи игрока в шаге 1, чтобы увидеть рекомендацию именно для твоих бойцов.</div>';
    return;
  }
  const d = state.recs;
  const recs = d.recommendations || [];
  if (!recs.length) {
    body.innerHTML =
      '<div class="empty">Никто из твоих бойцов не попал в статистику этой карты.</div>';
    return;
  }
  const table = `
    <div class="pills">
      <span class="pill">Бойцов с данными на карте: <b>${recs.length}</b></span>
      ${d.topWeak ? `<span class="pill warn-pill">Все твои бойцы на этой карте с винрейтом &lt; 50%. Лучший из доступных: <b>${recs[0].name}</b></span>` : ""}
      <span class="pill">Лучший выбор: <b>${recs[0].name}</b> (рейтинг ${recs[0].score.toFixed(1)})</span>
    </div>
    <label class="check">
      <input type="checkbox" id="powerFilter" ${state.onlyMax ? "checked" : ""} />
       Только бойцы с power ≥ ${d.minPower}
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
            <td class="num">${Number(r.score).toFixed(1)}</td>
          </tr>`,
          )
          .join("")}
      </tbody>
    </table>
    <div class="note">
      Рейтинг = 0.7·винрейт + 0.3·наигранность (нормированы 0–100 по твоему пулу, ${d.tierName || state.tierName}). Винрейт скорректирован по пикрейту: редкие пики тянутся к 50%. Винрейт ниже 50% подсвечен красным.
    </div>`;

  body.innerHTML = table;
  $("powerFilter").onchange = () => {
    state.onlyMax = $("powerFilter").checked;
    loadRecommendation();
  };
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
    state.tag = tag;
    localStorage.setItem("bsh:tag", state.tag);
    state.recs = null;
    const countBrawlersPower9Plus = state.owned.brawlers.filter(
      (b) => b.power >= 9,
    ).length;
    const countBrawlersPower11 = state.owned.brawlers.filter(
      (b) => b.power >= 11,
    ).length;
    info.className = "ok";
    info.textContent =
      `${state.owned.name || tag}: ${state.owned.brawlers.length} бойцов, ` +
      `${countBrawlersPower9Plus} с силой ≥ 9, ` +
      `${countBrawlersPower11} с силой 11.`;
    const ranked = state.owned.ranked || {};
    if (ranked.name) {
      if (ranked.icon) {
        const img = document.createElement("img");
        img.src = ranked.icon;
        img.alt = "";
        img.className = "rank-icon";
        info.append(img);
      }
      info.append(` Ранг: ${ranked.name}${ranked.elo ? ` (${ranked.elo})` : ""}.`);
    }
    if (
      state.owned.recommendedTier &&
      state.owned.recommendedTier !== state.tier
    ) {
      switchTier(state.owned.recommendedTier);
      return;
    }
    if (state.selectedMap) loadRecommendation();
  } catch (e) {
    state.owned = null;
    state.tag = "";
    state.recs = null;
    info.className = "error";
    info.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
}

function switchTier(tier) {
  state.tier = tier;
  state.selectedMap = null;
  state.recs = null;
  renderTierDropdown();
  const panel = $("recPanel");
  panel.hidden = true;
  const grid = $("mapGrid");
  grid.className = "loading";
  grid.textContent = "Загружаю карты...";
  loadMaps();
}

function renderTierDropdown() {
  const box = $("tierDropdown");
  if (!state.leagues.length) return;
  const cur =
    state.leagues.find((l) => l.value === state.tier) || state.leagues[0];
  box.innerHTML = `
    <button type="button" class="dropdown-btn">
      ${cur.icon ? `<img class="rank-icon" src="${cur.icon}" alt="" />` : ""}
      <span>${cur.name}</span><span class="caret">▾</span>
    </button>
    <div class="dropdown-list">
      ${state.leagues
        .map(
          (l) => `
        <button type="button" class="dropdown-item${l.value === state.tier ? " active" : ""}" data-tier="${l.value}">
          ${l.icon ? `<img class="rank-icon" src="${l.icon}" alt="" />` : ""}
          <span>${l.name}</span>
        </button>`,
        )
        .join("")}
    </div>`;
}

$("loadBtn").onclick = loadPlayer;
$("tagInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadPlayer();
});
$("mapSearch").addEventListener("input", renderMaps);
$("tierDropdown").addEventListener("click", (e) => {
  const item = e.target.closest(".dropdown-item");
  if (item) {
    $("tierDropdown").classList.remove("open");
    switchTier(item.dataset.tier);
    return;
  }
  if (e.target.closest(".dropdown-btn")) {
    $("tierDropdown").classList.toggle("open");
  }
});
document.addEventListener("click", (e) => {
  if (!e.target.closest("#tierDropdown")) {
    $("tierDropdown").classList.remove("open");
  }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("tierDropdown").classList.remove("open");
});

const savedTag = localStorage.getItem("bsh:tag");
if (savedTag) {
  $("tagInput").value = savedTag;
  loadPlayer();
}
loadMaps();
