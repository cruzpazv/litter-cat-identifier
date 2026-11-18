/*
 * Litter Cat Identifier – dashboard cards.
 * Served by the integration and loaded automatically; no HACS frontend install needed.
 *   custom:litter-cat-identifier-cat      one cat: photo, name, weight, visits today, last visit
 *   custom:litter-cat-identifier-cats     several cats together
 *   custom:litter-cat-identifier-visits   recent visits with reasons for unidentified readings
 *   custom:litter-cat-identifier-weight   weight history per cat (statistics graph)
 *   custom:litter-cat-identifier-visits-chart  visits per day, one bar per cat
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
    busy: "The litter box was moving the litter (cleaning, emptying or levelling)",
    stayed: "A cat stayed too long: the litter box levelled the litter and reset the weight",
    health: { frequent_visits: (v) => `${v} visits today, much more than usual`, long_visit: (v) => `${v} s visit, much longer than usual`,
      weight_loss: (v) => `Lost ${v} % of weight in 3 weeks` },
    notFound: "No Litter Cat Identifier litter box found.",
    days: (d) => `${d} days`,
    hide: "Hide unidentified", show: (n) => `Show unidentified (${n} hidden)`,
    clean: "Clean now", cleaning: "Cleaning…", confirmClean: "Clean the litter box now? Make sure no cat is inside.",
    autoClean: "Automatic cleaning", todayTitle: "Today", noClean: "Pick the cleaning entity in the card editor.",
    cancel: "Cancel", tapAgain: "Tap again to clean", visitsToday: (n) => (n === 1 ? "1 visit today" : `${n} visits today`),
    l: {
      device_id: "Litter box", title: "Title", columns: "Cats per row", show_weight: "Show weight",
      show_visits: "Show visits today", show_last: "Show last visit", count: "Visits shown",
      show_duration: "Show duration", show_toggle: "Show hide/show button", days: "Days to show",
      period: "Period", chart_type: "Chart type", stat: "Value", clean_entity: "Cleaning entity (switch, button or script)",
      auto_clean_entity: "Automatic cleaning switch (optional)", confirm: "Ask before cleaning", show_today: "Show today's summary",
      hour: "Hour", day: "Day", week: "Week", month: "Month", line: "Line", bar: "Bars", mean: "Average", min: "Minimum", max: "Maximum",
      show_title: "Show title", cat: "Cat", cats: "Cats to show (empty = all)", layout: "Layout", horizontal: "Horizontal", vertical: "Vertical",
      show_photo: "Show photo", avatar_size: "Photo size (px)", color: "Icon colour (when there's no photo)",
      show_health: "Show health alerts", show_unidentified: "Show unidentified visits", collapsible: "Collapsible list", expanded_count: "Visits when expanded",
    },
    pickCat: "Pick a cat in the card editor.",
    more: "Show more", less: "Show less", all: (n) => (n ? `Whole history (${n})` : "Whole history"),
    visitsChart: "Visits per day", loading: "Loading…", lastDays: (n) => `Last ${n} days (tap a day for details)`, perDay: (v) => `${v}/day`,
  },
  es: {
    cats: "Gatos", visits: "Últimas visitas", weight: "Peso", box: "Arenero", none: "Sin visitas todavía",
    time: "Hora", cat: "Gato", kg: "Peso", dur: "Duración",
    today: (n) => `${n} hoy`, last: "última", never: "sin visitas",
    unidentified: "Gato no identificado",
    partial: (c) => `Posible ${c} medio dentro, justo tras su visita`,
    noWeight: "Visita detectada sin peso",
    refill: "Probablemente relleno de arena o un gato medio dentro",
    busy: "El arenero estaba moviendo la arena (limpiando, vaciando o nivelando)",
    stayed: "Un gato estuvo demasiado tiempo: el arenero niveló la arena y reinició el peso",
    health: { frequent_visits: (v) => `${v} visitas hoy, muchas más de lo habitual`, long_visit: (v) => `Visita de ${v} s, mucho más larga de lo habitual`,
      weight_loss: (v) => `Ha perdido un ${v} % de peso en 3 semanas` },
    notFound: "No se encontró ningún arenero de Litter Cat Identifier.",
    days: (d) => `${d} días`,
    hide: "Ocultar no identificadas", show: (n) => `Mostrar no identificadas (${n} ocultas)`,
    clean: "Limpiar ahora", cleaning: "Limpiando…", confirmClean: "¿Limpiar el arenero ahora? Comprueba que no hay ningún gato dentro.",
    autoClean: "Limpieza automática", todayTitle: "Hoy", noClean: "Elige la entidad de limpieza en el editor de la tarjeta.",
    cancel: "Cancelar", tapAgain: "Pulsa otra vez para limpiar", visitsToday: (n) => (n === 1 ? "1 visita hoy" : `${n} visitas hoy`),
    l: {
      device_id: "Arenero", title: "Título", columns: "Gatos por fila", show_weight: "Mostrar peso",
      show_visits: "Mostrar visitas de hoy", show_last: "Mostrar última visita", count: "Visitas visibles",
      show_duration: "Mostrar duración", show_toggle: "Mostrar botón ocultar/mostrar", days: "Días a mostrar",
      period: "Periodo", chart_type: "Tipo de gráfica", stat: "Valor", clean_entity: "Entidad de limpieza (interruptor, botón o script)",
      auto_clean_entity: "Interruptor de limpieza automática (opcional)", confirm: "Preguntar antes de limpiar", show_today: "Mostrar resumen de hoy",
      hour: "Hora", day: "Día", week: "Semana", month: "Mes", line: "Línea", bar: "Barras", mean: "Media", min: "Mínimo", max: "Máximo",
      show_title: "Mostrar título", cat: "Gato", cats: "Gatos a mostrar (vacío = todos)", layout: "Disposición", horizontal: "Horizontal", vertical: "Vertical",
      show_photo: "Mostrar foto", avatar_size: "Tamaño de la foto (px)", color: "Color del icono (si no hay foto)",
      show_health: "Mostrar avisos de salud", show_unidentified: "Mostrar visitas no identificadas", collapsible: "Lista desplegable", expanded_count: "Visitas al desplegar",
    },
    pickCat: "Elige un gato en el editor de la tarjeta.",
    more: "Ver más", less: "Ver menos", all: (n) => (n ? `Todo el historial (${n})` : "Todo el historial"),
    visitsChart: "Visitas por día", loading: "Cargando…", lastDays: (n) => `Últimos ${n} días (toca un día para ver el detalle)`, perDay: (v) => `${v}/día`,
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
  for (const [key, field] of [["cat_weight", "weight"], ["cat_visits_today", "visits"], ["cat_last_visit", "last"], ["cat_health", "health"]]) {
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
  .lci-cat.vertical { flex-direction: column; text-align: center; }
  .lci-cat.vertical > div { width: 100%; }
  .lci-single .lci-cat { background: none; padding: 0; }
  .lci-avatar { width: var(--lci-avatar, 52px); height: var(--lci-avatar, 52px); border-radius: 50%; flex: none; object-fit: cover;
                display: flex; align-items: center; justify-content: center;
                background: var(--primary-background-color); color: var(--lci-color, var(--primary-color)); }
  .lci-avatar ha-icon { --mdc-icon-size: calc(var(--lci-avatar, 52px) * 0.55); }
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
  .lci-health { display: flex; align-items: center; gap: 4px; margin-top: 4px; color: var(--error-color, #db4437); font-size: .85em; }
  .lci-health ha-icon { --mdc-icon-size: 16px; flex: none; }
  .lcb-head, .lcb-mini { display: flex; align-items: center; gap: 12px; }
  .lcb-head { margin-bottom: 14px; }
  .lcb-titles { flex: 1; min-width: 0; }
  .lcb-badge { width: 44px; height: 44px; border-radius: 50%; flex: none; display: grid; place-items: center;
               background: color-mix(in srgb, var(--primary-color) 14%, transparent); color: var(--primary-color); }
  .lcb-badge.busy ha-icon { animation: lcb-spin 2.4s linear infinite; }
  @keyframes lcb-spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) { .lcb-badge.busy ha-icon { animation: none; } }
  .lcb-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 18px; border-radius: 14px; border: 0;
             cursor: pointer; font: inherit; font-weight: 500; color: var(--text-primary-color, #fff); background: var(--primary-color); }
  .lcb-btn.wide { width: 100%; font-size: 1.05em; }
  .lcb-btn[disabled] { opacity: .6; cursor: default; }
  .lcb-ask { display: flex; flex-direction: column; gap: 10px; padding: 12px; border-radius: 14px; background: var(--secondary-background-color); }
  .lcb-ask-b { display: flex; justify-content: flex-end; gap: 8px; align-items: center; }
  .lcb-link { border: 0; background: none; font: inherit; color: var(--primary-color); cursor: pointer; padding: 8px 12px; }
  .lcb-row { display: flex; align-items: center; gap: 12px; width: 100%; margin-top: 12px; padding: 10px 12px; border: 0; border-radius: 14px;
             background: var(--secondary-background-color); font: inherit; color: var(--primary-text-color); cursor: pointer; text-align: left; }
  .lcb-row > span:first-of-type { flex: 1; }
  .lcb-row ha-icon { color: var(--state-icon-color, var(--secondary-text-color)); }
  .lcb-sw { width: 40px; height: 24px; border-radius: 12px; background: var(--divider-color); position: relative; flex: none; transition: background .2s; }
  .lcb-sw span { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,.3); transition: transform .2s; }
  .lcb-sw.on { background: var(--primary-color); } .lcb-sw.on span { transform: translateX(16px); }
  .lcb-label { margin-top: 14px; }
  .lcb-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .lcb-chip { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px 3px 3px; border-radius: 16px; background: var(--secondary-background-color); font-size: .9em; }
  .lcb-chip img, .lcb-chip ha-icon { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; --mdc-icon-size: 16px;
                                     display: grid; place-items: center; background: var(--card-background-color); color: var(--primary-color); }
  .lcb-chip b { font-weight: 600; }
  .lcb-round { width: 44px; height: 44px; border-radius: 50%; border: 0; flex: none; cursor: pointer; display: grid; place-items: center;
               background: color-mix(in srgb, var(--primary-color) 14%, transparent); color: var(--primary-color); }
  .lcb-round.armed { background: var(--error-color, #db4437); color: #fff; }
  .lcb-round[disabled] { opacity: .5; cursor: default; }
  .lci-foot { display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
  .lci-scroll { max-height: 420px; overflow-y: auto; }
  .lci-chart-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
  .lci-rng { font: inherit; font-size: .85em; border: 0; cursor: pointer; padding: 3px 10px; border-radius: 14px; margin-left: 4px;
             background: var(--secondary-background-color); color: var(--primary-text-color); }
  .lci-rng.sel { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .lci-chart { width: 100%; height: auto; display: block; overflow: visible; }
  .lci-chart text { fill: var(--secondary-text-color); font-size: 10px; text-anchor: middle; }
  .lci-chart text.max { text-anchor: start; } .lci-chart text.x.today { fill: var(--primary-text-color); font-weight: 600; }
  .lci-chart text.v { font-size: 9px; fill: var(--primary-text-color); }
  .lci-chart .axis { stroke: var(--divider-color); }
  .lci-chart .hit { fill: transparent; cursor: pointer; } .lci-chart .hit.picked { fill: var(--secondary-background-color); }
  .lci-legend { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .lci-leg { display: inline-flex; align-items: center; gap: 6px; font: inherit; font-size: .9em; cursor: pointer; border: 0;
             padding: 4px 10px; border-radius: 16px; background: var(--secondary-background-color); color: var(--primary-text-color); }
  .lci-leg.off { opacity: .45; } .lci-leg .dot { width: 10px; height: 10px; border-radius: 50%; }
  .lci-leg .tot { color: var(--secondary-text-color); font-size: .9em; }
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
    const ids = [box.lastVisit, box.unidentified, box.showSwitch, ...box.cats.flatMap((c) => [c.weight, c.visits, c.last, c.health])];
    return ids.map((id) => hass.states[id]?.last_updated).join("|") + (hass.locale?.language || "");
  }
  shell(title, body) {
    if (this._config && this._config.show_title === false) title = "";
    this.innerHTML = `<ha-card ${title ? `header="${esc(title)}"` : ""}><div class="lci">${body}</div></ha-card><style>${STYLE}</style>`;
  }
  getCardSize() { return 3; }
}

/* ---------- visual editor (ha-form) ---------- */
// ha-form is lazy-loaded by the frontend; make sure it exists before an editor opens.
async function loadHaForm() {
  if (customElements.get("ha-form")) return;
  try {
    const helpers = await window.loadCardHelpers();
    const card = await helpers.createCardElement({ type: "entities", entities: [] });
    await card?.constructor?.getConfigElement?.();
  } catch (e) { /* the editor still opens; HA falls back to YAML if needed */ }
  if (!customElements.get("ha-form")) {
    await Promise.race([customElements.whenDefined("ha-form"), new Promise((r) => setTimeout(r, 3000))]);
  }
}

