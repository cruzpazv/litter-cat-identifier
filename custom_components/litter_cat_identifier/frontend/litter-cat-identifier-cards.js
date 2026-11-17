/*
 * Litter Cat Identifier – dashboard cards.
 * Served by the integration and loaded automatically; no HACS frontend install needed.
 *   custom:litter-cat-identifier-cats     photo, name, weight, visits today, last visit
 *   custom:litter-cat-identifier-visits   recent visits with reasons for unidentified readings
 *   custom:litter-cat-identifier-weight   weight history per cat (statistics graph)
 *   custom:litter-cat-identifier-box      clean now, auto-clean, today's summary
 * All cards auto-detect the litter box; set `device_id` when you have more than one.
 * Every card has a visual editor.
 */

const DOMAIN = "litter_cat_identifier";

const I18N = {
  en: {
    cats: "Cats", visits: "Recent visits", weight: "Weight", box: "Litter box", none: "No visits yet",
    time: "Time", cat: "Cat", kg: "Weight", dur: "Duration",
    today: (n) => `${n} today`, last: "last", never: "no visits yet",
    unidentified: "Unidentified cat",
    partial: (c) => `Probably ${c} half inside, right after the visit`,
    noWeight: "Visit detected without a weight",
    refill: "Probably a litter refill or a cat half inside",
    notFound: "No Litter Cat Identifier litter box found.",
    days: (d) => `${d} days`,
    hide: "Hide unidentified", show: (n) => `Show unidentified (${n} hidden)`,
    clean: "Clean now", cleaning: "Cleaning…", confirmClean: "Clean the litter box now? Make sure no cat is inside.",
    autoClean: "Automatic cleaning", todayTitle: "Today", noClean: "Pick the cleaning entity in the card editor.",
    l: {
      device_id: "Litter box", title: "Title", columns: "Cats per row", show_weight: "Show weight",
      show_visits: "Show visits today", show_last: "Show last visit", count: "Number of visits",
      show_duration: "Show duration", show_toggle: "Show hide/show button", days: "Days to show",
      period: "Period", chart_type: "Chart type", stat: "Value", clean_entity: "Cleaning entity (switch, button or script)",
      auto_clean_entity: "Automatic cleaning switch (optional)", confirm: "Ask before cleaning", show_today: "Show today's summary",
      hour: "Hour", day: "Day", week: "Week", month: "Month", line: "Line", bar: "Bars", mean: "Average", min: "Minimum", max: "Maximum",
    },
  },
  es: {
    cats: "Gatos", visits: "Últimas visitas", weight: "Peso", box: "Arenero", none: "Sin visitas todavía",
    time: "Hora", cat: "Gato", kg: "Peso", dur: "Duración",
    today: (n) => `${n} hoy`, last: "última", never: "sin visitas",
    unidentified: "Gato no identificado",
    partial: (c) => `Posible ${c} medio dentro, justo tras su visita`,
    noWeight: "Visita detectada sin peso",
    refill: "Probablemente relleno de arena o un gato medio dentro",
    notFound: "No se encontró ningún arenero de Litter Cat Identifier.",
    days: (d) => `${d} días`,
    hide: "Ocultar no identificadas", show: (n) => `Mostrar no identificadas (${n} ocultas)`,
    clean: "Limpiar ahora", cleaning: "Limpiando…", confirmClean: "¿Limpiar el arenero ahora? Comprueba que no hay ningún gato dentro.",
    autoClean: "Limpieza automática", todayTitle: "Hoy", noClean: "Elige la entidad de limpieza en el editor de la tarjeta.",
    l: {
      device_id: "Arenero", title: "Título", columns: "Gatos por fila", show_weight: "Mostrar peso",
      show_visits: "Mostrar visitas de hoy", show_last: "Mostrar última visita", count: "Número de visitas",
      show_duration: "Mostrar duración", show_toggle: "Mostrar botón ocultar/mostrar", days: "Días a mostrar",
      period: "Periodo", chart_type: "Tipo de gráfica", stat: "Valor", clean_entity: "Entidad de limpieza (interruptor, botón o script)",
      auto_clean_entity: "Interruptor de limpieza automática (opcional)", confirm: "Preguntar antes de limpiar", show_today: "Mostrar resumen de hoy",
      hour: "Hora", day: "Día", week: "Semana", month: "Mes", line: "Línea", bar: "Barras", mean: "Media", min: "Mínimo", max: "Máximo",
    },
  },
};

