# Lavinia & Daniel — wedding site

Static site, no build step. GitHub Pages deploys from `main`; custom domain
`wedding.germann-mail.com` via the `CNAME` file.

- `index.html` — hub linking to both events
- `canada.html` — Celebration Canada
- `switzerland.html` — Switzerland (ceremony, Apéro, reception)
- `seating-switzerland.html` + `assets/seating-switzerland.jpg` — static seating chart
- `apero-switzerland.html` + `assets/apero-switzerland.jpg` — static Apéro site plan
- `tables-canada.html` + `assets/tables-canada.jpg` — Canada outdoor table layout
- `setup-canada.html` — the Canada setup plan for the crew

The three static plan pages share one template: top bar, centred
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
array of `[plan, [[task, [bullets]]]]`, where a bullet is a string or
`[string, [sub-bullets]]`; shared fragments (place setting, head table, round
table, food tables) are variables, so the inside and outside plans cannot drift
apart where the doc repeats itself. `<b>` inside a bullet marks the quantities
the doc bolds.

Its headings are translated; the step text is deliberately English-only, since
the Canada crew works in English and the i18n fallback shows it untranslated.
If that changes, add the bullet strings to the page's `de` dictionary keyed by
the English source, as everywhere else.