/** `default` values declared in an ha-form schema (grids included). */
function schemaDefaults(schema, out = {}) {
  for (const s of schema) {
    if (s.schema) schemaDefaults(s.schema, out);
    else if (s.default !== undefined) out[s.name] = s.default;
  }
  return out;
}

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
          for (const k of Object.keys(config)) {
            // Drop empty values and values equal to the default, so the YAML stays minimal.
            if (config[k] === "" || config[k] === undefined || this._defaults[k] === config[k]) delete config[k];
          }
          this._config = config;
          this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
        });
        this.appendChild(this._form);
      }
      const schema = schemaFn(T, this._hass, this._config);
      this._defaults = schemaDefaults(schema);
      this._form.hass = this._hass;
      this._form.schema = schema;
      // ha-form does not apply `default` itself: without this a toggle that defaults to on (e.g. Show title)
      // is drawn off, and the first tap seems to do nothing.
      this._form.data = { ...this._defaults, ...this._config };
    }
  };
}

const sel = (T, options) => ({ select: { mode: "dropdown", options: options.map((o) => ({ value: o, label: T.l[o] || o })) } });
const COMMON = () => [
  { name: "device_id", selector: { device: { integration: DOMAIN } } },
  { type: "grid", name: "", schema: [
    { name: "title", selector: { text: {} } },
    { name: "show_title", selector: { boolean: {} }, default: true },
  ] },
];
const catNames = (hass, config) => (findBox(hass, config?.device_id)?.cats || []).map((c) => c.name);
const avatarSchema = (T) => [{ type: "grid", name: "", schema: [
  { name: "layout", selector: sel(T, ["horizontal", "vertical"]) },
  { name: "avatar_size", selector: { number: { min: 24, max: 200, step: 4, mode: "box", unit_of_measurement: "px" } } },
] }];
const showSchema = () => [{ type: "grid", name: "", schema: [
  { name: "show_photo", selector: { boolean: {} }, default: true },
  { name: "show_weight", selector: { boolean: {} }, default: true },
  { name: "show_visits", selector: { boolean: {} }, default: true },
  { name: "show_last", selector: { boolean: {} }, default: true },
  { name: "show_health", selector: { boolean: {} }, default: true },
] }];