const t = (hass) => {
  const lang = (hass?.locale?.language || hass?.language || "en").split("-")[0];
  return I18N[lang] || I18N.en;
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const on = (v, dflt = true) => (v === undefined ? dflt : !!v);

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
    showSwitch: byKey("show_unidentified")[0],
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

const STYLE = `
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
  .lci-bar { display: flex; justify-content: flex-end; margin: -4px 0 6px; }
  .lci-toggle { display: inline-flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.85em;
                color: var(--secondary-text-color); background: none; border: 0; padding: 2px 4px; }
  .lci-toggle ha-icon { --mdc-icon-size: 18px; }
  .lci .q { cursor: help; color: var(--primary-color); font-weight: 600; margin-left: 4px; }
  .lci-actions { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .lci-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 12px; border: 0;
             cursor: pointer; font: inherit; font-weight: 500; color: var(--text-primary-color, #fff);
             background: var(--primary-color); }
  .lci-btn[disabled] { opacity: .6; cursor: default; }
  .lci-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; }
  .lci-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  .lci-chip { padding: 4px 10px; border-radius: 16px; background: var(--secondary-background-color); font-size: .9em; }
`;

class BaseCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._sig = null;
    if (this._hass) this.hass = this._hass;
  }
  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    const box = findBox(hass, this._config.device_id);
    const sig = this.signature(hass, box) + JSON.stringify(this._config);
    if (sig === this._sig) return;
    this._sig = sig;
    this.render(hass, box);
  }
  get hass() { return this._hass; }
  signature(hass, box) {
    if (!box) return "none";
    const ids = [box.lastVisit, box.unidentified, box.showSwitch, ...box.cats.flatMap((c) => [c.weight, c.visits, c.last])];
    return ids.map((id) => hass.states[id]?.last_updated).join("|") + (hass.locale?.language || "");
  }
  shell(title, body) {
    this.innerHTML = `<ha-card ${title ? `header="${esc(title)}"` : ""}><div class="lci">${body}</div></ha-card><style>${STYLE}</style>`;
  }
  getCardSize() { return 3; }
}

/* ---------- visual editor (ha-form) ---------- */
function makeEditor(schemaFn) {
  return class extends HTMLElement {
    setConfig(config) { this._config = { ...config }; this._render(); }
    set hass(hass) { this._hass = hass; this._render(); }
    _render() {
      if (!this._hass || !this._config) return;
      const T = t(this._hass);
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.computeLabel = (s) => T.l[s.name] || s.name;
        this._form.addEventListener("value-changed", (ev) => {
          const config = { ...ev.detail.value };
          for (const k of Object.keys(config)) if (config[k] === "" || config[k] === undefined) delete config[k];
          this._config = config;
          this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
        });
        this.appendChild(this._form);
      }
      this._form.hass = this._hass;
      this._form.schema = schemaFn(T);
      this._form.data = this._config;
    }
  };
}

const sel = (T, options) => ({ select: { mode: "dropdown", options: options.map((o) => ({ value: o, label: T.l[o] || o })) } });
const COMMON = () => [
  { name: "device_id", selector: { device: { integration: DOMAIN } } },
  { name: "title", selector: { text: {} } },
];

/* ---------- cats ---------- */
class CatsCard extends BaseCard {
  static getStubConfig() { return { columns: 2 }; }
  static getConfigElement() { return document.createElement("litter-cat-identifier-cats-editor"); }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.cats;
    if (!box) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const tiles = box.cats.map((cat) => {
      const w = hass.states[cat.weight];
      const pic = w?.attributes?.entity_picture;
      const kg = w && !isNaN(parseFloat(w.state)) ? `${parseFloat(w.state).toFixed(2)} kg` : "–";
      const visits = hass.states[cat.visits]?.state ?? "0";
      const last = hass.states[cat.last]?.state;
      const lastTxt = last && !["unknown", "unavailable"].includes(last) ? `${T.last} ${fmtTime(hass, last)}` : T.never;
      const sub = [on(c.show_visits) ? T.today(esc(visits)) : null, on(c.show_last) ? lastTxt : null].filter(Boolean).join(" · ");
      const avatar = pic
        ? `<img class="lci-avatar" src="${esc(pic)}" alt="">`
        : `<div class="lci-avatar"><ha-icon icon="mdi:cat"></ha-icon></div>`;
      return `<div class="lci-cat" data-entity="${esc(cat.weight)}">${avatar}
        <div style="min-width:0"><div class="lci-name">${esc(cat.name)}</div>
        ${on(c.show_weight) ? `<div class="lci-kg">${kg}</div>` : ""}${sub ? `<div class="lci-sub">${sub}</div>` : ""}</div></div>`;
    });
    this.shell(title, `<div class="lci-cats" style="--lci-cols:${Number(c.columns) || 2}">${tiles.join("")}</div>`);
    this.querySelectorAll(".lci-cat").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.entity)));
  }
  getCardSize() { return 2; }
  getGridOptions() { return { columns: 12, min_columns: 4 }; }
}
const CatsEditor = makeEditor(() => [
  ...COMMON(),
  { name: "columns", selector: { number: { min: 1, max: 4, mode: "box" } } },
  { type: "grid", name: "", schema: [
    { name: "show_weight", selector: { boolean: {} }, default: true },
    { name: "show_visits", selector: { boolean: {} }, default: true },
    { name: "show_last", selector: { boolean: {} }, default: true },
  ] },
]);

