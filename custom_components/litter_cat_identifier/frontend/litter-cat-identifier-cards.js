/*
 * Litter Cat Identifier – dashboard cards.
 * Served by the integration and loaded automatically; no HACS frontend install needed.
 *   custom:litter-cat-identifier-cats     photo, name, weight, visits today, last visit
 *   custom:litter-cat-identifier-visits   recent visits with reasons for unidentified readings
 *   custom:litter-cat-identifier-weight   weight history per cat (statistics graph)
 * All cards auto-detect the litter box; set `device_id` when you have more than one.
 */

const DOMAIN = "litter_cat_identifier";

const I18N = {
  en: {
    cats: "Cats", visits: "Recent visits", weight: "Weight", none: "No visits yet",
    time: "Time", cat: "Cat", kg: "Weight", dur: "Duration",
    today: (n) => `${n} today`, last: "last", never: "no visits yet",
    unidentified: "Unidentified cat",
    partial: (c) => `Probably ${c} half inside, right after the visit`,
    noWeight: "Visit detected without a weight",
    refill: "Probably a litter refill or a cat half inside",
    notFound: "No Litter Cat Identifier litter box found.",
    days: (d) => `${d} days`,
  },
  es: {
    cats: "Gatos", visits: "Últimas visitas", weight: "Peso", none: "Sin visitas todavía",
    time: "Hora", cat: "Gato", kg: "Peso", dur: "Duración",
    today: (n) => `${n} hoy`, last: "última", never: "sin visitas",
    unidentified: "Gato no identificado",
    partial: (c) => `Posible ${c} medio dentro, justo tras su visita`,
    noWeight: "Visita detectada sin peso",
    refill: "Probablemente relleno de arena o un gato medio dentro",
    notFound: "No se encontró ningún arenero de Litter Cat Identifier.",
    days: (d) => `${d} días`,
  },
};

const t = (hass) => {
  const lang = (hass?.locale?.language || hass?.language || "en").split("-")[0];
  return I18N[lang] || I18N.en;
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** Collect the integration's entities for one litter box. */
function findBox(hass, deviceId) {
  const ents = Object.values(hass.entities || {}).filter((e) => e.platform === DOMAIN);
  const devices = [...new Set(ents.map((e) => e.device_id).filter(Boolean))];
  const dev = deviceId || devices[0];
  if (!dev) return null;
  const mine = ents.filter((e) => e.device_id === dev);
  const byKey = (k) => mine.filter((e) => e.translation_key === k).map((e) => e.entity_id);
  const catOf = (id) => hass.states[id]?.attributes?.cat;
  const cats = {};
  for (const [key, field] of [["cat_weight", "weight"], ["cat_visits_today", "visits"], ["cat_last_visit", "last"]]) {
    for (const id of byKey(key)) {
      const name = catOf(id);
      if (!name) continue;
      (cats[name] ||= { name })[field] = id;
    }
  }
  return {
    device: dev,
    lastVisit: byKey("last_visit")[0],
    unidentified: byKey("unidentified_today")[0],
    cats: Object.values(cats),
  };
}

const fmtTime = (hass, iso, withDate) => {
  const d = new Date(iso);
  if (isNaN(d)) return "–";
  const opts = withDate
    ? { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }
    : { hour: "2-digit", minute: "2-digit" };
  return d.toLocaleString(hass?.locale?.language || hass?.language || undefined, opts);
};

const moreInfo = (el, entityId) =>
  el.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));

class BaseCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._sig = null;
  }
  set hass(hass) {
    this._hass = hass;
    const box = findBox(hass, this._config.device_id);
    const sig = this.signature(hass, box);
    if (sig === this._sig) return;
    this._sig = sig;
    this.render(hass, box);
  }
  signature(hass, box) {
    if (!box) return "none";
    const ids = [box.lastVisit, box.unidentified, ...box.cats.flatMap((c) => [c.weight, c.visits, c.last])];
    return ids.map((id) => hass.states[id]?.last_updated).join("|") + (hass.locale?.language || "");
  }
  shell(title, body) {
    this.innerHTML = `
      <ha-card ${title ? `header="${esc(title)}"` : ""}>
        <div class="lci">${body}</div>
      </ha-card>
      <style>
        .lci { padding: 0 16px 16px; }
        ha-card:not([header]) .lci { padding-top: 16px; }
        .lci-empty { color: var(--secondary-text-color); }
        .lci-cats { display: grid; grid-template-columns: repeat(var(--lci-cols, 2), minmax(0, 1fr)); gap: 12px; }
        .lci-cat { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 12px;
                   background: var(--secondary-background-color); cursor: pointer; min-width: 0; }
        .lci-avatar { width: 52px; height: 52px; border-radius: 50%; flex: none; object-fit: cover;
                      display: flex; align-items: center; justify-content: center;
                      background: var(--primary-background-color); color: var(--primary-color); }
        .lci-name { font-weight: 600; font-size: 1.05em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .lci-kg { font-size: 1.3em; font-weight: 500; }
        .lci-sub { color: var(--secondary-text-color); font-size: 0.85em; }
        .lci table { width: 100%; border-collapse: collapse; font-size: 0.95em; }
        .lci th { text-align: left; font-weight: 500; color: var(--secondary-text-color); padding: 4px 6px; }
        .lci td { padding: 6px; border-top: 1px solid var(--divider-color); }
        .lci .num { text-align: right; white-space: nowrap; }
        .lci .q { cursor: help; color: var(--primary-color); font-weight: 600; margin-left: 4px; }
      </style>`;
  }
  getCardSize() { return 3; }
}