/** One cat tile, shared by the Cats and Cat cards. */
function catTile(hass, T, c, cat) {
  const w = hass.states[cat.weight];
  const pic = on(c.show_photo) && w?.attributes?.entity_picture;
  const kg = w && !isNaN(parseFloat(w.state)) ? `${parseFloat(w.state).toFixed(2)} kg` : "–";
  const visits = hass.states[cat.visits]?.state ?? "0";
  const last = hass.states[cat.last]?.state;
  const lastTxt = last && !["unknown", "unavailable"].includes(last) ? `${T.last} ${fmtTime(hass, last)}` : T.never;
  const sub = [on(c.show_visits) ? T.today(esc(visits)) : null, on(c.show_last) ? lastTxt : null].filter(Boolean).join(" · ");
  const hs = cat.health && hass.states[cat.health];
  const alerts = hs?.state === "on" && on(c.show_health)
    ? (hs.attributes.reasons || []).map((r) => T.health[r] ? T.health[r](hs.attributes[r]) : r) : [];
  const avatar = pic
    ? `<img class="lci-avatar" src="${esc(pic)}" alt="">`
    : `<div class="lci-avatar"><ha-icon icon="mdi:cat"></ha-icon></div>`;
  const color = c.color || w?.attributes?.color;  // card option first, then the cat's colour
  const style = [c.avatar_size ? `--lci-avatar:${Number(c.avatar_size)}px` : "", color ? `--lci-color:${esc(color)}` : ""].join(";");
  return `<div class="lci-cat ${c.layout === "vertical" ? "vertical" : ""}" style="${style}" data-entity="${esc(cat.weight)}">${avatar}
    <div style="min-width:0"><div class="lci-name">${esc(cat.name)}</div>
    ${on(c.show_weight) ? `<div class="lci-kg">${kg}</div>` : ""}${sub ? `<div class="lci-sub">${sub}</div>` : ""}
    ${alerts.map((a) => `<div class="lci-health"><ha-icon icon="mdi:heart-pulse"></ha-icon>${esc(a)}</div>`).join("")}</div></div>`;
}