/* ---------- visits ---------- */
class VisitsCard extends BaseCard {
  static getStubConfig() { return { count: 8 }; }
  static getConfigElement() { return document.createElement("litter-cat-identifier-visits-editor"); }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.visits;
    if (!box || !box.lastVisit) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const all = hass.states[box.lastVisit]?.attributes?.history || [];
    const sw = box.showSwitch && hass.states[box.showSwitch];
    const hiding = sw?.state === "off";
    const history = hiding ? all.filter((v) => v.cat !== "unidentified") : all;
    const hiddenCount = all.filter((v) => v.cat === "unidentified").length;
    const bar = on(c.show_toggle) && sw && (hiddenCount || hiding)
      ? `<div class="lci-bar"><button class="lci-toggle"><ha-icon icon="${hiding ? "mdi:eye-outline" : "mdi:eye-off-outline"}"></ha-icon>${hiding ? T.show(hiddenCount) : T.hide}</button></div>`
      : "";
    const wire = () => this.querySelector(".lci-toggle")?.addEventListener("click", () =>
      hass.callService("switch", "toggle", { entity_id: box.showSwitch }));
    if (!history.length) { this.shell(title, `${bar}<div class="lci-empty">${T.none}</div>`); return wire(); }
    const showKg = on(c.show_weight), showDur = on(c.show_duration);
    const rows = history.slice(0, Number(c.count) || 8).map((v) => {
      let cat = esc(v.cat);
      if (v.cat === "unidentified") {
        const tip = v.reason === "partial_after_visit" ? T.partial(v.likely_cat || "?")
          : v.reason === "no_weight" ? T.noWeight : T.refill;
        cat = `${T.unidentified}<span class="q" title="${esc(tip)}">(?)</span>`;
      }
      const kg = typeof v.weight === "number" ? `${v.weight.toFixed(2)} kg` : "–";
      const dur = typeof v.duration === "number" ? `${Math.round(v.duration)} s` : "–";
      return `<tr><td>${fmtTime(hass, v.time, true)}</td><td>${cat}</td>${showKg ? `<td class="num">${kg}</td>` : ""}${showDur ? `<td class="num">${dur}</td>` : ""}</tr>`;
    });
    const head = `<tr><th>${T.time}</th><th>${T.cat}</th>${showKg ? `<th class="num">${T.kg}</th>` : ""}${showDur ? `<th class="num">${T.dur}</th>` : ""}</tr>`;
    this.shell(title, `${bar}<table>${head}${rows.join("")}</table>`);
    wire();
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
  getGridOptions() { return { columns: 12, min_columns: 6 }; }
}
const VisitsEditor = makeEditor(() => [
  ...COMMON(),
  { name: "count", selector: { number: { min: 1, max: 20, mode: "box" } } },
  { type: "grid", name: "", schema: [
    { name: "show_weight", selector: { boolean: {} }, default: true },
    { name: "show_duration", selector: { boolean: {} }, default: true },
    { name: "show_toggle", selector: { boolean: {} }, default: true },
  ] },
]);

