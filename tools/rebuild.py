#!/usr/bin/env python3
"""Rebuild everything derived from the pages: the offline bundle and the PDFs.

The pages hold the data, but guests download the artifacts. A sync that edits
a page and stops has shipped a stale PDF, so this runs the lot in one go.

    python3 tools/rebuild.py            # rebuild everything
    python3 tools/rebuild.py --check    # only say what is out of date

Run it after every sheet sync.
"""
import pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

# Every artifact, and the sources it is built from. Used by --check to say
# what has gone stale, and listed here so a new page cannot be forgotten.
SOURCES = sorted(ROOT.glob("*.html")) + sorted((ROOT / "assets").glob("*.js"))
ARTIFACTS = [
    ROOT / "wedding-offline.html",
    ROOT / "wedding-switzerland.pdf", ROOT / "wedding-switzerland-de.pdf",
    ROOT / "wedding-canada.pdf", ROOT / "wedding-canada-de.pdf",
]

BUILDS = [
    ["python3", str(TOOLS / "build-offline.py")],
    ["python3", str(TOOLS / "build-pdf.py")],
]


def newest_source() -> tuple:
    newest = max((p for p in SOURCES if p.name not in {a.name for a in ARTIFACTS}),
                 key=lambda p: p.stat().st_mtime)
    return newest, newest.stat().st_mtime


def check() -> int:
    src, src_time = newest_source()
    stale = []
    for a in ARTIFACTS:
        if not a.exists():
            stale.append((a, "missing"))
        elif a.stat().st_mtime < src_time:
            stale.append((a, "older than %s" % src.name))
    if not stale:
        print("up to date — all %d artifacts are newer than %s" % (len(ARTIFACTS), src.name))
        return 0
    print("stale, rebuild with: python3 tools/rebuild.py")
    for a, why in stale:
        print("  %-28s %s" % (a.name, why))
    return 1


def main() -> None:
    if "--check" in sys.argv[1:]:
        sys.exit(check())

    started = time.time()
    for cmd in BUILDS:
        print("$ %s" % " ".join(pathlib.Path(c).name if c.endswith(".py") else c for c in cmd))
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            sys.exit("%s failed — nothing further was built" % pathlib.Path(cmd[-1]).name)

    print("\nrebuilt in %.0fs:" % (time.time() - started))
    for a in ARTIFACTS:
        print("  %-28s %6.1f MB" % (a.name, a.stat().st_size / 1048576)
              if a.exists() else "  %-28s MISSING" % a.name)
    sys.exit(check())


if __name__ == "__main__":
    main()
