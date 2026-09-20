# Lavinia & Daniel — wedding site

Static site, no build step. GitHub Pages deploys from `main`; custom domain
`wedding.germann-mail.com` via the `CNAME` file.

- `index.html` — hub linking to both events
- `canada.html` — Celebration Canada
- `switzerland.html` — Switzerland (ceremony, Apéro, reception)
- `seating-switzerland.html` + `assets/seating-switzerland.jpg` — static seating chart

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
