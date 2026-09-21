/* The Switzerland day's menu, shared by every page in that section.
 *
 * switzerland.html and seating-switzerland.html both load this, so the menu is
 * identical throughout the day; only the link targets differ, depending on
 * whether the timeline is on the current page or another one.
 *
 * GROUPS mirrors the Group column of the sheet's Switzerland tab. When a sync
 * adds or renames a group, update it here too — switzerland.html logs a warning
 * if the two drift apart.
 */
(function () {
  "use strict";

  var GROUPS = ["Setup", "Ceremony", "Apéro", "Reception"];
  var DAY_PAGE = "switzerland.html";
  var SEATING_PAGE = "seating-switzerland.html";

  // Must match groupId() in switzerland.html: slug the English name so the
  // anchors survive a language switch.
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
    // On the seating page the timeline lives elsewhere, so anchors need the page.
    var base = document.getElementById("tl-ch") ? "" : DAY_PAGE;
    var items = GROUPS.map(function (g) {
      return { href: base + "#" + slug(g), label: t(g) };
    });
    items.push({ href: base + "#team", label: t("Day-of Team") });
    items.push({ href: SEATING_PAGE, label: t("Seating") });
    return items;
  };
})();