/* ---------- cats ---------- */
class CatsCard extends BaseCard {
  static getStubConfig() { return { columns: 2 }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-cats-editor"); }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.cats;
    if (!box) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const wanted = Array.isArray(c.cats) && c.cats.length ? c.cats : null;
    const tiles = box.cats.filter((cat) => !wanted || wanted.includes(cat.name)).map((cat) => catTile(hass, T, c, cat));
    this.shell(title, `<div class="lci-cats" style="--lci-cols:${Number(c.columns) || 2}">${tiles.join("")}</div>`);
    this.querySelectorAll(".lci-cat").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.entity)));
  }
  getCardSize() { return 2; }
  getGridOptions() { return { columns: 12, min_columns: 4 }; }
}
const CatsEditor = makeEditor((T, hass, config) => [
  ...COMMON(),
  { name: "cats", selector: { select: { multiple: true, mode: "list", options: catNames(hass, config) } } },
  { name: "columns", selector: { number: { min: 1, max: 6, mode: "box" } } },
  ...avatarSchema(T),
  ...showSchema(),
]);

/* ---------- single cat ---------- */
class CatCard extends BaseCard {
  static getStubConfig(hass) {
    const first = hass && findBox(hass)?.cats[0];
    return { cat: first?.name || "", show_title: false };
  }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-cat-editor"); }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? c.cat ?? "";
    if (!box) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const cat = box.cats.find((x) => x.name === c.cat);
    if (!cat) return this.shell(title, `<div class="lci-empty">${T.pickCat}</div>`);
    this.shell(title, `<div class="lci-single">${catTile(hass, T, c, cat)}</div>`);
    this.querySelector(".lci-cat")?.addEventListener("click", () => moreInfo(this, cat.weight));
  }
  getCardSize() { return 2; }
  getGridOptions() { return { columns: 6, min_columns: 3 }; }
}
const CatEditor = makeEditor((T, hass, config) => [
  { name: "cat", required: true, selector: { select: { mode: "dropdown", options: catNames(hass, config) } } },
  ...COMMON(),
  ...avatarSchema(T),
  { name: "color", selector: { text: {} } },
  ...showSchema(),
]);

