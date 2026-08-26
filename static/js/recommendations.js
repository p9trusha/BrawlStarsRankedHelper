import { state, $, fmt, api, esc } from "./core.js";

const recBody = $("recBody");

let requestSeq = 0;

export function activateMode(mode) {
  state.mode = mode;
  document
    .querySelectorAll(".tab-btn")
    .forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
}

export async function loadRecommendation() {
  const body = recBody;
  const seq = ++requestSeq;
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
  });
  const url =
    state.mode === "ban"
      ? `/api/ban-recommend?${params}`
      : `/api/recommend?${params}`;
  try {
    const data = await api(url);
    if (seq !== requestSeq) return;
    state.recs = data;
    if (state.mode === "ban") renderBanRecommendation();
    else renderRecommendation();
  } catch (e) {
    if (seq !== requestSeq) return;
    body.innerHTML = `<div class="error">${esc(e.message)}</div>`;
  }
}

function renderRecommendation() {
  const body = recBody;
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
      ${d.topWeak ? `<span class="pill warn-pill">Все твои бойцы на этой карте с винрейтом &lt; 50%. Лучший из доступных: <b>${esc(recs[0].name)}</b></span>` : ""}
      <span class="pill">Лучший выбор: <b>${esc(recs[0].name)}</b> (рейтинг ${Number(recs[0].score).toFixed(1)})</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Боец</th>
          <th class="num">Сила</th>
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
                ${r.icon ? `<img src="${esc(r.icon)}" alt="${esc(r.name)}" />` : ""}
                <span>${esc(r.name)}</span>
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
      Рейтинг = 0.7·винрейт + 0.3·наигранность (нормированы 0–100 по твоему пулу, ${esc(d.tierName || state.tierName)}). Винрейт скорректирован по пикрейту: редкие пики тянутся к 50%. Винрейт ниже 50% подсвечен красным.
    </div>`;

  body.innerHTML = table;
}

function renderBanRecommendation() {
  const body = recBody;
  if (!state.recs) {
    body.innerHTML =
      '<div class="empty">Сначала загрузи игрока в шаге 1, чтобы увидеть кандидатов на бан.</div>';
    return;
  }
  const d = state.recs;
  const recs = d.recommendations || [];
  if (!recs.length) {
    body.innerHTML =
      '<div class="empty">Никто из твоих бойцов не попал в статистику этой карты.</div>';
    return;
  }
  const minPower = d.minPower;
  const table = `
    <div class="pills">
      <span class="pill">Кандидатов: <b>${recs.length}</b></span>
      <span class="pill">Лучший бан: <b>${esc(recs[0].name)}</b> (рейтинг ${Number(recs[0].score).toFixed(1)})</span>
      <span class="pill">Мин. сила в лиге: <b>P${minPower}</b></span>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Боец</th>
          <th class="num">Сила</th>
          <th class="num">Трофеи</th>
          <th class="num">Винрейт</th>
          <th class="num">Пикрейт</th>
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
                ${r.icon ? `<img src="${esc(r.icon)}" alt="${esc(r.name)}" />` : ""}
                <span>${esc(r.name)}</span>
                ${r.locked ? `<span class="lock-badge">нет силы ${minPower} — бан бесплатный</span>` : ""}
              </div>
            </td>
            <td class="num">${r.power}</td>
            <td class="num">${r.trophies}</td>
            <td class="num${r.winRate < 50 ? " bad" : ""}">${fmt(r.winRate)}%</td>
            <td class="num">${fmt(r.pickRate)}%</td>
            <td class="num">${Number(r.score).toFixed(1)}</td>
          </tr>`,
          )
          .join("")}
      </tbody>
    </table>
    <div class="note">
      Рейтинг бана = винрейт + пикрейт − трофеи (нормированы 0–100 по твоему пулу, ${esc(d.tierName || state.tierName)}). Бан глобальный: боец исчезнет и у соперников, и у тебя. Если у бойца нет требуемой силы (P${minPower}), он получает бонус — терять его не страшно, а из чужого пула он пропадёт. Трофеи вычитаются только у бойцов с нужной силой: чем меньше наигран, тем меньше жаль терять.
    </div>`;

  body.innerHTML = table;
}
