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

    print("3b. the cf_email rewrite is normalized out (dana AMS #2724/#2725)")
    # Cloudflare rewrites /cdn-cgi/l/email-protection#<hex> with a per-request XOR
    # key, so /privacy/ and /terms/ have no reproducible raw digest even at fixed
    # length (measured: three plain GETs, three sha16). Normalizing the payload
    # makes the digest mean content again. The apex carries zero spans, so this
    # must be a no-op there or the pinned fa31dd15248287ce moves.
    cfa = ('<a href="/cdn-cgi/l/email-protection#aabbcc">x</a>'
           "<span data-cfemail=\"aabbcc\">x</span>")
    cfb = ('<a href="/cdn-cgi/l/email-protection#ddeeff">x</a>'
           "<span data-cfemail=\"ddeeff\">x</span>")
    check("cf_email payloads normalize to one digest",
          g.sha12(g.normalize_request_scoped(cfa)) == g.sha12(g.normalize_request_scoped(cfb)),
          f"{g.sha12(g.normalize_request_scoped(cfa))} vs {g.sha12(g.normalize_request_scoped(cfb))}")
    check("normalizing does not collapse genuinely different content",
          g.sha12(g.normalize_request_scoped(cfa))
          != g.sha12(g.normalize_request_scoped(cfa + "<p>more</p>")))
    apex = '<html><body><p>no obfuscation spans here</p></body></html>\n'
    check("the apex body is unchanged by cf_email normalization (no-op)",
          g.normalize_request_scoped(apex) == apex)

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

    print("6. the honest-404 body is pinned by a beacon-stripped digest (lizzie AMS #2857)")
    # The 404 page is the same bytes at 200 (/404.html) and at any unknown path
    # (404) once the beacon is stripped, so ONE fixture pins both shapes. The pin
    # must be a DIGEST, never a count: the apex zone answers 702 B under
    # ``Accept: */*`` and 1,069 B under any other shape (the 366 B beacon + one
    # trailing newline), while the origin stays 702 B - the count is not a pin.
    check("NOT_FOUND_STRIPPED_SHA12 is a true sha256_12 (exactly 12 hex chars)",
          isinstance(g.NOT_FOUND_STRIPPED_SHA12, str)
          and len(g.NOT_FOUND_STRIPPED_SHA12) == 12
          and all(c in "0123456789abcdef" for c in g.NOT_FOUND_STRIPPED_SHA12),
          repr(g.NOT_FOUND_STRIPPED_SHA12))
    # sha12() is a misnomer: it returns 16 hex chars. Carrying lizzie's 12-char
    # value as if it were the whole return value gave a false red on the live
    # wire (2026-10-02: "digest 83972470b5674ad9 != pinned 83972470b567"). The
    # pin is a PREFIX compare; the units are asserted here so a reader cannot
    # re-make the mistake.
    check("sha12() really returns 16 hex chars (name != units)",
          len(g.sha12("x")) == 16, f"{len(g.sha12('x'))}")
    check("NOT_FOUND_STRIPPED_PREFIX matches the carried 12-char units",
          g.NOT_FOUND_STRIPPED_PREFIX == 12)
    check("the dead path is an absolute path, distinct from the canonical 404 path",
          g.NOT_FOUND_DEAD_PATH.startswith("/")
          and g.NOT_FOUND_DEAD_PATH != g.NOT_FOUND_PATH)
    check("the origin host is pinned (the layer a purge exposes)",
          g.ORIGIN.startswith("https://") and g.ORIGIN != g.APEX, g.ORIGIN)

    page404 = ('<!doctype html><html lang="en"><body><h1>404</h1>'
               '<p>That page does not exist.</p></body></html>')
    beacon = ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js"'
              ' data-cf-beacon=\'{"token":"x"}\'></script>\n')
    check("404 page + injected beacon strips to the bare page's digest",
          g.sha12(g.strip_beacon(page404 + beacon)) == g.sha12(g.strip_beacon(page404)))

    fix12 = g.sha12(g.strip_beacon(page404))[:12]
    orig_pin, orig_status = g.NOT_FOUND_STRIPPED_SHA12, g._fetch_status

    # _fetch_status must return the body of a 404 rather than raise: the contract
    # is *about* a 404 body, so a raiser cannot read it. Also prove all THREE
    # readings are taken - zone dead path, zone /404.html, origin dead path. A
    # pin of one layer passes while the layer a purge exposes serves something
    # else, which is the conflation the residue registry's layer discriminator
    # exists to avoid.
    STATUS = {(g.APEX, g.NOT_FOUND_DEAD_PATH): 404,
              (g.APEX, g.NOT_FOUND_PATH): 200,
              (g.ORIGIN, g.NOT_FOUND_DEAD_PATH): 404}
    seen: list[tuple[str, str]] = []

    def spy(path, base=None, **k):
        key = (base or g.APEX, path)
        seen.append(key)
        return STATUS.get(key, 200), page404.encode()

    g.NOT_FOUND_STRIPPED_SHA12 = fix12
    g._fetch_status = spy
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
    check("the 404 pin reads the zone dead path, the zone /404.html AND the origin",
          (g.APEX, g.NOT_FOUND_DEAD_PATH) in seen
          and (g.APEX, g.NOT_FOUND_PATH) in seen
          and (g.ORIGIN, g.NOT_FOUND_DEAD_PATH) in seen, f"{seen}")
    check("a matching body + matching statuses yields no 404 failure", fails == [], f"{fails}")

    # A pin that cannot go red is not a pin. Change the body and it must fall.
    g._fetch_status = lambda path, base=None, **k: (404, (page404 + "<p>changed</p>").encode())
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
    check("a changed 404 body appends a failure",
          any("404 body digest" in f for f in fails), f"{fails}")

    # The units bug: the same bytes must NOT fail against the 12-char pin (i.e.
    # the compare is a prefix, not whole-return-value equality).
    def all_ok(path, base=None, **k):
        return STATUS.get((base or g.APEX, path), 200), page404.encode()

    g._fetch_status = all_ok
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
    check("a 16-char digest matches the 12-char pin by prefix (units bug pinned)",
          fails == [], f"{fails}")

    # The status is part of the contract. A soft-200 catch-all (dead path
    # answering 200) or a hard-500 must fail even when the bytes are identical:
    # the guard's whole "404 = not served" skip logic depends on it.
    g._fetch_status = lambda path, base=None, **k: (200, page404.encode())
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
    check("a dead path answering 200 (soft-200 catch-all) appends a failure",
          any("expected 404" in f for f in fails), f"{fails}")

    # A cf_email span carries a per-request XOR key, so the body has NO
    # reproducible digest even at fixed length. The pin must refuse to read it
    # rather than pin a value that moves every request (the 403-challenge class
    # already documented in the guard header).
    g._fetch_status = lambda path, base=None, **k: (
        404, (page404 + '<a href="/cdn-cgi/l/email-protection#aabbcc">x</a>').encode())
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
    check("a 404 body carrying a cf_email span is refused, not pinned",
          any("cf_email span" in f for f in fails), f"{fails}")

    # Zone and origin must serve the SAME 404 page. If they diverge, a purge
    # changes what a dead path answers and the pin is a pin of one layer only.
    def by_host(path, base=None, **k):
        body = page404 if (base or g.APEX) == g.APEX else page404 + "<p>origin</p>"
        return STATUS.get((base or g.APEX, path), 200), body.encode()

    g._fetch_status = by_host
    try:
        fails = g.not_found_findings()
    finally:
        g._fetch_status = orig_status
        g.NOT_FOUND_STRIPPED_SHA12 = orig_pin
    check("a 404 page that differs by layer appends a failure",
          any("layer-dependent" in f for f in fails), f"{fails}")

    # The contract channel must be separate from transport: a broken 404 is a
    # FINDING (exit 1), and scan_url must expose it as a third channel so main()
    # can report it as one instead of "endpoint(s) unreachable" (exit 2).
    import inspect
    sig = inspect.getsource(g.scan_url)
    check("scan_url returns a third (contract) channel",
          "claim_findings, transport_failures, contract_failures" in sig)
    check("main() reports the 404 contract separately from transport",
          "honest-404 contract failure(s)" in inspect.getsource(g.main))

    print(f"\n{CHECKS - len(FAILS)}/{CHECKS} checks passed")
    if FAILS:
        print("FAILED: " + "; ".join(FAILS), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
