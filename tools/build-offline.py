#!/usr/bin/env python3
"""Bundle the whole site into one self-contained wedding-offline.html.

Every page keeps its own markup, styles and scripts; images, fonts and the
shared assets/*.js are inlined, and the pages are carried as srcdoc documents
inside one host frame. Each page therefore behaves exactly as it does online —
sticky top bar, hamburger, EN/DE switch, collapsible groups — with no server
and no network.

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
# One copy of the 380 KB of fonts lives in the host; each page carries this
# marker instead, and the host splices the faces in as it shows the page.
FONT_SLOT = "/*WD_FONTS*/"

# Injected into every page: cross-page links, a lightbox for the plans, and
# full screen for the 3D — the three things that need a server or a real URL.
SHIM = r"""
<style>
  .wd-lb{position:fixed;inset:0;z-index:999;background:rgba(18,6,9,.94);overflow:auto;
    -webkit-overflow-scrolling:touch;padding:0;margin:0}
  .wd-lb img{display:block;margin:0 auto;max-width:100%;height:auto;cursor:zoom-in}
  .wd-lb.zoom img{max-width:none;width:auto;cursor:zoom-out}
  .wd-lb-x{position:fixed;top:.55rem;right:.55rem;z-index:1000;appearance:none;border:0;
    border-radius:999px;width:2.4rem;height:2.4rem;font:500 1.3rem/1 system-ui,sans-serif;
    color:#2C0D12;background:#C9A877;cursor:pointer}
</style>
<script>
(function () {
  "use strict";

  function lightbox(src, alt) {
    var box = document.createElement("div");
    box.className = "wd-lb";
    var img = document.createElement("img");
    img.src = src; img.alt = alt || "";
    // Opens fitted, like the image would in its own tab; tap for 1:1 and pan.
    img.addEventListener("click", function () { box.classList.toggle("zoom"); });
    var x = document.createElement("button");
    x.type = "button"; x.className = "wd-lb-x"; x.setAttribute("aria-label", "Close"); x.textContent = "×";
    function close() { box.remove(); document.removeEventListener("keydown", esc); }
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
      parent.postMessage({ wdNav: 1, page: m[1], hash: m[2] || "" }, "*");
    }
  }, true);

  // The host frame asks for an anchor once the page has loaded.
  window.addEventListener("message", function (e) {
    var d = e.data || {};
    if (!d.wdGo) return;
    var el = null;
    try { el = document.querySelector(d.wdGo); } catch (err) { /* not a selector */ }
    if (el) el.scrollIntoView();
  });
})();
</script>
"""

HOST = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Lavinia &amp; Daniel — Wedding (offline)</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  html, body {{ margin: 0; height: 100%; background: #4A161E; }}
  #view {{ display: block; border: 0; width: 100%; height: 100%; }}
  noscript p {{ color: #F1E7D6; font: 400 1rem/1.6 system-ui, sans-serif; padding: 2rem; }}
</style>
</head>
<body>
<noscript><p>This offline copy needs JavaScript. The live site is
<a href="https://wedding.germann-mail.com" style="color:#C9A877">wedding.germann-mail.com</a>.</p></noscript>
<iframe id="view" title="Lavinia &amp; Daniel — wedding"></iframe>
<script>
var PAGES = {pages};
var HOME = {home};
var FONTS = {fonts};
var SLOT = {slot};
var view = document.getElementById("view");
var current = null, pending = "";

function parse() {{
  var h = location.hash.replace(/^#/, "");
  if (!h) return {{ page: HOME, hash: "" }};
  var i = h.indexOf("!");                       // "#canada.html!g-apero"
  if (i === -1) return {{ page: h, hash: "" }};
  return {{ page: h.slice(0, i), hash: "#" + h.slice(i + 1) }};
}}

function go() {{
  var s = parse();
  if (!PAGES[s.page]) s = {{ page: HOME, hash: "" }};
  if (s.page === current) {{                     // same page, just jump
    if (s.hash) view.contentWindow.postMessage({{ wdGo: s.hash }}, "*");
    return;
  }}
  current = s.page; pending = s.hash;
  // A function replacement, so "$&" and friends in the CSS stay literal.
  view.srcdoc = PAGES[s.page].replace(SLOT, function () {{ return FONTS; }});
}}

view.addEventListener("load", function () {{
  if (pending) view.contentWindow.postMessage({{ wdGo: pending }}, "*");
  pending = "";
}});

window.addEventListener("message", function (e) {{
  var d = e.data || {{}};
  if (!d.wdNav) return;
  var next = "#" + d.page + (d.hash ? "!" + d.hash.replace(/^#/, "") : "");
  if (location.hash === next) go(); else location.hash = next;
}});

window.addEventListener("hashchange", go);
go();
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
    src, n = re.subn(r'<link href="https://fonts\.googleapis\.com/css2[^"]*" rel="stylesheet">',
                     "<style>" + FONT_SLOT + "</style>", src)
    if n != 1:
        sys.exit("%s: expected one Google Fonts <link>, found %d" % (name, n))

    # 2. The shared modules, in the order the page loads them.
    def inline_script(m: "re.Match") -> str:
        js = (ROOT / m.group(1)).read_text(encoding="utf-8")
        return "<script>\n" + js + "</script>"
    src, n = re.subn(r'<script src="(assets/[\w.-]+\.js)"></script>', inline_script, src)
    if n == 0 and 'assets/' in src:
        sys.exit("%s: asset references left but no scripts inlined" % name)

    # 3. The 3D artifact, before the image pass so its own paths are untouched.
    if ARTIFACT in src:
        src = src.replace('src="%s"' % ARTIFACT, 'srcdoc="%s"' % attr_escape(artifact))
        src = src.replace('href="%s" target="_blank" rel="noopener"' % ARTIFACT, 'href="#wd-fullscreen"')

    # 4. Images, in markup and in the setup page's JS data alike. A plan is
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

    # 5. The shim goes last so it sees the finished document.
    if "</body>" in src:
        return src.replace("</body>", SHIM + "</body>", 1)
    return src + SHIM


def main() -> None:
    if not FONT_CSS.exists():
        sys.exit("missing %s — run tools/fetch-fonts.py first" % FONT_CSS)
    fonts = FONT_CSS.read_text(encoding="utf-8")
    artifact = (ROOT / ARTIFACT).read_text(encoding="utf-8")

    docs = {name: build_page(name, artifact) for name in PAGES}
    # "</" would close the host's <script> early, wherever it appears in a page.
    pages_json = json.dumps(docs, ensure_ascii=False).replace("</", "<\\/")

    OUT.write_text(HOST.format(pages=pages_json, home=json.dumps(HOME),
                               fonts=json.dumps(fonts), slot=json.dumps(FONT_SLOT)),
                   encoding="utf-8")
    print("wrote %s — %d pages, %.1f MB" % (OUT.name, len(docs), OUT.stat().st_size / 1048576))


if __name__ == "__main__":
    main()