/* ---------- visits ---------- */
class VisitsCard extends BaseCard {
  static getStubConfig() { return { count: 8 }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-visits-editor"); }

  /** How many visits the current view wants (Infinity = whole history). */
  _wanted() {
    const c = this._config, count = Number(c.count) || 8;
    if (!on(c.collapsible, false)) return count;
    if (this._mode === "all") return Infinity;
    if (this._mode === "expanded") return Math.max(count, Number(c.expanded_count) || 20);
    return count;
  }

  signature(hass, box) {
    return `${super.signature(hass, box)}|${this._mode}|${this._fullVersion || 0}`;
  }

  /** The sensor only carries the latest 20 visits: fetch more from the integration when asked for. */
  async _fetch(hass, box, limit, key) {
    this._fullKey = key;
    try {
      const res = await hass.callWS({ type: `${DOMAIN}/history`, device_id: box.device, limit: limit === Infinity ? 0 : limit });
      if (this._fullKey !== key) return;
      this._full = res.history;
      this._total = res.total;
    } catch (e) {
      this._full = null;
    }
    this._fullVersion = (this._fullVersion || 0) + 1;
    this._sig = null;
    if (this._hass) this.hass = this._hass;
  }

  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.visits;
    if (!box || !box.lastVisit) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    const latest = hass.states[box.lastVisit]?.attributes?.history || [];
    const wanted = this._wanted();
    let all = latest, loading = false;
    if (wanted > latest.length && latest.length >= 20 && hass.callWS) {
      // a new visit or a different view invalidates what was fetched
      const key = `${hass.states[box.lastVisit]?.last_updated}|${wanted}`;
      if (this._fullKey === key && this._full) all = this._full;
      else { loading = true; if (this._fullKey !== key) this._fetch(hass, box, wanted, key); }
    }
    const sw = box.showSwitch && hass.states[box.showSwitch];
    const hiding = sw?.state === "off";
    const history = hiding ? all.filter((v) => v.cat !== "unidentified") : all;
    const hiddenCount = all.filter((v) => v.cat === "unidentified").length;
    const bar = on(c.show_toggle) && sw && (hiddenCount || hiding)
      ? `<div class="lci-bar"><button class="lci-toggle lci-hide"><ha-icon icon="${hiding ? "mdi:eye-outline" : "mdi:eye-off-outline"}"></ha-icon>${hiding ? T.show(hiddenCount) : T.hide}</button></div>`
      : "";
    const wire = () => this.querySelector(".lci-hide")?.addEventListener("click", () =>
      hass.callService("switch", "toggle", { entity_id: box.showSwitch }));
    if (!history.length) { this.shell(title, `${bar}<div class="lci-empty">${T.none}</div>`); return wire(); }
    const showKg = on(c.show_weight), showDur = on(c.show_duration);
    const shown = history.slice(0, wanted);
    const rows = shown.map((v) => {
      let cat = esc(v.cat);
      if (v.cat === "unidentified") {
        const tip = v.reason === "partial_after_visit" ? T.partial(v.likely_cat || "?")
          : v.reason === "no_weight" ? T.noWeight : v.reason === "device_busy" ? T.busy
          : v.reason === "stayed_too_long" ? T.stayed : T.refill;
        cat = `${T.unidentified}<span class="q" title="${esc(tip)}">(?)</span>`;
      }
      const kg = typeof v.weight === "number" ? `${v.weight.toFixed(2)} kg` : "–";
      const dur = typeof v.duration === "number" ? `${Math.round(v.duration)} s` : "–";
      return `<tr><td>${fmtTime(hass, v.time, true)}</td><td>${cat}</td>${showKg ? `<td class="num">${kg}</td>` : ""}${showDur ? `<td class="num">${dur}</td>` : ""}</tr>`;
    });
    const head = `<tr><th>${T.time}</th><th>${T.cat}</th>${showKg ? `<th class="num">${T.kg}</th>` : ""}${showDur ? `<th class="num">${T.dur}</th>` : ""}</tr>`;

    // collapsible footer: show more / whole history / show less
    let foot = "";
    if (on(c.collapsible, false)) {
      const count = Number(c.count) || 8, expanded = Math.max(count, Number(c.expanded_count) || 20);
      const mode = this._mode || "collapsed";
      const btn = (m, icon, label) => `<button class="lci-toggle lci-more" data-mode="${m}"><ha-icon icon="${icon}"></ha-icon>${esc(label)}</button>`;
      const btns = [];
      if (mode === "collapsed" && expanded > count && (history.length > count || latest.length >= 20)) btns.push(btn("expanded", "mdi:chevron-down", T.more));
      if (mode !== "all" && (history.length > shown.length || latest.length >= 20)) btns.push(btn("all", "mdi:history", T.all(mode === "all" ? null : this._total)));
      if (mode !== "collapsed") btns.push(btn("collapsed", "mdi:chevron-up", T.less));
      if (loading) btns.unshift(`<span class="lci-sub">${T.loading}</span>`);
      foot = btns.length ? `<div class="lci-foot">${btns.join("")}</div>` : "";
    }
    const scroll = shown.length > 20 ? " lci-scroll" : "";
    this.shell(title, `${bar}<div class="lci-table${scroll}"><table>${head}${rows.join("")}</table></div>${foot}`);
    wire();
    this.querySelectorAll(".lci-more").forEach((el) => el.addEventListener("click", () => {
      this._mode = el.dataset.mode;
      this._sig = null;
      this.hass = this._hass;
    }));
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
  { type: "grid", name: "", schema: [
    { name: "count", selector: { number: { min: 1, max: 50, mode: "box" } } },
    { name: "collapsible", selector: { boolean: {} }, default: false },
  ] },
  { name: "expanded_count", selector: { number: { min: 5, max: 500, mode: "box" } } },
  { type: "grid", name: "", schema: [
    { name: "show_weight", selector: { boolean: {} }, default: true },
    { name: "show_duration", selector: { boolean: {} }, default: true },
    { name: "show_toggle", selector: { boolean: {} }, default: true },
  ] },
]);

