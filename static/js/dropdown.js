import { state, $, esc } from "./core.js";

export function renderTierDropdown() {
  const box = $("tierDropdown");
  if (!state.leagues.length) return;
  const cur =
    state.leagues.find((l) => l.value === state.tier) || state.leagues[0];
  box.innerHTML = `
    <button type="button" class="dropdown-btn">
      ${cur.icon ? `<img class="rank-icon" src="${esc(cur.icon)}" alt="" />` : ""}
      <span>${esc(cur.name)}</span><span class="caret">▾</span>
    </button>
    <div class="dropdown-list">
      ${state.leagues
        .map(
          (l) => `
        <button type="button" class="dropdown-item${l.value === state.tier ? " active" : ""}" data-tier="${esc(l.value)}">
          ${l.icon ? `<img class="rank-icon" src="${esc(l.icon)}" alt="" />` : ""}
          <span>${esc(l.name)}</span>
        </button>`,
        )
        .join("")}
    </div>`;
}