/* ---------- weight ---------- */
class WeightCard extends BaseCard {
  static getStubConfig() { return { days: 7 }; }
  static getConfigElement() { return document.createElement("litter-cat-identifier-weight-editor"); }
  async render(hass, box) {
    const T = t(hass), c = this._config;
    const days = Number(c.days) || 7;
    const title = c.title ?? `${T.weight} (${T.days(days)})`;
    if (!box || !box.cats.length) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const cfg = {
      type: "statistics-graph",
      title,
      days_to_show: days,
      period: c.period || (days <= 14 ? "hour" : days <= 90 ? "day" : "week"),
      stat_types: [c.stat || "mean"],
      chart_type: c.chart_type || "line",
      entities: box.cats.map((cat) => ({ entity: cat.weight, name: cat.name })),
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
  get hass() { return this._hass; }
  getCardSize() { return 5; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }
}
const WeightEditor = makeEditor((T) => [
  ...COMMON(),
  { name: "days", selector: { number: { min: 1, max: 365, mode: "box" } } },
  { type: "grid", name: "", schema: [
    { name: "period", selector: sel(T, ["hour", "day", "week", "month"]) },
    { name: "chart_type", selector: sel(T, ["line", "bar"]) },
    { name: "stat", selector: sel(T, ["mean", "min", "max"]) },
  ] },
]);

/* ---------- litter box ---------- */
class BoxCard extends BaseCard {
  static getStubConfig() { return { confirm: true }; }
  static getConfigElement() { return document.createElement("litter-cat-identifier-box-editor"); }
  signature(hass, box) {
    const c = this._config || {};
    return super.signature(hass, box) + [c.clean_entity, c.auto_clean_entity].map((id) => id && hass.states[id]?.last_updated).join("|");
  }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.box;
    const clean = c.clean_entity && hass.states[c.clean_entity];
    const busy = clean && c.clean_entity.startsWith("switch.") && clean.state === "on";
    const actions = clean
      ? `<button class="lci-btn" ${busy ? "disabled" : ""}><ha-icon icon="mdi:broom"></ha-icon>${busy ? T.cleaning : T.clean}</button>`
      : `<div class="lci-empty">${T.noClean}</div>`;
    const auto = c.auto_clean_entity && hass.states[c.auto_clean_entity];
    const autoRow = auto
      ? `<div class="lci-row"><span>${T.autoClean}</span><ha-switch ${auto.state === "on" ? "checked" : ""}></ha-switch></div>`
      : "";
    let today = "";
    if (box && on(c.show_today)) {
      const chips = box.cats.map((cat) => `<span class="lci-chip">${esc(cat.name)} ${esc(hass.states[cat.visits]?.state ?? "0")}</span>`);
      if (box.unidentified) chips.push(`<span class="lci-chip">❔ ${esc(hass.states[box.unidentified]?.state ?? "0")}</span>`);
      today = `<div class="lci-sub" style="margin-top:12px">${T.todayTitle}</div><div class="lci-chips" style="margin-top:4px">${chips.join("")}</div>`;
    }
    this.shell(title, `<div class="lci-actions">${actions}</div>${autoRow}${today}`);
    this.querySelector(".lci-btn")?.addEventListener("click", () => {
      if (on(c.confirm) && !window.confirm(T.confirmClean)) return;
      const id = c.clean_entity, domain = id.split(".")[0];
      if (domain === "button") hass.callService("button", "press", { entity_id: id });
      else if (domain === "script") hass.callService("script", "turn_on", { entity_id: id });
      else hass.callService(domain, "turn_on", { entity_id: id });
    });
    this.querySelector("ha-switch")?.addEventListener("change", (ev) =>
      hass.callService("switch", ev.target.checked ? "turn_on" : "turn_off", { entity_id: c.auto_clean_entity }));
  }
  getCardSize() { return 2; }
  getGridOptions() { return { columns: 6, min_columns: 4 }; }
}
const BoxEditor = makeEditor(() => [
  ...COMMON(),
  { name: "clean_entity", selector: { entity: { domain: ["switch", "button", "script"] } } },
  { name: "auto_clean_entity", selector: { entity: { domain: "switch" } } },
  { type: "grid", name: "", schema: [
    { name: "confirm", selector: { boolean: {} }, default: true },
    { name: "show_today", selector: { boolean: {} }, default: true },
  ] },
]);

const define = (tag, cls) => { if (!customElements.get(tag)) customElements.define(tag, cls); };
define("litter-cat-identifier-cats", CatsCard);
define("litter-cat-identifier-cats-editor", CatsEditor);
define("litter-cat-identifier-visits", VisitsCard);
define("litter-cat-identifier-visits-editor", VisitsEditor);
define("litter-cat-identifier-weight", WeightCard);
define("litter-cat-identifier-weight-editor", WeightEditor);
define("litter-cat-identifier-box", BoxCard);
define("litter-cat-identifier-box-editor", BoxEditor);

window.customCards = window.customCards || [];
for (const [type, name, description] of [
  ["litter-cat-identifier-cats", "Litter Cat Identifier – Cats", "Photo, name, weight, visits today and last visit for each cat."],
  ["litter-cat-identifier-visits", "Litter Cat Identifier – Recent visits", "Latest litter box visits, with the likely reason for unidentified readings."],
  ["litter-cat-identifier-weight", "Litter Cat Identifier – Weight", "Weight history of each cat."],
  ["litter-cat-identifier-box", "Litter Cat Identifier – Litter box", "Clean now, automatic cleaning and today's visits."],
]) {
  if (!window.customCards.some((c) => c.type === type)) {
    window.customCards.push({ type, name, description, preview: true,
      documentationURL: "https://github.com/cruzpazv/litter-cat-identifier#dashboard-cards" });
  }
}
