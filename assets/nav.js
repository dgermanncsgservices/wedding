/* Mobile hamburger menu for the top bar.
 *
 * Wraps the existing .navlinks and the language switcher into one panel that
 * collapses behind a hamburger below 640px and stays inline above it. Loads
 * after assets/i18n.js so the language switcher already exists in the bar.
 */
(function () {
  "use strict";

  var BP = "(max-width: 640px)";

  var STYLE = [
    ".nav-panel{display:flex;align-items:center;gap:0.6rem;min-width:0}",
    ".nav-toggle{display:none}",
    "@media " + BP + "{",
      ".topbar{position:relative}",
      ".nav-toggle{",
        "display:inline-flex;flex-direction:column;justify-content:center;gap:4px;",
        "flex:none;width:42px;height:38px;padding:0 10px;cursor:pointer;",
        "background:transparent;border:1px solid var(--line,#DACBAE);border-radius:999px;",
        "transition:border-color .2s ease}",
      ".nav-toggle span{display:block;height:1.5px;width:100%;border-radius:2px;",
        "background:var(--text-soft,#7A6266);transition:transform .2s ease,opacity .2s ease}",
      ".nav-toggle:hover{border-color:var(--accent,#C9A877)}",
      ".nav-toggle:focus-visible{outline:2px solid var(--accent,#C9A877);outline-offset:2px}",
      ".nav-toggle[aria-expanded='true'] span:nth-child(1){transform:translateY(5.5px) rotate(45deg)}",
      ".nav-toggle[aria-expanded='true'] span:nth-child(2){opacity:0}",
      ".nav-toggle[aria-expanded='true'] span:nth-child(3){transform:translateY(-5.5px) rotate(-45deg)}",
      ".nav-panel{",
        "display:none;position:absolute;top:100%;left:0;right:0;z-index:39;",
        "flex-direction:column;align-items:stretch;gap:0.5rem;",
        "padding:0.9rem clamp(1rem,4vw,2.5rem) 1.1rem;",
        "background:var(--bg,var(--cream-050,#FBF7EE));",
        "border-bottom:1px solid var(--line,#DACBAE);",
        "box-shadow:0 20px 34px -26px rgba(0,0,0,0.55)}",
      ".nav-panel[data-open]{display:flex}",
      ".nav-panel .navlinks{flex-direction:column;gap:0.45rem;overflow:visible}",
      ".nav-panel .navlinks a{text-align:center;padding:0.62rem 0.95rem}",
      ".nav-panel .lang-switch{align-self:center;margin-top:0.2rem}",
    "}"
  ].join("");

  function init() {
    var bar = document.querySelector(".topbar");
    var links = bar && bar.querySelector(".navlinks");
    if (!bar || !links) return;                 // pages without a nav keep the plain bar

    var style = document.createElement("style");
    style.textContent = STYLE;
    document.head.appendChild(style);

    var panel = document.createElement("div");
    panel.className = "nav-panel";
    panel.id = "nav-panel";
    bar.insertBefore(panel, links);
    panel.appendChild(links);

    var lang = bar.querySelector(".lang-switch");   // injected by i18n.js
    if (lang) panel.appendChild(lang);

    // A page can describe its own menu (the sections of that day) through
    // window.WD_NAV_ITEMS; otherwise the markup's links are kept as they are.
    function fillLinks() {
      if (typeof window.WD_NAV_ITEMS !== "function") return;
      var items = window.WD_NAV_ITEMS() || [];
      while (links.firstChild) links.removeChild(links.firstChild);
      items.forEach(function (item) {
        var a = document.createElement("a");
        a.href = item.href;
        a.textContent = item.label;
        links.appendChild(a);
      });
    }
    fillLinks();

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "nav-toggle";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "nav-panel");
    toggle.setAttribute("aria-label", "Menu");
    for (var i = 0; i < 3; i++) toggle.appendChild(document.createElement("span"));
    bar.insertBefore(toggle, panel);

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", String(open));
      if (open) panel.setAttribute("data-open", "");
      else panel.removeAttribute("data-open");
    }

    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Following a link or picking a language closes the menu.
    panel.addEventListener("click", function (e) {
      if (e.target.closest("a, .lang-switch button")) setOpen(false);
    });

    document.addEventListener("click", function (e) {
      if (!bar.contains(e.target)) setOpen(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });

    // Leaving mobile width must not strand the panel in its open state.
    var mq = window.matchMedia(BP);
    var onChange = function () { if (!mq.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange);

    if (window.WD_I18N) {
      window.WD_I18N.onChange(function () {
        toggle.setAttribute("aria-label", window.WD_I18N.t("Menu", "Menu"));
        fillLinks();
      });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
