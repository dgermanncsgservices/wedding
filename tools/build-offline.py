#!/usr/bin/env python3
"""Bundle the whole site into one self-contained wedding-offline.html.

Every page keeps its own markup, styles and scripts; images, fonts and the
shared assets/*.js are inlined. The pages are carried as strings and the
router swaps one into the live document at a time, so a page behaves exactly
as it does online — sticky top bar, hamburger, EN/DE switch, collapsible
groups — with no server and no network.

There is deliberately no iframe. srcdoc frames inside a file:// document are
blocked by WebKit, which left the whole bundle blank on iPad: the host CSS
painted its background and nothing else ever appeared. One document works in
every browser, and in restricted viewers like the iOS Files preview.

The one thing that still needs a connection is the 3D string light view: the
artifact pulls three.js from unpkg at runtime, and unpkg is not something this
file can carry. Everything around it, the cut list included, works offline.

Re-run after any sheet sync:  python3 tools/build-offline.py
No network needed; the fonts come from tools/offline-fonts.css.
"""
import base64, json, mimetypes, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "wedding-offline.html"
FONT_CSS = ROOT / "tools" / "offline-fonts.css"

# The hub first: it is what the bundle opens on, as entering the domain does.
PAGES = [
    "index.html",
    "switzerland.html", "apero-switzerland.html", "seating-switzerland.html",
    "canada.html", "indoor-canada.html", "outdoor-canada.html", "setup-canada.html",
    # Carried because parking directions are the thing you most want without a
    # signal. It stays as unlinked here as it is on the site: nothing links to
    # it, it links to nothing, and it is only reachable at #leissigen.html.
    "leissigen.html",
]
HOME = PAGES[0]
ARTIFACT = "assets/string-lights-canada.html"
# The pages share one copy of the fonts, held by the host.

# The router's own behaviour: cross-page links, in-page anchors, a lightbox
# for the plans, and full screen for the 3D. Everything the pages cannot do
# for themselves once they are served from a single file.
SHIM = r"""
  function lightbox(src, alt) {
    var box = document.createElement("div");
    box.className = "wd-lb";
    var img = document.createElement("img");
    img.src = src; img.alt = alt || "";
    // Opens fitted, like the image would in its own tab; tap for 1:1 and pan.
    img.addEventListener("click", function () { box.classList.toggle("zoom"); });
    var x = document.createElement("button");
    x.type = "button"; x.className = "wd-lb-x";
    x.setAttribute("aria-label", "Close"); x.textContent = "\u00d7";
    function close() {
      if (box.parentNode) box.parentNode.removeChild(box);
      document.removeEventListener("keydown", esc);
    }
    function esc(e) { if (e.key === "Escape") close(); }
    x.addEventListener("click", close);
    box.addEventListener("click", function (e) { if (e.target === box) close(); });
    document.addEventListener("keydown", esc);
    box.appendChild(img); box.appendChild(x);
    document.body.appendChild(box);
  }

  document.addEventListener("click", function (e) {
    var node = e.target && e.target.nodeType === 1 ? e.target : null;
    var a = node && node.closest ? node.closest("a[href]") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";

    if (href === "#wd-fullscreen") {                    // the 3D "full screen" hint
      e.preventDefault();
      var f = document.querySelector(".stage-frame iframe") || document.querySelector(".stage-frame");
      if (f && f.requestFullscreen) f.requestFullscreen();
      else if (f && f.webkitRequestFullscreen) f.webkitRequestFullscreen();
      return;
    }
    if (href === "#wd-img") {                           // a plan, by name
      e.preventDefault();
      var im = document.querySelector('img[data-wd-name="' + a.getAttribute("data-wd-img") + '"]');
      if (im) lightbox(im.currentSrc || im.src, im.getAttribute("alt"));
      return;
    }
    if (href.slice(0, 11) === "data:image/") {          // a setup photo, inlined
      e.preventDefault();
      var img = a.querySelector("img");
      lightbox(href, img ? img.getAttribute("alt") : "");
      return;
    }
    var m = href.match(/^([\w.-]+\.html)(#.*)?$/);      // another page of the site
    if (m) {
      e.preventDefault();
      navigate(m[1], m[2] || "");
      return;
    }
    // An in-page anchor. The whole bundle is one document whose own URL
    // carries the routing hash, so these cannot be left to the browser:
    // "#team" would overwrite the route. Scroll, and record it in the route.
    if (href.charAt(0) === "#") {
      e.preventDefault();
      navigate(current, href.length > 1 ? href : "");
    }
  }, true);
"""


