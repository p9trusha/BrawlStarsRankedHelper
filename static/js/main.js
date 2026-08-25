import { state, $ } from "./core.js";
import { loadRecommendation } from "./recommendations.js";
import { renderMaps, loadMaps } from "./maps.js";
import { loadPlayer, switchTier } from "./player.js";

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

$("loadBtn").onclick = loadPlayer;
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.onclick = () => {
    if (state.mode === btn.dataset.mode) return;
    state.mode = btn.dataset.mode;
    document
      .querySelectorAll(".tab-btn")
      .forEach((b) => b.classList.toggle("active", b === btn));
    loadRecommendation();
  };
});
$("tagInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadPlayer();
});
$("mapSearch").addEventListener(
  "input",
  debounce(() => renderMaps(), 250),
);
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
