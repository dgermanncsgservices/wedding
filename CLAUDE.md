# Lavinia & Daniel — wedding site

Static site, no build step. GitHub Pages deploys from `main`; custom domain
`wedding.germann-mail.com` via the `CNAME` file.

- `index.html` — hub linking to both events
- `canada.html` — Celebration Canada
- `switzerland.html` — Switzerland (ceremony, Apéro, reception)
- `seating-switzerland.html` + `assets/seating-switzerland.jpg` — static seating chart
- `apero-switzerland.html` + `assets/apero-switzerland.jpg` — static Apéro site plan
- `indoor-canada.html` — Canada indoors: the 3D floor plan and the seating chart
- `outdoor-canada.html` — Canada outdoors: the floor plan and the seating chart
- `setup-canada.html` — the Canada setup plan for the crew
- `leissigen.html` — German-only parking directions for the Swiss reception at the Alti Sagi in Leissigen, served at `/leissigen`. Guest-facing but deliberately **unlinked**: no page links to it and it links to no other page (share the URL directly). Self-contained — own inline street map and data, no `i18n.js`/`nav.js`; `noindex`.

The static plan pages share one template: top bar, centred
`.section-head`, a `.chart-frame` holding the image, a `.chart-hint` line,
footer. The image is wrapped in a link to its own file — labels on an aerial
plan are unreadable at phone width, so tapping opens it full size. To add
another, copy one of them, swap the image, the `data-i18n` keys and the `de`
entries, then add it to that section's day file so the whole section's menu
picks it up.

## The spreadsheet is the master

Schedule and responsibilities data lives in the Google Drive file **"Wedding
Planning Spreadsheet"** (file ID `1fADR4WRdslSFRoZzQK-BNTRFU2e0CB0qTLTxHrtl0eI`).

**Always sync sheet → website, never the other way.** The pages embed the data
as JS arrays, so a sync means rewriting those arrays to match the sheet:

| Sheet tab          | Page               | Arrays                                 |
| ------------------ | ------------------ | -------------------------------------- |
| Switzerland        | `switzerland.html` | `scheduleCH`, `team`, `equipment`      |
| Celebration Canada | `canada.html`      | `scheduleCA`, `team`                   |

Rules when syncing:

- A row that is in the page but no longer in the sheet has been **cancelled** —
  delete it. Do not keep it because it looks intentional.
- Each schedule row is `["group", "time", "activity", "responsible", "notes"]`,
  one field per sheet column. The sheet names a Group only on the first row of
  each block and leaves the rest blank — carry it forward so every row in the
  page data names its group explicitly. Consecutive rows sharing a group become
  one collapsible section. A tab with no Group column (currently Canada) uses
  `""` throughout and renders as one flat timeline. The responsible name always shows on the timeline; only the
  notes go behind the expandable "Details" toggle. A trailing continuation row
  (a note with no time or activity) folds into the row above it. Leave a field
  as `""` when the sheet cell is blank — do not invent a responsible.
- A `;` in the sheet's Notes cell is a **line break**. Keep the semicolons in
  the data verbatim; the renderer splits on them, trims, and drops the symbol,
  so each fragment becomes its own line inside the Details toggle. Never
  hand-flatten a semicolon list into one comma-joined sentence.
- Times go `HHMM` → `HH:MM`; a blank time renders as `—`.
- Normalize prose to the page's house style: `and`/`&` between two people
  becomes `&` (`Lavinia & Daniel`, `Michelle & Mike`), sentence case for
  activities, fix the sheet's typos.
- The sheet's "Phone Nr" column sometimes holds status text (`?`, `Confirmed`)
  instead of a number — leave those blank rather than rendering them as phones.
- Bump `SYNCED_AT` in the page you touched; the footer shows it.
- `read_file_content` on the spreadsheet sometimes returns a **sampled** view —
  about 24 rows per sheet with long notes cut off at `...`. Never sync from
  that: it would read as rows deleted. When the response looks sampled, pull
  the whole workbook with `download_file_content` and
  `exportMimeType: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  then read every sheet with openpyxl.
- `equipment` is a list of `[heading, [items]]`, one entry per "Equipment ..."
  block in the sheet, each rendered as its own card. The sheet currently has
  two, Apéro and Reception.

Hero event details (date, venue, dress code) are **not** from the sheet — they
are static and sourced from withjoy.com/laviniadaniel.

## Design

Shared template across both event pages: deep maroon (`#4A161E`) hero, cream
text, "Herr Von Muellerhoff" for the names, Cormorant Garamond headings, Jost
body, IBM Plex Mono for times and phone numbers. Light and dark themes are both
defined — keep any new color as a token on `:root` with a dark counterpart.

## Languages (EN / DE)

