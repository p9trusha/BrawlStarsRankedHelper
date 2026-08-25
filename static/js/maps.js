import { state, $, api, esc } from "./core.js";
import { renderTierDropdown } from "./dropdown.js";
import { loadRecommendation } from "./recommendations.js";

export async function loadMaps() {
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

export function renderMaps() {
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
  const searching = q.length > 0;
  for (const g of groups) {
    const expanded = searching || state.openMode === g.mode;
    const group = document.createElement("div");
    group.className = "mode-group" + (expanded ? "" : " collapsed");
    group.innerHTML = `
      <button type="button" class="mode-header">
        ${g.icon ? `<img src="${esc(g.icon)}" alt="" />` : ""}
        <span class="mode-name">${esc(g.mode)}</span>
        <span class="mode-count">${g.maps.length}</span>
        <span class="caret">▾</span>
      </button>
      <div class="mode-grid"></div>`;
    if (expanded) {
      const cards = group.querySelector(".mode-grid");
      for (const m of g.maps) {
        const card = document.createElement("div");
        card.className =
          "map-card" + (state.selectedMap?.slug === m.slug ? " active" : "");
        card.innerHTML = `
          <img class="map-img" src="${esc(m.image)}" alt="${esc(m.name)}" loading="lazy" />
          <div class="map-name">${esc(m.name)}</div>`;
        card.onclick = () => selectMap(m);
        cards.appendChild(card);
      }
    }
    group.querySelector(".mode-header").onclick = () => {
      state.openMode = state.openMode === g.mode ? null : g.mode;
      renderMaps();
    };
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
