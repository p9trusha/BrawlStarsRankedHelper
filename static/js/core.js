/**
 * @typedef {Object} MapInfo
 * @property {string} name
 * @property {string} mode
 * @property {string} modeSlug
 * @property {string} modeIcon
 * @property {string} slug
 * @property {string} image
 * @property {number|null} [matchCount]
 */

/**
 * @typedef {Object} AppState
 * @property {string} tier
 * @property {string} tierName
 * @property {Array<{value: string, name: string, icon: string}>} leagues
 * @property {MapInfo[]} maps
 * @property {any} owned
 * @property {string} tag
 * @property {MapInfo|null} selectedMap
 * @property {any} recs
 * @property {string|null} openMode
 * @property {"ban"|"pick"} mode
 */

/** @type {AppState} */
export const state = {
  tier: "pl",
  tierName: "Diamond I+",
  leagues: [],
  maps: [],
  owned: null,
  tag: "",
  selectedMap: null,
  recs: null,
  openMode: null,
  mode: "ban",
};

export const $ = (id) => document.getElementById(id);

const ESC_MAP = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

export function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ESC_MAP[c]);
}

export function fmt(v) {
  return v == null ? "—" : Number(v).toFixed(1);
}

export async function api(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Ошибка ${res.status}`);
  return data;
}
