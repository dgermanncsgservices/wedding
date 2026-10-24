# Lavinia & Daniel — wedding site (offline)

The site was taken offline on 2026-10-24 at Daniel's request, after both
weddings. `main` now serves only a thank-you page (`index.html`, with
`404.html` as a copy so every old URL lands on it); `CNAME` keeps the custom
domain `wedding.germann-mail.com` attached to GitHub Pages.

The full site, with its build tools, PDFs and the original CLAUDE.md, is
intact on the `site-archive` branch and in the history of `main`.

To bring it back, restore main from the archive:

    git checkout main
    git checkout site-archive -- .
    git rm -q 404.html
    git commit -m "Bring the wedding site back online"
    git push origin main