/* ---------- cats ---------- */
class CatsCard extends BaseCard {
  static getStubConfig() { return {}; }
  render(hass, box) {
    const T = t(hass);
    const title = this._config.title ?? T.cats;
    if (!box) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const tiles = box.cats.map((c) => {
      const w = hass.states[c.weight];
      const pic = w?.attributes?.entity_picture;
      const kg = w && !isNaN(parseFloat(w.state)) ? `${parseFloat(w.state).toFixed(2)} kg` : "–";
      const visits = hass.states[c.visits]?.state ?? "0";
      const last = hass.states[c.last]?.state;
      const lastTxt = last && !["unknown", "unavailable"].includes(last) ? `${T.last} ${fmtTime(hass, last)}` : T.never;
      const avatar = pic
        ? `<img class="lci-avatar" src="${esc(pic)}" alt="">`
        : `<div class="lci-avatar"><ha-icon icon="mdi:cat"></ha-icon></div>`;
      return `<div class="lci-cat" data-entity="${esc(c.weight)}">${avatar}
        <div style="min-width:0"><div class="lci-name">${esc(c.name)}</div>
        <div class="lci-kg">${kg}</div><div class="lci-sub">${T.today(esc(visits))} · ${lastTxt}</div></div></div>`;
    });
    this.shell(title, `<div class="lci-cats" style="--lci-cols:${Number(this._config.columns) || 2}">${tiles.join("")}</div>`);
    this.querySelectorAll(".lci-cat").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.entity)));
  }
  getCardSize() { return 2; }
}

/* ---------- visits ---------- */
class VisitsCard extends BaseCard {
  static getStubConfig() { return { count: 8 }; }
  render(hass, box) {
    const T = t(hass);
    const title = this._config.title ?? T.visits;
    if (!box || !box.lastVisit) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const history = hass.states[box.lastVisit]?.attributes?.history || [];
    if (!history.length) return this.shell(title, `<div class="lci-empty">${T.none}</div>`);
    const rows = history.slice(0, Number(this._config.count) || 8).map((v) => {
      let cat = esc(v.cat);
      if (v.cat === "unidentified") {
        const tip = v.reason === "partial_after_visit" ? T.partial(v.likely_cat || "?")
          : v.reason === "no_weight" ? T.noWeight : T.refill;
        cat = `${T.unidentified}<span class="q" title="${esc(tip)}">(?)</span>`;
      }
      const kg = typeof v.weight === "number" ? `${v.weight.toFixed(2)} kg` : "–";
      const dur = typeof v.duration === "number" ? `${Math.round(v.duration)} s` : "–";
      return `<tr><td>${fmtTime(hass, v.time, true)}</td><td>${cat}</td><td class="num">${kg}</td><td class="num">${dur}</td></tr>`;
    });
    this.shell(title, `<table><tr><th>${T.time}</th><th>${T.cat}</th><th class="num">${T.kg}</th><th class="num">${T.dur}</th></tr>${rows.join("")}</table>`);
    // touch screens have no hover: tap the (?) to read the reason
    this.querySelectorAll(".q").forEach((q) =>
      q.addEventListener("click", () => {
        const showing = q.dataset.open === "1";
        q.textContent = showing ? "(?)" : `(${q.title})`;
        q.dataset.open = showing ? "0" : "1";
      })
    );
  }
  getCardSize() { return 4; }
}

/* ---------- weight ---------- */
class WeightCard extends BaseCard {
  static getStubConfig() { return { days: 7 }; }
  async render(hass, box) {
    const T = t(hass);
    const days = Number(this._config.days) || 7;
    const title = this._config.title ?? `${T.weight} (${T.days(days)})`;
    if (!box || !box.cats.length) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const cfg = {
      type: "statistics-graph",
      title,
      days_to_show: days,
      period: this._config.period || (days <= 14 ? "hour" : days <= 90 ? "day" : "week"),
      stat_types: ["mean"],
      chart_type: "line",
      entities: box.cats.map((c) => ({ entity: c.weight, name: c.name })),
    };
    const key = JSON.stringify(cfg);
    if (this._graphKey !== key) {
      this._graphKey = key;
      const helpers = await window.loadCardHelpers();
      this._graph = helpers.createCardElement(cfg);
      this.innerHTML = "";
      this.appendChild(this._graph);
    }
    this._graph.hass = hass;
  }
  signature(hass, box) {
    // the graph fetches its own statistics; only rebuild when cats change
    return (box?.cats || []).map((c) => c.weight + c.name).join("|") + (hass.locale?.language || "");
  }
  set hass(hass) {
    super.hass = hass;
    if (this._graph) this._graph.hass = hass;
  }
  getCardSize() { return 5; }
}

const define = (tag, cls) => { if (!customElements.get(tag)) customElements.define(tag, cls); };
define("litter-cat-identifier-cats", CatsCard);
define("litter-cat-identifier-visits", VisitsCard);
define("litter-cat-identifier-weight", WeightCard);

window.customCards = window.customCards || [];
for (const [type, name, description] of [
  ["litter-cat-identifier-cats", "Litter Cat Identifier – Cats", "Photo, name, weight, visits today and last visit for each cat."],
  ["litter-cat-identifier-visits", "Litter Cat Identifier – Recent visits", "Latest litter box visits, with the likely reason for unidentified readings."],
  ["litter-cat-identifier-weight", "Litter Cat Identifier – Weight", "Weight history of each cat."],
]) {
  if (!window.customCards.some((c) => c.type === type)) {
    window.customCards.push({ type, name, description, preview: true,
      documentationURL: "https://github.com/cruzpazv/litter-cat-identifier#dashboard-cards" });
  }
}
