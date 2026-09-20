/* Shared EN/DE language switching for the wedding site.
 *
 * A page declares its German strings as window.I18N_PAGE.de before loading
 * this file. Keys are either a dotted key (for static markup, matched by a
 * data-i18n attribute) or the English source string itself (for the data the
 * page renders from the spreadsheet). Anything without a translation falls
 * back to English, so a fresh sheet sync never blanks the page.
 */
(function () {
  "use strict";

  var KEY = "wd-lang";
  var SUPPORTED = ["en", "de"];
  var listeners = [];
  var lang = detect();

  // Saved choice wins; otherwise follow the device language.
  function detect() {
    try {
      var saved = window.localStorage.getItem(KEY);
      if (SUPPORTED.indexOf(saved) !== -1) return saved;
    } catch (e) { /* private mode, blocked storage */ }
    var langs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || navigator.userLanguage || "en"];
    for (var i = 0; i < langs.length; i++) {
      var l = String(langs[i]).toLowerCase();
      if (l.indexOf("de") === 0) return "de";
      if (l.indexOf("en") === 0) return "en";
    }
    return "en";
  }

  function dict() {
    var p = window.I18N_PAGE || {};
    return (lang !== "en" && p[lang]) ? p[lang] : {};
  }

  // Translate one string, falling back to the English original.
  function t(key, fallback) {
    var d = dict();
    if (Object.prototype.hasOwnProperty.call(d, key)) return d[key];
    return fallback !== undefined ? fallback : key;
  }

  function applyMarkup() {
    document.documentElement.lang = lang;

    var d = dict();
    [].forEach.call(document.querySelectorAll("[data-i18n]"), function (node) {
      if (node.__i18nOrig === undefined) node.__i18nOrig = node.innerHTML;
      var k = node.getAttribute("data-i18n");
      node.innerHTML = Object.prototype.hasOwnProperty.call(d, k) ? d[k] : node.__i18nOrig;
    });

    // data-i18n-attr="alt:seating.alt" — translate an attribute instead of text.
    [].forEach.call(document.querySelectorAll("[data-i18n-attr]"), function (node) {
      node.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
        var bits = pair.split(":");
        var attr = bits[0].trim(), k = bits[1] && bits[1].trim();
        if (!attr || !k) return;
        if (node.__i18nAttr === undefined) node.__i18nAttr = {};
        if (node.__i18nAttr[attr] === undefined) node.__i18nAttr[attr] = node.getAttribute(attr) || "";
        node.setAttribute(attr, Object.prototype.hasOwnProperty.call(d, k) ? d[k] : node.__i18nAttr[attr]);
      });
    });

    if (Object.prototype.hasOwnProperty.call(d, "page.title")) {
      if (document.__i18nTitle === undefined) document.__i18nTitle = document.title;
      document.title = d["page.title"];
    } else if (document.__i18nTitle !== undefined) {
      document.title = document.__i18nTitle;
    }
  }

  function setLang(next) {
    if (SUPPORTED.indexOf(next) === -1 || next === lang) return;
    lang = next;
    try { window.localStorage.setItem(KEY, lang); } catch (e) { /* ignore */ }
    applyMarkup();
    syncButtons();
    listeners.forEach(function (fn) { fn(lang); });
  }

  // ---------------- switcher ----------------
  var STYLE = [
    ".lang-switch{display:inline-flex;border:1px solid var(--line,#DACBAE);border-radius:999px;overflow:hidden;flex:none}",
    ".lang-switch button{appearance:none;background:transparent;border:0;cursor:pointer;",
    "font-family:'Jost',ui-sans-serif,system-ui,sans-serif;font-size:0.72rem;font-weight:500;",
    "letter-spacing:0.1em;text-transform:uppercase;padding:0.5rem 0.7rem;color:var(--text-soft,#7A6266);",
    "transition:background .2s ease,color .2s ease}",
    ".lang-switch button+button{border-left:1px solid var(--line,#DACBAE)}",
    ".lang-switch button:hover{color:var(--text,#2A1418)}",
    ".lang-switch button[aria-pressed='true']{background:var(--accent,#C9A877);color:#2C0D12}",
    ".lang-switch button:focus-visible{outline:2px solid var(--accent,#C9A877);outline-offset:-2px}",
    ".lang-switch-float{position:fixed;top:1rem;right:1rem;z-index:50;background:var(--surface,#fff)}"
  ].join("");

  var buttons = [];

  function syncButtons() {
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === lang));
    });
  }

  function buildSwitcher() {
    var style = document.createElement("style");
    style.textContent = STYLE;
    document.head.appendChild(style);

    var box = document.createElement("div");
    box.className = "lang-switch";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "Language / Sprache");

    [["en", "EN", "English"], ["de", "DE", "Deutsch"]].forEach(function (spec) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("data-lang", spec[0]);
      b.setAttribute("lang", spec[0]);
      b.setAttribute("title", spec[2]);
      b.textContent = spec[1];
      b.addEventListener("click", function () { setLang(spec[0]); });
      box.appendChild(b);
      buttons.push(b);
    });

    // Sits in the top bar where there is one, otherwise floats in the corner.
    var bar = document.querySelector(".topbar");
    if (bar) bar.appendChild(box);
    else { box.classList.add("lang-switch-float"); document.body.appendChild(box); }
    syncButtons();
  }

  function init() {
    buildSwitcher();
    applyMarkup();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  window.WD_I18N = {
    get lang() { return lang; },
    t: t,
    set: setLang,
    // Call with a render function: runs now and again on every switch.
    onChange: function (fn) { listeners.push(fn); fn(lang); }
  };
})();
