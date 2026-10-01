#!/usr/bin/env python3
"""Print each event day to its own PDF — what the menus offer for download.

A PDF needs nothing of the device, so this is what a guest gets when they tap
"Download PDF", and what to print for the day itself. One per day per
language: a Switzerland guest has no use for the Canada setup plan.

    python3 tools/build-pdf.py                 # all four
    python3 tools/build-pdf.py switzerland de  # just one

Re-run after a sheet sync, like the HTML bundle. Needs Chromium and pdfrw.
"""
import pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

# One document per event, in the order someone would page through it on the
# day: the schedule and team first, then the plans.
#
# leissigen.html is deliberately left out. It is unlinked on the site by
# design — the URL is shared directly with the people who need it — and a PDF
# has no way to carry a page without also handing it to everyone who opens
# the file.
SECTIONS = {
    "switzerland": ["switzerland.html", "apero-switzerland.html", "seating-switzerland.html"],
    "canada": ["canada.html", "indoor-canada.html", "outdoor-canada.html", "setup-canada.html"],
}
LANGS = ["en", "de"]

CHROME_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
    "chromium", "chromium-browser", "google-chrome",
]

PRINT_CSS = """
<style id="wd-print">
  @page { size: A4; margin: 12mm 10mm; }
  html, body {
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
    scroll-behavior: auto;
  }
  /* Navigation is meaningless on paper. */
  .topbar, .navlinks, .nav-panel, .nav-toggle, .lang-switch { display: none !important; }
  /* Every disclosure is opened below; the pill that opens it would just confuse. */
  .t-chip { display: none !important; }
  details > summary { list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details > summary::marker { content: ""; }
  /* The 3D view cannot be printed; its cut list, just below, is what matters. */
  .stage-frame { display: none !important; }
  /* A tall plan is 1880px high: without a ceiling it runs past the bottom of
     the page and leaves the overflow on a blank one. Cap it to the printable
     height and let the width follow. */
  img { max-width: 100% !important; max-height: 200mm !important;
        width: auto !important; height: auto !important; }
  /* "Tap the plan to open it full size" — not on paper. */
  .chart-hint { display: none !important; }
  /* Keep a row, a card or a plan photo whole rather than split across a page. */
  .t-row, .card, .event-block, .cut-table tr, .chart-frame, figure { break-inside: avoid; }
  /* A heading that splits from its own chart reads as two broken pages. */
  .section-head, .panel-head { break-inside: avoid; break-after: avoid; }
  h1, h2, h3 { break-after: avoid; }
  footer { break-before: avoid; }
  a { text-decoration: none; color: inherit; }
</style>
"""

# Runs after the page has rendered itself, so every collapsible section is on
# the paper. The page builds its timeline on DOMContentLoaded, which is before
# load, so this needs no delay — the second pass is belt and braces.
EXPAND_JS = """
<script>
(function () {
  function openAll() {
    var d = document.querySelectorAll("details");
    for (var i = 0; i < d.length; i++) d[i].open = true;
    var f = document.querySelector(".stage-frame");
    if (f && f.parentNode) {
      var p = document.createElement("p");
      p.className = "chart-hint";
      p.textContent = "The 3D string light plan is on the website \\u2014 the cut list follows.";
      f.parentNode.replaceChild(p, f);
    }
    document.documentElement.setAttribute("data-wd-print-ready", "1");
  }
  if (document.readyState === "complete") openAll();
  else window.addEventListener("load", openAll);
  setTimeout(openAll, 600);
})();
</script>
"""


def chrome() -> str:
    for c in CHROME_CANDIDATES:
        if "/" in c and pathlib.Path(c).exists():
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.exit("no Chromium found — looked for: %s" % ", ".join(CHROME_CANDIDATES))


def prepare(name: str, lang: str, dest: pathlib.Path) -> pathlib.Path:
    src = (ROOT / name).read_text(encoding="utf-8")

    if lang != "en":
        # i18n.js reads this the moment it loads, so it has to be set first.
        src, n = re.subn(r'(<meta charset=["\']?[\w-]+["\']?\s*/?>)',
                         r'\1\n<script>try{localStorage.setItem("wd-lang","%s");}catch(e){}</script>' % lang,
                         src, count=1)
        if n != 1:
            sys.exit("%s: no <meta charset> to set the language on" % name)

    extra = PRINT_CSS + EXPAND_JS
    for close in ("</body>", "</html>"):
        if close in src:
            src = src.replace(close, extra + close, 1)
            break
    else:
        src = src + extra

    out = dest / name
    out.write_text(src, encoding="utf-8")
    return out


def build(section: str, lang: str, browser: str) -> pathlib.Path:
    from pdfrw import PdfReader, PdfWriter

    names = SECTIONS[section]
    out_pdf = ROOT / ("wedding-%s%s.pdf" % (section, "" if lang == "en" else "-" + lang))
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        # The pages reference assets/ relatively, so give them one.
        (work / "assets").symlink_to(ROOT / "assets")
        parts = []
        for name in names:
            prepare(name, lang, work)
            pdf = work / name.replace(".html", ".pdf")
            r = subprocess.run([
                browser, "--headless", "--disable-gpu", "--no-sandbox",
                "--no-pdf-header-footer", "--virtual-time-budget=20000",
                "--print-to-pdf=%s" % pdf, (work / name).as_uri(),
            ], capture_output=True, text=True, timeout=180)
            if not pdf.exists():
                sys.exit("failed to print %s\n%s" % (name, r.stderr[-800:]))
            parts.append(pdf)

        writer = PdfWriter()
        for pdf in parts:
            writer.addpages(PdfReader(str(pdf)).pages)
        writer.write(str(out_pdf))

    pages = len(PdfReader(str(out_pdf)).pages)
    print("  %-28s %2d pages from %d sections, %.1f MB"
          % (out_pdf.name, pages, len(names), out_pdf.stat().st_size / 1048576))
    return out_pdf


def main() -> None:
    args = [a.lower() for a in sys.argv[1:]]
    sections = [a for a in args if a in SECTIONS] or list(SECTIONS)
    langs = [a for a in args if a in LANGS] or LANGS
    unknown = [a for a in args if a not in SECTIONS and a not in LANGS]
    if unknown:
        sys.exit("unknown argument(s): %s — expected one of %s"
                 % (", ".join(unknown), ", ".join(list(SECTIONS) + LANGS)))

    try:
        import pdfrw  # noqa: F401
    except ImportError:
        sys.exit("pdfrw is needed to join the pages: pip install pdfrw")

    browser = chrome()
    for section in sections:
        for lang in langs:
            build(section, lang, browser)


if __name__ == "__main__":
    main()