/* ---------- weight ---------- */
class WeightCard extends BaseCard {
  static getStubConfig() { return { days: 7 }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-weight-editor"); }
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
    if (c.grid_options) cfg.grid_options = c.grid_options;
    const key = JSON.stringify(cfg);
    if (this._graphKey !== key) {
      this._graphKey = key;
      const helpers = await window.loadCardHelpers();
      this._graph = helpers.createCardElement(cfg);
      this._graph.style.height = "100%";
      if (this._layout) this._graph.layout = this._layout;
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
  // sections dashboards set layout="grid" and size the card; pass that on so the chart fills it
  set layout(v) { this._layout = v; if (this._graph) this._graph.layout = v; }
  get layout() { return this._layout; }
  connectedCallback() { this.style.display = "block"; this.style.height = "100%"; }
  getCardSize() { return 5; }
  getGridOptions() { return { columns: 12, min_columns: 4, rows: 5, min_rows: 3 }; }
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

/* ---------- visits per day, one bar per cat ---------- */
const PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1", "#edc948", "#76b7b2", "#ff9da7"];
const GREY = "#9e9e9e";
const dayStart = (offset) => { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + offset); return d; };

class VisitsChartCard extends BaseCard {
  static getStubConfig() { return { days: 7 }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-visits-chart-editor"); }

  _range() { return this._days || Number(this._config.days) || 7; }

  signature(hass, box) {
    const days = this._range();
    if (box && hass.callWS && (!this._fetchedAt || Date.now() - this._fetchedAt > 300000 || this._fetchedDays !== days)) {
      this._fetch(hass, box, days);
    }
    return `${super.signature(hass, box)}|${this._version || 0}|${days}|${this._picked}|${[...(this._hidden || [])].join(",")}`;
  }

  _ids(box) {
    const ids = box.cats.map((c) => c.visits).filter(Boolean);
    if (on(this._config.show_unidentified) && box.unidentified) ids.push(box.unidentified);
    return ids;
  }

  async _fetch(hass, box, days) {
    this._fetchedAt = Date.now();
    this._fetchedDays = days;
    try {
      this._stats = await hass.callWS({
        type: "recorder/statistics_during_period", start_time: dayStart(-(days - 1)).toISOString(),
        statistic_ids: this._ids(box), period: "day", types: ["change"],
      });
    } catch (e) { this._stats = {}; }
    this._version = (this._version || 0) + 1;
    this._sig = null;
    if (this._hass) this.hass = this._hass;
  }

  /** [{name, color, id, values[days]}]: statistics per day, today's live value from the sensor. */
  _series(hass, box, days) {
    const T = t(hass), colors = this._config.colors || {};
    const list = box.cats.map((c, i) => ({ name: c.name, id: c.visits, color: colors[c.name] || hass.states[c.weight]?.attributes?.color || PALETTE[i % PALETTE.length] }));
    if (on(this._config.show_unidentified) && box.unidentified) list.push({ name: T.unidentified, id: box.unidentified, color: GREY, unknown: true });
    const keys = Array.from({ length: days }, (_, i) => dayStart(i - (days - 1)).toDateString());
    for (const s of list) {
      const byDay = {};
      for (const row of (this._stats || {})[s.id] || []) {
        const d = new Date(typeof row.start === "number" ? row.start : Date.parse(row.start));
        byDay[d.toDateString()] = row.change || 0;
      }
      s.values = keys.map((k) => byDay[k] || 0);
      const live = parseFloat(hass.states[s.id]?.state);
      if (!isNaN(live)) s.values[days - 1] = live;
    }
    return list;
  }

  _chart(hass, series, days) {
    const W = 320, H = 140, top = 14;
    const shown = series.filter((s) => !(this._hidden || new Set()).has(s.name));
    const max = Math.max(1, ...shown.flatMap((s) => s.values));
    const slot = W / days, group = slot * 0.82, bw = shown.length ? group / shown.length : 0;
    const lang = hass.locale?.language || hass.language;
    let bars = "", labels = "", hits = "";
    for (let i = 0; i < days; i++) {
      const x0 = slot * i + (slot - group) / 2;
      shown.forEach((s, j) => {
        const v = s.values[i], h = (v / max) * (H - top);
        if (v > 0) {
          bars += `<rect x="${(x0 + j * bw + 0.5).toFixed(2)}" y="${(H - h).toFixed(2)}" width="${Math.max(1, bw - 1).toFixed(2)}" height="${h.toFixed(2)}" rx="${Math.min(3, bw / 3).toFixed(2)}" fill="${esc(s.color)}"/>`;
          if (days <= 7 && bw >= 9) bars += `<text class="v" x="${(x0 + j * bw + bw / 2).toFixed(2)}" y="${(H - h - 3).toFixed(2)}">${v}</text>`;
        }
      });
      const d = dayStart(i - (days - 1));
      if (days <= 7 || i % 5 === (days - 1) % 5) {
        const label = days <= 7 ? d.toLocaleDateString(lang, { weekday: "short" }) : d.getDate();
        labels += `<text class="x ${i === days - 1 ? "today" : ""}" x="${(slot * i + slot / 2).toFixed(2)}" y="${H + 14}">${esc(label)}</text>`;
      }
      hits += `<rect class="hit ${this._picked === i ? "picked" : ""}" data-day="${i}" x="${(slot * i).toFixed(2)}" y="0" width="${slot.toFixed(2)}" height="${H}"/>`;
    }
    return `<svg class="lci-chart" viewBox="0 0 ${W} ${H + 20}" role="img">
      <line class="axis" x1="0" x2="${W}" y1="${H + 0.5}" y2="${H + 0.5}"/>
      <text class="max" x="0" y="9">${max}</text>${hits}${bars}${labels}</svg>`;
  }

  render(hass, box) {
    const T = t(hass), c = this._config, days = this._range();
    const title = c.title ?? T.visitsChart;
    if (!box || !box.cats.length) return this.shell(title, `<div class="lci-empty">${T.notFound}</div>`);
    if (!this._stats) return this.shell(title, `<div class="lci-empty">${T.loading}</div>`);
    const series = this._series(hass, box, days);
    const hidden = this._hidden || new Set();
    const lang = hass.locale?.language || hass.language;
    let summary;
    if (this._picked !== undefined && this._picked !== null) {
      const d = dayStart(this._picked - (days - 1)).toLocaleDateString(lang, { weekday: "long", day: "numeric", month: "short" });
      summary = `${d}: ${series.filter((s) => !hidden.has(s.name)).map((s) => `${s.name} ${s.values[this._picked]}`).join(" · ")}`;
    } else {
      summary = T.lastDays(days);
    }
    const legend = series.map((s) => {
      const total = s.values.reduce((a, b) => a + b, 0);
      return `<button class="lci-leg ${hidden.has(s.name) ? "off" : ""}" data-name="${esc(s.name)}" aria-pressed="${!hidden.has(s.name)}">
        <span class="dot" style="background:${esc(s.color)}"></span>${esc(s.name)}
        <span class="tot">${total} · ${T.perDay(Number((total / days).toFixed(1)).toLocaleString(lang))}</span></button>`;
    }).join("");
    const range = [7, 30].map((d) => `<button class="lci-rng ${d === days ? "sel" : ""}" data-days="${d}">${T.days(d)}</button>`).join("");
    this.shell(title, `<div class="lci-chart-head"><span class="lci-sub">${esc(summary)}</span><span>${range}</span></div>
      ${this._chart(hass, series, days)}<div class="lci-legend">${legend}</div>`);
    const rerender = () => { this._sig = null; this.hass = this._hass; };
    this.querySelectorAll(".hit").forEach((el) => el.addEventListener("click", () => {
      const i = Number(el.dataset.day);
      this._picked = this._picked === i ? null : i;
      rerender();
    }));
    this.querySelectorAll(".lci-leg").forEach((el) => el.addEventListener("click", () => {
      const set = new Set(this._hidden || []);
      set.has(el.dataset.name) ? set.delete(el.dataset.name) : set.add(el.dataset.name);
      this._hidden = set;
      rerender();
    }));
    this.querySelectorAll(".lci-rng").forEach((el) => el.addEventListener("click", () => {
      this._days = Number(el.dataset.days);
      this._picked = null;
      rerender();
    }));
  }
  getCardSize() { return 4; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }
}
const VisitsChartEditor = makeEditor((T) => [
  ...COMMON(),
  { name: "days", selector: { select: { mode: "dropdown", options: [7, 14, 30].map((d) => ({ value: d, label: T.days(d) })) } } },
  { name: "show_unidentified", selector: { boolean: {} }, default: true },
]);

/* ---------- litter box ---------- */
/** Run the cleaning entity (switch, button or script). */
const runClean = (hass, id) => {
  const domain = id.split(".")[0];
  if (domain === "button") hass.callService("button", "press", { entity_id: id });
  else if (domain === "script") hass.callService("script", "turn_on", { entity_id: id });
  else hass.callService(domain, "turn_on", { entity_id: id });
};
const isCleaning = (hass, id) => id && id.startsWith("switch.") && hass.states[id]?.state === "on";

class BoxCard extends BaseCard {
  static getStubConfig() { return { confirm: true }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-box-editor"); }
  signature(hass, box) {
    const c = this._config || {};
    return `${super.signature(hass, box)}${[c.clean_entity, c.auto_clean_entity].map((id) => id && hass.states[id]?.last_updated).join("|")}|${this._asking}`;
  }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const title = c.title ?? T.box;
    const clean = c.clean_entity && hass.states[c.clean_entity];
    const busy = isCleaning(hass, c.clean_entity);
    const total = box ? box.cats.reduce((n, cat) => n + (parseInt(hass.states[cat.visits]?.state) || 0), 0)
      + (parseInt(hass.states[box.unidentified]?.state) || 0) : 0;
    const auto = c.auto_clean_entity && hass.states[c.auto_clean_entity];
    const autoOn = auto?.state === "on";
    const head = `<div class="lcb-head"><span class="lcb-badge ${busy ? "busy" : ""}"><ha-icon icon="${busy ? "mdi:rotate-3d-variant" : "mdi:cat"}"></ha-icon></span>
      <div class="lcb-titles"><div class="lci-name">${esc(c.show_title === false ? "" : title) || esc(T.box)}</div>
      <div class="lci-sub">${busy ? T.cleaning : T.visitsToday(total)}</div></div></div>`;
    const action = clean
      ? (this._asking
        ? `<div class="lcb-ask"><span>${esc(T.confirmClean)}</span><div class="lcb-ask-b"><button class="lcb-link" data-a="no">${T.cancel}</button>
            <button class="lcb-btn" data-a="yes"><ha-icon icon="mdi:broom"></ha-icon>${T.clean}</button></div></div>`
        : `<button class="lcb-btn wide" data-a="clean" ${busy ? "disabled" : ""}><ha-icon icon="mdi:broom"></ha-icon>${busy ? T.cleaning : T.clean}</button>`)
      : `<div class="lci-empty">${T.noClean}</div>`;
    const autoRow = auto ? `<button class="lcb-row" data-a="auto" role="switch" aria-checked="${autoOn}">
        <ha-icon icon="mdi:robot-vacuum"></ha-icon><span>${T.autoClean}</span><span class="lcb-sw ${autoOn ? "on" : ""}"><span></span></span></button>` : "";
    let today = "";
    if (box && on(c.show_today)) {
      const chips = box.cats.map((cat) => {
        const pic = hass.states[cat.weight]?.attributes?.entity_picture;
        const color = hass.states[cat.weight]?.attributes?.color;
        return `<span class="lcb-chip">${pic ? `<img src="${esc(pic)}" alt="">` : `<ha-icon icon="mdi:cat" ${color ? `style="color:${esc(color)}"` : ""}></ha-icon>`}${esc(cat.name)}<b>${esc(hass.states[cat.visits]?.state ?? "0")}</b></span>`;
      });
      if (box.unidentified && parseInt(hass.states[box.unidentified]?.state)) chips.push(`<span class="lcb-chip"><ha-icon icon="mdi:help-circle-outline"></ha-icon>${T.unidentified}<b>${esc(hass.states[box.unidentified].state)}</b></span>`);
      today = `<div class="lci-sub lcb-label">${T.todayTitle}</div><div class="lcb-chips">${chips.join("")}</div>`;
    }
    this.shell("", `${head}${action}${autoRow}${today}`);
    this.querySelectorAll("[data-a]").forEach((el) => el.addEventListener("click", () => {
      const a = el.dataset.a;
      if (a === "clean") { if (on(c.confirm)) { this._asking = true; this._sig = null; this.hass = this._hass; } else runClean(hass, c.clean_entity); }
      else if (a === "yes") { this._asking = false; runClean(hass, c.clean_entity); this._sig = null; this.hass = this._hass; }
      else if (a === "no") { this._asking = false; this._sig = null; this.hass = this._hass; }
      else if (a === "auto") hass.callService("switch", autoOn ? "turn_off" : "turn_on", { entity_id: c.auto_clean_entity });
    }));
  }
  getCardSize() { return 3; }
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

/* ---------- compact litter box: clean only ---------- */
class BoxMiniCard extends BaseCard {
  static getStubConfig() { return { confirm: true }; }
  static async getConfigElement() { await loadHaForm(); return document.createElement("litter-cat-identifier-box-mini-editor"); }
  signature(hass, box) {
    const c = this._config || {};
    return `${super.signature(hass, box)}${c.clean_entity && hass.states[c.clean_entity]?.last_updated}|${this._armed}`;
  }
  render(hass, box) {
    const T = t(hass), c = this._config;
    const busy = isCleaning(hass, c.clean_entity);
    const total = box ? box.cats.reduce((n, cat) => n + (parseInt(hass.states[cat.visits]?.state) || 0), 0)
      + (parseInt(hass.states[box.unidentified]?.state) || 0) : 0;
    const name = c.title ?? T.box;
    const sub = !c.clean_entity ? T.noClean : busy ? T.cleaning : this._armed ? T.tapAgain : T.visitsToday(total);
    this.shell("", `<div class="lcb-mini"><span class="lcb-badge ${busy ? "busy" : ""}"><ha-icon icon="${busy ? "mdi:rotate-3d-variant" : "mdi:cat"}"></ha-icon></span>
      <div class="lcb-titles"><div class="lci-name">${esc(name)}</div><div class="lci-sub">${esc(sub)}</div></div>
      ${c.clean_entity ? `<button class="lcb-round ${this._armed ? "armed" : ""}" aria-label="${T.clean}" ${busy ? "disabled" : ""}>
        <ha-icon icon="${this._armed ? "mdi:check" : "mdi:broom"}"></ha-icon></button>` : ""}</div>`);
    this.querySelector(".lcb-round")?.addEventListener("click", () => {
      if (on(c.confirm) && !this._armed) {
        this._armed = true;
        clearTimeout(this._armTimer);
        this._armTimer = setTimeout(() => { this._armed = false; this._sig = null; this.hass = this._hass; }, 4000);
      } else {
        this._armed = false;
        runClean(hass, c.clean_entity);
      }
      this._sig = null;
      this.hass = this._hass;
    });
  }
  getCardSize() { return 1; }
  getGridOptions() { return { columns: 6, min_columns: 4, rows: 1 }; }
}
const BoxMiniEditor = makeEditor(() => [
  ...COMMON(),
  { name: "clean_entity", selector: { entity: { domain: ["switch", "button", "script"] } } },
  { name: "confirm", selector: { boolean: {} }, default: true },
]);

const define = (tag, cls) => { if (!customElements.get(tag)) customElements.define(tag, cls); };
define("litter-cat-identifier-cats", CatsCard);
define("litter-cat-identifier-cats-editor", CatsEditor);
define("litter-cat-identifier-cat", CatCard);
define("litter-cat-identifier-cat-editor", CatEditor);
define("litter-cat-identifier-visits", VisitsCard);
define("litter-cat-identifier-visits-editor", VisitsEditor);
define("litter-cat-identifier-weight", WeightCard);
define("litter-cat-identifier-weight-editor", WeightEditor);
define("litter-cat-identifier-visits-chart", VisitsChartCard);
define("litter-cat-identifier-visits-chart-editor", VisitsChartEditor);
define("litter-cat-identifier-box", BoxCard);
define("litter-cat-identifier-box-editor", BoxEditor);
define("litter-cat-identifier-box-mini", BoxMiniCard);
define("litter-cat-identifier-box-mini-editor", BoxMiniEditor);

window.customCards = window.customCards || [];
for (const [type, name, description] of [
  ["litter-cat-identifier-cat", "Litter Cat Identifier – Cat", "One cat: photo, name, weight, visits today and last visit."],
  ["litter-cat-identifier-cats", "Litter Cat Identifier – Cats", "All (or some) cats together: photo, name, weight, visits today and last visit."],
  ["litter-cat-identifier-visits", "Litter Cat Identifier – Recent visits", "Latest litter box visits, with the likely reason for unidentified readings."],
  ["litter-cat-identifier-weight", "Litter Cat Identifier – Weight", "Weight history of each cat."],
  ["litter-cat-identifier-visits-chart", "Litter Cat Identifier – Visits per day", "Bars per day with one bar per cat, 7 or 30 days."],
  ["litter-cat-identifier-box", "Litter Cat Identifier – Litter box", "Clean now, automatic cleaning and today's visits."],
  ["litter-cat-identifier-box-mini", "Litter Cat Identifier – Litter box (compact)", "One row with a clean button."],
]) {
  if (!window.customCards.some((c) => c.type === type)) {
    window.customCards.push({ type, name, description, preview: true,
      documentationURL: "https://github.com/cruzpazv/litter-cat-identifier#dashboard-cards" });
  }
}