`assets/i18n.js` is shared by all four pages. It picks a language from a saved
choice (`localStorage` key `wd-lang`), else from the device language — anything
starting with `de` gets German — and renders an EN/DE toggle into `.topbar`, or
floating in the corner on pages without one.

Each page declares `window.I18N_PAGE = { de: { ... } }` *before* loading
`i18n.js`. Keys are either:

- a dotted key (`hero.title`, `nav.team`) matched by a `data-i18n` attribute in
  the markup, or `data-i18n-attr="alt:some.key"` to translate an attribute; or
- the **English source string itself**, for anything rendered from the sheet
  (activities, notes, group names, team roles, equipment).

The English text stays in the HTML and in the schedule arrays; German lives only
in the dictionary. Anything without a translation falls back to English, so a
sheet sync that adds a row never blanks the page — it just shows that row in
English until a German string is added. After syncing new rows, add the matching
`de` entries.

Page scripts re-render through `WD_I18N.onChange(fn)`, which fires immediately
and again on every switch.

## Navigation

`assets/nav.js` loads after `i18n.js` on the pages with a `.topbar`. It moves
`.navlinks` and the language switcher into one `.nav-panel`, shown inline when
the links fit and behind a hamburger when they do not. The panel closes on a
link, a language pick, Escape, an outside click, and when the bar goes back to
inline. `index.html` has no top bar, so it keeps the floating switcher and
loads no `nav.js`.

**Collapsing is measured, never a breakpoint.** `updateCollapsed()` compares
`.navlinks` scrollWidth against clientWidth and sets `data-collapsed` on the
bar; the CSS keys off that attribute. It re-runs on resize, on orientation
change, after `document.fonts.ready`, and after a language switch, because
label widths change. A fixed breakpoint is what previously left menu items
scrolled out of sight in the horizontally scrolling bar at desktop widths —
with seven items the bar needs about 1200px, and it silently hid the last of
them. Adding a menu item must never be able to hide one.

**The menu lists only the day the reader is already in.** Once an event is
picked there is no link back to the hub — `index.html` is reached by entering
the domain. Pages set `window.WD_NAV_ITEMS`, a function returning
`[{href, label}]`, and `nav.js` renders it into `.navlinks` and re-renders it
on every language switch; a page without that global keeps its markup links.

**Every page in a section shows the same menu.** Each section's menu lives in
one file — `assets/day-switzerland.js` and `assets/day-canada.js` — loaded by
every page of that section, so they cannot differ; only the hrefs change,
picked by whether the timeline (`#tl-ch` / `#tl-ca`) is on the current page.
Each file's `GROUPS` array mirrors that tab's Group column — **update it when a
sync adds or renames a group**; the day page logs a console warning when the
two drift apart. Canada's is empty, so its menu points at `#schedule` as a
whole. Every page in a section also needs the menu labels in its own `de`
dictionary.

`nav.js` must not set `position` on `.topbar`. The bar is `position: sticky`,
which is both the containing block `.nav-panel` anchors to and the reason the
menu button stays reachable while scrolling; overriding it with `relative`
silently unsticks the whole bar.

Group anchors come from `groupId()`, which slugs the **English** group name, so
`#g-apero` survives a switch to German. Keep it that way — slugging the
translated name would break every menu link in German.

Each page's `de` dictionary needs a `"Menu"` entry — it is the toggle's
`aria-label` — plus entries for the labels `WD_NAV_ITEMS` builds.

## Timeline row layout

The "Details" disclosure rides on the activity line as a small pill, not on a
line of its own — a collapsed row is exactly as tall as a row with no notes.
Below 640px the pill's label is visually hidden (still read by screen readers)
so it cannot push the activity text onto a second line. Keep it that way: a
full-width toggle costs roughly 180px over the Switzerland timeline on a phone.

Note lines render as a bulleted `<ul class="t-notes">`, one `<li>` per
semicolon-separated fragment, with a gold `•` marker.

## The Canada setup page

`setup-canada.html` holds the Google Doc "Canada Setup Notes" (Drive id
`1drUKNLj_l04rsj4-kcBpZTt827AQwIYzewucJYiX5Eg`), which is crew-facing detail
rather than guest content — hence its own page. It renders from a `setup`
array of `[plan, [[task, [bullets], [pictures]]]]`, where a bullet is a string
or `[string, [sub-bullets]]` and a picture is `{src, alt}`; shared fragments
(place setting, head table, round table, food tables, and the photos) are
variables, so the inside and outside plans cannot drift apart where the doc
repeats itself. Where the doc repeats a block but varies one detail, the
variable takes that detail as an argument rather than being forked in two —
`HEAD_TABLE(cloth)` is called with `"oval"` inside and `"round"` outside.
`<b>` inside a bullet marks the quantities the doc bolds.

