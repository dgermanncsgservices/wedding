/* The Canada day's menu, shared by every page in that section.
 *
 * canada.html and setup-canada.html both load this, so the menu is identical
 * throughout the day; only the link targets differ, depending on whether the
 * timeline is on the current page or another one.
 *
 * GROUPS mirrors the Group column of the sheet's Celebration Canada tab, which
 * currently has none — the timeline renders flat and the menu points at the
 * schedule section as a whole. When a sync introduces groups, list them here;
 * canada.html logs a warning if the two drift apart.
 */
(function () {
  "use strict";

  var GROUPS = [];
  var DAY_PAGE = "canada.html";
  var INDOOR_PAGE = "indoor-canada.html";
  var OUTDOOR_PAGE = "outdoor-canada.html";
  var SETUP_PAGE = "setup-canada.html";

  // Must match groupId() in canada.html: slug the English name so the anchors
  // survive a language switch.
  function slug(name) {
    return "g-" + name.toLowerCase()
      .replace(/é/g, "e").replace(/[äöü]/g, function (c) {
        return { "ä": "a", "ö": "o", "ü": "u" }[c];
      })
      .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  window.WD_DAY_GROUPS = GROUPS;

  window.WD_NAV_ITEMS = function () {
    var t = function (s) { return window.WD_I18N ? window.WD_I18N.t(s, s) : s; };
    var base = document.getElementById("tl-ca") ? "" : DAY_PAGE;
    var items = GROUPS.map(function (g) {
      return { href: base + "#" + slug(g), label: t(g) };
    });
    if (!items.length) items.push({ href: base + "#schedule", label: t("Day-of Timeline") });
    items.push({ href: base + "#team", label: t("Day-of Team") });
    items.push({ href: INDOOR_PAGE, label: t("Indoors") });
    items.push({ href: OUTDOOR_PAGE, label: t("Outdoors") });
    items.push({ href: SETUP_PAGE, label: t("Setup Plan") });
    return items;
  };
})();
