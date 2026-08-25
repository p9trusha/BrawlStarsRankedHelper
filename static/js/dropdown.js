import { state, $ } from "./core.js";

export function renderTierDropdown() {
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