The doc's photos live in `assets/setup-ca-*.jpg`, attached to the task whose
bullets say "refer to the picture" — the rectangular table, the round table,
and two on the head table (draping, then the finished look). They are resized
to 1600px on the long edge and open full size when tapped, like the plan
pages. Their alt text is translated; re-export the doc as `application/zip` to
pull fresh copies, since the text export drops images entirely.

Its headings are translated; the step text is deliberately English-only, since
the Canada crew works in English and the i18n fallback shows it untranslated.
If that changes, add the bullet strings to the page's `de` dictionary keyed by
the English source, as everywhere else.

## The offline bundle

`wedding-offline.html` is the whole site as one file, for the venue where
there is no signal. `tools/build-offline.py` generates it — **re-run it after
every sheet sync, or the offline copy goes stale**:

```
python3 tools/build-offline.py
```

It needs no network. Each page keeps its own markup, styles and scripts and
is carried as a string; the router swaps one into the live document at a
time, so the sticky bar, hamburger, EN/DE switch and collapsible groups all
behave exactly as they do online.

**There is deliberately no iframe.** The bundle used to hold each page in a
`srcdoc` frame. WebKit blocks `srcdoc` frames inside a `file://` document, so
on an iPad the whole thing was a blank burgundy page — the host painted its
background and nothing ever appeared, while Android was fine. One document
has no origin to be refused, and works in restricted viewers like the iOS
Files preview too. Keep it that way.

Each page sits in its own inert `<script type="text/wd-page">` in `<head>`.
That keeps it out of `<body>`, which the router replaces wholesale, and means
the JS engine never parses a multi-megabyte string literal — the HTML parser
just stores text, and only the page being shown is ever made into a string.

Swapping a page in means: drop the previous page's `<style>` blocks, copy in
this page's, set `body.innerHTML`, then **re-create every `<script>`** —
scripts inserted through `innerHTML` never run. They execute in document
order, which is what `i18n.js` and `nav.js` need, and both initialise
immediately because `document.readyState` is no longer `"loading"`. The
host's own styles are the only ones with an `id`, so everything else in
`<head>` — including the styles `i18n.js` and `nav.js` append at runtime —
is safe to clear on each swap. Only one page is ever in the document, so
duplicate ids and class names across pages can never collide.

Inside a page block the HTML parser must never meet `</`, which would end the
block early. The build escapes the backslash first and then `</` → `<\/`, and
the router undoes both in one pass with `/\\([\s\S])/g`. Escaping only `</`
is **not** reversible: the 3D artifact's own JavaScript already contains
`<\/script>`, which would come back as `</script>` and corrupt it. The build
asserts the round-trip for every page, and refuses any page containing
`<!--`, which starts a comment state a later `<script` makes `</script>`
unable to close.

**The host template is a raw Python string, and must stay one.** It is
JavaScript travelling through Python, the HTML parser and then JS, and a
miscounted backslash has twice produced a file that looked perfect and died
on open: once a regex that ended early, once `\n` decoded to a real newline
inside a string literal, which left the boot script unparseable and the whole
page blank. Neither was visible anywhere but in a browser, so
`check_host_scripts()` now runs `node --check` over the host's two scripts at
build time.

The host is **ES5 only** (no arrow functions, `let`, or template strings) and
pairs `inset` with `top/right/bottom/left`, so an older iPad runs it. A tiny
boot script runs before everything else and, if the router has not started
within six seconds or anything throws, writes the error, the page-block count
and the user agent onto the page. A blank page tells the reader nothing and
tells us less.

The bundle's copies of the plans are re-encoded (long edge 1600, quality 72)
by `image_uri()`, which roughly halves them — the originals on the site are
untouched. It is decoded bitmap, not file size, that a phone has to hold: the
two 2000px plans were about 12 MB each in memory. Pillow is optional; without
it the build falls back to the originals.

Three things cannot survive being served from one file, and the router
handles them:

- Cross-page links (`canada.html#team`) are intercepted and routed. The route
  lives in the document's own hash — `#canada.html!team` — so Back works and
  a page can be linked.
- **Bare fragments too** (`#team`, `#g-apero`), because that same hash is the
  route: letting the browser handle `#team` would overwrite it. A jump to a
  freshly rendered page is instant, the way the real site lands on
  `canada.html#team`; a click within a page keeps the page's smooth scroll.
- A plan's `<a href="assets/....jpg">` becomes a lightbox, because a browser
  will not navigate to a `data:` URL. Only the `<img>` carries the bytes and
  the links find it by `data-wd-name`; inlining every reference would carry
  the larger plans three times over.
- The 3D plan's "open full screen" link calls the Fullscreen API.

