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
- Each schedule row is `["time", "activity", "responsible · notes"]`. The sheet's
  Responsible and Notes columns are joined with ` · ` into that third field, and
  a trailing continuation row (a note with no time or activity) folds into the
  row above it.
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
