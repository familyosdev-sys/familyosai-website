#!/usr/bin/env python3
"""Self-test for check-published-banned-claims.py — the guard's own guard.

The 2026-10-02 incident was a guard that was GREEN against a live defect, so
the properties worth pinning are the ones whose absence made it useless:

  1. ``.py`` is scanned. The zone served ``familyos_explainer.py`` carrying
     "The AI lives in your house." while ``--all`` exited 0. (AMS #2603, lizzie)
  2. media is checked on the WIRE, not only in the tree. ``scan_media`` read
     ``PUBLISH_ROOT.rglob``, found nothing (the outputs were deleted), printed
     "nothing to check (good)" and exited 0 while familyosai.com still served
     the banned-pixel video. (AMS #2603)
  3. the apex digest does not depend on the client's request shape. Cloudflare
     appends an analytics beacon without ``Accept: */*``; a guard that pins a
     digest must strip it or it is unreproducible. (AMS #2631, dana)

Run:  python3 scripts/test_check_published_banned_claims.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

FAILS: list[str] = []
CHECKS = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{' — ' + detail if detail else ''}")
        FAILS.append(label)


def load_guard():
    spec = importlib.util.spec_from_file_location(
        "claims_guard", HERE / "check-published-banned-claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # module has no import-time side effects
    return mod


def main() -> int:
    g = load_guard()

    print("1. suffixes and the matcher")
    check(".py is a scanned suffix", ".py" in g.SCAN_SUFFIXES,
          f"SCAN_SUFFIXES={sorted(g.SCAN_SUFFIXES)}")
    hits = g.scan_text("fixture.py", 'Text("The AI lives in your house.")')
    check("the served .py line is flagged", any("lives in your house" in h for h in hits),
          f"got {hits}")
    check("a clean line is not flagged",
          g.scan_text("fixture.py", 'Text("Your whole household.")') == [])
    # The banned list must not have been softened while fixing the guard.
    phrases = {p for p, _ in g.BANNED}
    for must in ("lives in your house", "on device", "on-device", "never touch a cloud"):
        check(f"banned list still contains {must!r}", must in phrases)

    print("2. media is checked on the wire, not only in the tree")
    real_files = list(g.PUBLISH_ROOT.rglob("*.mp4"))
    check("no mp4 remains in the working tree (the branch deleted them)",
          real_files == [], f"found {real_files}")
    wire = g.served_media_paths()
    check("served_media_paths() still returns the deleted mp4s from the residue registry",
          any(p.endswith("familyos-explainer.mp4") for p in wire),
          f"got {len(wire)} paths")
    check("served_media_paths() includes the self-renewing stale image",
          any(p.endswith("deploy/assets/brand/og-card.png") for p in wire))
    text_wire = g.served_text_paths()
    check("served_text_paths() includes the deleted .py",
          any(p.endswith("familyos_explainer.py") for p in text_wire))
    check("served_text_paths() excludes media suffixes",
          all(not p.endswith(".mp4") for p in text_wire))

    # A tree-only media scan must NOT be able to report a clean wire: prove that
    # scan_media actually fetches by feeding it a body that only the wire has.
    fetched: list[str] = []
    orig_fetch = g.fetch
    try:
        g.fetch = lambda path, *a, **k: (fetched.append(path), b"")[1]
        # ffmpeg on an empty blob fails, which lands as a NOT CHECKED problem —
        # the point is that the fetch happened at all.
        g.scan_media()
    finally:
        g.fetch = orig_fetch
    check("scan_media() fetches served media URLs (proves the wire leg is live)",
          any(p.endswith("familyos-explainer.mp4") for p in fetched),
          f"fetched {len(fetched)}: {fetched[:3]}")

    print("3. the apex body is compared beacon-stripped, by shape")
    beacon = ('<html><body>hi</body></html>\n'
              '<script defer src="https://static.cloudflareinsights.com/beacon.min.js"'
              ' data-cf-beacon=\'{"token":"x"}\'></script>\n')
    plain = "<html><body>hi</body></html>\n"
    check("the injected beacon is stripped",
          g.strip_beacon(beacon) == plain, repr(g.strip_beacon(beacon))[:80])
    check("beacon-stripped digests of both shapes agree",
          g.sha12(g.strip_beacon(beacon)) == g.sha12(g.strip_beacon(plain)))
    check("a real body change still differs after stripping",
          g.sha12(g.strip_beacon(beacon)) != g.sha12(g.strip_beacon(plain + "<p>new</p>")))

    print("4. the residue registry is honest about being unreadable")
    tmp = pathlib.Path(tempfile.mkdtemp())
    missing = tmp / "nope.json"
    orig = g.RESIDUE_FILE
    try:
        g.RESIDUE_FILE = missing
        check("a missing registry returns [] (checked, not silently claimed clean)",
              g.load_residue() == [])
        bad = tmp / "bad.json"
        bad.write_text('{"paths": "not a list"}')
        g.RESIDUE_FILE = bad
        check("a malformed registry returns [] rather than raising", g.load_residue() == [])
    finally:
        g.RESIDUE_FILE = orig

    print("5. an unreadable frame is NOT a clean frame, and callers cannot share a temp dir")
    # Regression pin for dana's AMS #2685 defect. _frames_and_ocr used to extract into a
    # hard-coded /tmp/banned-claims-frames and unlink its *.jpg at entry, so a second
    # caller (the self-test is one — it calls the real scan_media()) killed the first
    # caller's frames mid-flight; tesseract then failed by path, returned empty stdout,
    # and 9 banned frames scored as 0 with err=None. Both halves are pinned here:
    src = (HERE / "check-published-banned-claims.py").read_text()
    check("each call gets its own tempfile.mkdtemp (no shared /tmp path)",
          'tempfile.mkdtemp(prefix="banned-claims-")' in src)
    check("no code still extracts into the shared /tmp/banned-claims-frames",
          'tmp = pathlib.Path("/tmp/banned-claims-frames")' not in src)

    png = sorted(g.PUBLISH_ROOT.rglob("*.png"))
    if not png:
        check("a local media file exists to exercise the OCR path", False, "no PNG under deploy/")
    else:
        blob = png[0].read_bytes()
        tools = tuple(g.shutil.which(x) for x in ("ffmpeg", "ffprobe", "tesseract"))
        seen: list[str] = []
        real_run = g.subprocess.run

        def spy(cmd, *a, **k):
            if str(cmd[0]).endswith("ffmpeg") and "-i" in cmd:
                seen.append(str(pathlib.Path(cmd[cmd.index("-i") + 1]).parent))
            return real_run(cmd, *a, **k)

        g.subprocess.run = spy
        try:
            g._frames_and_ocr(blob, ".png", tools)
            g._frames_and_ocr(blob, ".png", tools)
        finally:
            g.subprocess.run = real_run
        check("two calls do not share a frame directory",
              len(seen) == 2 and seen[0] != seen[1], f"{seen}")

        def unlinker(cmd, *a, **k):
            if str(cmd[0]).endswith("tesseract"):
                pathlib.Path(cmd[1]).unlink(missing_ok=True)   # the exact mid-flight unlink
            return real_run(cmd, *a, **k)

        real_fetch = g.fetch
        g.fetch = lambda path, *a, **k: blob
        g.subprocess.run = unlinker
        try:
            problems, _transport = g.scan_media()
        finally:
            g.subprocess.run = real_run
            g.fetch = real_fetch
        check("an unreadable frame becomes a NOT CHECKED finding (guard exits 1), never clean",
              any("could not be read" in p for p in problems),
              f"{len(problems)} problems")
        check("no unreadable frame was scored clean",
              not any("frame(s), clean" in p for p in problems))

    print(f"\n{CHECKS - len(FAILS)}/{CHECKS} checks passed")
    if FAILS:
        print("FAILED: " + "; ".join(FAILS), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
