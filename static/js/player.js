import { state, $, api } from "./core.js";
import { loadRecommendation } from "./recommendations.js";
import { renderTierDropdown } from "./dropdown.js";
import { loadMaps } from "./maps.js";

export async function loadPlayer() {
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

export function switchTier(tier) {
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