Fonts live once in the host, in `<style id="wd-fonts">`.
`tools/fetch-fonts.py` regenerates `tools/offline-fonts.css` from Google
Fonts, latin subset only; run it only when a page starts using a new family
or weight.

**Nothing links to the bundle any more.** Both day menus used to offer it;
they offer that day's PDF instead, which asks nothing of the device. The file
and its build are kept because they work everywhere except, so far, an iPad —
but it is reachable only by typing the URL.

`leissigen.html` is in the bundle too — parking directions are the thing you
most want without a signal — and stays as unlinked there as it is on the site,
reachable only at `#leissigen.html`. Add a new page to `PAGES` in the build
script, or it is simply left out.

**The 3D string light view is the one thing that still needs a connection** —
the artifact pulls three.js from unpkg at runtime and that cannot be carried
in the file. It is still embedded the one way it can be, as a `srcdoc` frame,
so on an iPad opened from a file it stays blank either way. The cut list
beside it, and everything else, works offline everywhere.

## The PDFs

One PDF per event day per language — `wedding-switzerland.pdf`,
`wedding-switzerland-de.pdf`, `wedding-canada.pdf`, `wedding-canada-de.pdf`.
This is what the day menus offer under **Download PDF**, and what to print for
the day. A PDF asks nothing of the device, which the HTML bundle cannot say.

```
python3 tools/build-pdf.py                 # all four
python3 tools/build-pdf.py switzerland de  # just one
```

**After a sync, three things need rebuilding**: the page you edited, then
`build-offline.py`, then `build-pdf.py`.

Each day holds only its own pages — a Switzerland guest has no use for the
Canada setup plan. `leissigen.html` is in neither: it is unlinked on the site
by design, the URL being shared directly with the people who need it, and a
PDF has no way to carry a page without handing it to everyone who opens the
file. Say so before adding it.

The menu item's `href` follows the reader's language, because `nav.js`
re-runs `WD_NAV_ITEMS` on every switch; `nav.js` sets the `download`
attribute when an entry asks for it. The build sets `window.WD_OFFLINE`
before any page script runs and the day files drop the item when it is set,
so the offline bundle — one file, with no PDF beside it — does not offer a
link that cannot resolve. It needs a `de` entry on every page of both
sections, like any other menu label.

It prints each page separately with Chromium and joins them with pdfrw, so
every section starts on a fresh sheet. Before printing, each page gets a print
stylesheet and a script that opens every `<details>` — a collapsed timeline on
paper would hide the notes. The nav, the language switch, the "Details" pills
and the "tap to open full size" hints are hidden, since none of them mean
anything printed, and the 3D frame is replaced by a line pointing at the
website; its cut list prints normally.

Images are capped at `max-height: 200mm` so a tall plan fits beside its own
heading. Without that the Switzerland seating chart (926×1880) ran past the
bottom of the page and left the overflow on a blank one, and `.section-head`
needs `break-inside: avoid` or the eyebrow and the title land on separate
sheets. `-webkit-print-color-adjust: exact` keeps the maroon and gold.

German is produced by injecting the `wd-lang` choice into `localStorage`
before `i18n.js` loads, which is why it is set right after `<meta charset>`.

## The Canada string-light page

`assets/string-lights-canada.html` is a self-contained three.js artifact,
uploaded as-is and never edited: a bundler HTML that gunzips its own assets
into blob URLs and swaps in the real page. The `#floorplan` panel of
`indoor-canada.html` holds it in a `.stage-frame` iframe, plus a link to open
it full screen, which is the usable way to orbit it on a phone.

It pulls three.js from unpkg at runtime via an importmap inside the bundle, so
the 3D view needs a working connection. To replace it, drop in a new export
under the same filename — the panel does not care what the artifact contains.
Before publishing a new one, diff its first 381 lines against the copy in the
repo: that is the bundler loader, and if it matches byte for byte only the
payload changed, so the whole file does not need re-reading.

The export carries no legend, so the rigging numbers live on the page as the
`.cutlist` table under the 3D: four strings keyed by colour, with the swatch
hexes sampled from the companion cut list so they match the colours in the
model. Those four hexes are the one place in the site where a colour is not a
theme token — they are data, not decoration, and must not be restyled.

Canada's plans are grouped by **where you are**, not by what kind of drawing
they are: the menu has **Indoors** and **Outdoors**, and each page stacks two
`.panel` sections — `#floorplan` then `#seating`. Indoors the floor plan is the
3D string-light artifact in a `.stage-frame` iframe; outdoors it is the aerial
photo. Both seating panels now hold a real chart. Assets are named for what
they are, not for the page they sit on: `seating-indoor-canada.jpg`,
`seating-outdoor-canada.jpg`, `tables-canada.jpg`, `string-lights-canada.html`.