HOST = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Lavinia &amp; Daniel — Wedding (offline)</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style id="wd-fonts">__FONTS__</style>
<style id="wd-host">
  /* top/right/bottom/left before inset: Safari only learned inset in 14.1. */
  .wd-lb{position:fixed;top:0;right:0;bottom:0;left:0;inset:0;z-index:999;
    background:rgba(18,6,9,.94);overflow:auto;
    -webkit-overflow-scrolling:touch;padding:0;margin:0}
  .wd-lb img{display:block;margin:0 auto;max-width:100%;height:auto;cursor:zoom-in}
  .wd-lb.zoom img{max-width:none;width:auto;cursor:zoom-out}
  .wd-lb-x{position:fixed;top:.55rem;right:.55rem;z-index:1000;appearance:none;border:0;
    border-radius:999px;width:2.4rem;height:2.4rem;font:500 1.3rem/1 system-ui,sans-serif;
    color:#2C0D12;background:#C9A877;cursor:pointer}
  .wd-msg{margin:0;padding:2rem;background:#4A161E;color:#F1E7D6;
    font:400 1rem/1.6 system-ui,sans-serif;min-height:100vh}
  .wd-msg a{color:#C9A877}
  .wd-msg code{display:block;margin-top:1rem;font-size:.82rem;color:#E6C9A0;word-break:break-word}
</style>
</head>
<body>
<noscript><p class="wd-msg">This offline copy needs JavaScript. The live site is
<a href="https://wedding.germann-mail.com">wedding.germann-mail.com</a>.</p></noscript>
<script>
(function () {
  "use strict";

  var PAGES = __PAGES__;
  var HOME = __HOME__;
  var current = null;

  // A blank page tells the reader nothing. If anything here fails, say so.
  function fail(what, err) {
    document.body.innerHTML = "";
    var p = document.createElement("p");
    p.className = "wd-msg";
    p.appendChild(document.createTextNode(
      "Sorry — this offline copy could not open " + what + " on this device. " +
      "The live site is wedding.germann-mail.com."));
    var c = document.createElement("code");
    c.textContent = String(err && (err.stack || err.message || err));
    p.appendChild(c);
    document.body.appendChild(p);
  }
  window.onerror = function (msg, src, line) { fail("a page", msg + " (line " + line + ")"); };

  // ---------------- rendering ----------------
  // One document, one page in it at a time. Nothing is sandboxed, nothing is
  // fetched, and duplicate ids and styles across pages can never collide
  // because only one page is ever present.
  function render(name) {
    var dom = new DOMParser().parseFromString(PAGES[name], "text/html");

    // Drop the previous page: its <style> blocks, and the ones i18n.js and
    // nav.js append at runtime. Ours are the only styles with an id.
    var stale = document.head.querySelectorAll("style:not([id]), [data-wd]");
    for (var i = 0; i < stale.length; i++) stale[i].parentNode.removeChild(stale[i]);

    // Styles and scripts come out of the parsed copy first: scripts inserted
    // through innerHTML never run, so they are re-created by hand below.
    var styles = dom.querySelectorAll("style");
    for (var j = 0; j < styles.length; j++) {
      var st = document.createElement("style");
      st.setAttribute("data-wd", "");
      st.textContent = styles[j].textContent;
      document.head.appendChild(st);
      styles[j].parentNode.removeChild(styles[j]);
    }
    var found = dom.querySelectorAll("script"), scripts = [];
    for (var k = 0; k < found.length; k++) {
      scripts.push(found[k].textContent);
      found[k].parentNode.removeChild(found[k]);
    }

    document.title = dom.title || "Lavinia & Daniel";
    document.documentElement.lang = dom.documentElement.getAttribute("lang") || "en";
    document.body.innerHTML = dom.body.innerHTML;

    // In order, synchronously: the page's own I18N_PAGE, then i18n.js,
    // the day menu, nav.js, and the page's renderer. Each checks
    // document.readyState and initialises straight away once loaded.
    for (var n = 0; n < scripts.length; n++) {
      var s = document.createElement("script");
      s.setAttribute("data-wd", "");
      s.text = scripts[n];
      document.body.appendChild(s);
    }
    current = name;
  }

  function jump(hash) {
    if (!hash) return window.scrollTo(0, 0);
    var el = null;
    try { el = document.querySelector(hash); } catch (e) { /* not a selector */ }
    if (!el) return window.scrollTo(0, 0);
    // Instant, the way the real site lands on canada.html#team. A click
    // within a page keeps the page's own smooth scrolling, below.
    try { el.scrollIntoView({ behavior: "instant", block: "start" }); }
    catch (e) { el.scrollIntoView(); }
  }

  // ---------------- routing ----------------
  // The document's own hash carries the route: "#canada.html!team".
  function parse() {
    var h = location.hash.replace(/^#/, "");
    if (!h) return { page: HOME, hash: "" };
    var i = h.indexOf("!");
    if (i === -1) return { page: h, hash: "" };
    return { page: h.slice(0, i), hash: "#" + h.slice(i + 1) };
  }

  function go() {
    var s = parse();
    if (!PAGES[s.page]) s = { page: HOME, hash: "" };
    try {
      if (s.page !== current) {
        render(s.page);
        jump(s.hash);
      } else if (s.hash) {
        // Already here: let the page's own scroll-behavior do the work.
        var el = null;
        try { el = document.querySelector(s.hash); } catch (e) {}
        if (el) el.scrollIntoView();
      } else {
        window.scrollTo(0, 0);
      }
    } catch (err) { fail(s.page, err); }
  }

  function navigate(page, hash) {
    var next = "#" + page + (hash ? "!" + hash.replace(/^#/, "") : "");
    if (location.hash === next) go(); else location.hash = next;
  }

__SHIM__

  window.addEventListener("hashchange", go);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go);
  else go();
})();
</script>
</body>
</html>
"""


def data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode("ascii"))


def attr_escape(html: str) -> str:
    return html.replace("&", "&amp;").replace('"', "&quot;")


def build_page(name: str, artifact: str) -> str:
    src = (ROOT / name).read_text(encoding="utf-8")

    # 1. Fonts: drop the Google preconnects and swap the stylesheet for the
    #    inlined faces, so nothing reaches for the network.
    src = re.sub(r'[ \t]*<link rel="preconnect" href="https://fonts\.[^"]+"[^>]*>\n', "", src)
    src, n = re.subn(r'[ \t]*<link href="https://fonts\.googleapis\.com/css2[^"]*" rel="stylesheet">\n?',
                     "", src)
    if n != 1:
        sys.exit("%s: expected one Google Fonts <link>, found %d" % (name, n))

    # 2. Mark the document as the offline copy, before any page script runs,
    #    so the day menus leave out their "Offline copy" download link.
    #    The charset tag is spelled a few different ways across the pages, so
    #    match it rather than guess.
    src, n = re.subn(r'(<meta charset=["\']?[\w-]+["\']?\s*/?>)',
                     r'\1\n<script>window.WD_OFFLINE = 1;</script>',
                     src, count=1)
    if n != 1:
        sys.exit("%s: no <meta charset> to mark the document as offline" % name)

    # 3. The shared modules, in the order the page loads them.
    def inline_script(m: "re.Match") -> str:
        js = (ROOT / m.group(1)).read_text(encoding="utf-8")
        return "<script>\n" + js + "</script>"
    src, n = re.subn(r'<script src="(assets/[\w.-]+\.js)"></script>', inline_script, src)
    if n == 0 and 'assets/' in src:
        sys.exit("%s: asset references left but no scripts inlined" % name)

    # 4. The 3D artifact, before the image pass so its own paths are untouched.
    if ARTIFACT in src:
        src = src.replace('src="%s"' % ARTIFACT, 'srcdoc="%s"' % attr_escape(artifact))
        src = src.replace('href="%s" target="_blank" rel="noopener"' % ARTIFACT, 'href="#wd-fullscreen"')

    # 5. Images, in markup and in the setup page's JS data alike. A plan is
    #    referenced up to three times per page — the <img>, the link around it
    #    and the "tap to open full size" hint — so only the <img> gets the
    #    bytes and the links point at it by name; the shim opens the lightbox
    #    from there. Inlining all three would carry the photo three times.
    for img in sorted((ROOT / "assets").glob("*.jpg")):
        ref = "assets/" + img.name
        if ref not in src:
            continue
        src = src.replace('href="%s"' % ref, 'href="#wd-img" data-wd-img="%s"' % img.name)
        src = src.replace('src="%s"' % ref, 'src="%s" data-wd-name="%s"' % (data_uri(img), img.name))
        src = src.replace(ref, data_uri(img))   # the setup page's JS picture data

    left = re.findall(r'(?:src|href)="(assets/[^"]+)"', src)
    if left:
        sys.exit("%s: un-inlined asset(s): %s" % (name, sorted(set(left))))

    if "WD_OFFLINE" not in src:
        sys.exit("%s: the offline marker did not survive the build" % name)
    return src


def main() -> None:
    if not FONT_CSS.exists():
        sys.exit("missing %s — run tools/fetch-fonts.py first" % FONT_CSS)
    fonts = FONT_CSS.read_text(encoding="utf-8")
    artifact = (ROOT / ARTIFACT).read_text(encoding="utf-8")

    docs = {name: build_page(name, artifact) for name in PAGES}
    # "</" would close the host's <script> early, wherever it appears in a page.
    pages_json = json.dumps(docs, ensure_ascii=False).replace("</", "<\\/")

    html = (HOST.replace("__SHIM__", SHIM)
                .replace("__FONTS__", fonts)
                .replace("__PAGES__", pages_json)
                .replace("__HOME__", json.dumps(HOME)))
    for token in ("__SHIM__", "__FONTS__", "__PAGES__", "__HOME__"):
        if token in html:
            sys.exit("host template still holds %s" % token)
    OUT.write_text(html, encoding="utf-8")
    print("wrote %s — %d pages, %.1f MB" % (OUT.name, len(docs), OUT.stat().st_size / 1048576))


if __name__ == "__main__":
    main()
