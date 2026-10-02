#!/usr/bin/env python3
"""Fail if this repo publishes a claim the product does not implement.

Three of these shipped in four days (see the header of ``tests/website-claims.test.ts``
in the familyos-app repo), and the 2026-10-02 recurrence was worse than the
earlier ones: the *page* was fixed and redeployed, and the retracted sentence
kept being served anyway — painted into a video that nobody re-read.

So the guard distinguishes *where* it looks, and you want the deepest mode in CI:

  * ``--tree`` (default) — text under the publish root. Catches the HTML/copy
    class. Cheap, no network.
  * ``--url`` — the live wire: the apex pages **and** every served text path
    this repo answers at, including the paths in ``scripts/served-residue.json``
    that the working tree no longer contains. This is the class that was wrong
    on 2026-10-02, and a tree-only guard was green through the whole incident.
  * ``--media`` — OCR rendered media. It reads the **served bytes** for every
    media URL it knows about (the publish root *plus* the residue registry)
    because the first version read only the tree, printed "no rendered media
    under deploy/ — nothing to check (good)", and exited 0 while
    familyosai.com still served the banned video. Needs ffmpeg, ffprobe and
    tesseract; when they are missing it says so and skips rather than
    reporting a false clean.
  * ``--all`` — ``--url`` and ``--media``.

Two facts a reader of this file should not have to rediscover:

  * The apex body is request-shape-dependent: Cloudflare appends a
    ``static.cloudflareinsights.com`` beacon after ``</body></html>`` unless the
    client sends ``Accept: */*``, so the same page is larger without the star
    Accept. The live check strips the beacon before comparing and asserts both
    shapes agree, instead of pinning a digest that only reproduces for one
    client shape.

    Pin the beacon-stripped DIGEST, never the byte count. The count is
    client- and RUM-dependent and has moved under a held digest: star-Accept
    13,225 B (dana #2609) -> 13,169 B (#2641), no-Accept 13,592 B -> 13,536 B.
    The stripped digests agreed throughout (fa31dd15248287ce on 2026-10-02),
    which is the fact worth pinning. (lizzie, AMS #2645; dana, AMS #2647.)
  * Every tree file is checked at ``/`` + its path from the repo root. That is
    a convention, not a fact about the wire, and it has already been wrong once:
    on 2026-10-02 the publish root moved from the REPO ROOT to ``deploy/``, so
    ``/deploy/index.html`` and ``/README.md`` stopped answering (404) while
    ``/`` and ``/privacy/`` stayed 200. The tree-derived paths then addressed
    nothing that was served, and the wire text leg silently covered only the
    apex pages. ``scan_url`` now prints how many paths 404-skipped and warns
    when every non-apex path did, so a green here cannot quietly mean less than
    it reads as. (dana, AMS #2703; verified live here.)

Exit codes: 0 clean, 1 banned claim found, 2 the guard could not run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLISH_ROOT = ROOT / "deploy"

# Paths the tree no longer contains but the zone may still serve. A tree scan
# cannot see these by construction; only a fetch can. See the file's own header.
RESIDUE_FILE = ROOT / "scripts" / "served-residue.json"

# --------------------------------------------------------------------------
# The banned list. Kept literal and case-insensitive on purpose — a regex here
# would invite clever near-misses. Mirrors familyos-app tests/website-claims.test.ts;
# when that list changes, change this one in the same breath.
# --------------------------------------------------------------------------
BANNED: list[tuple[str, str]] = [
    ("never leave your home network",
     "Photos reach the Cloudflare relay when the family has no in-house AI server. Reconciliation §2a.2."),
    ("never touch a cloud",
     "The relay IS a cloud endpoint and it is the default for the v3.0 target market."),
    ("photos never leave",
     "The original false promise. Reconciliation §1."),
    ("lives in your house",
     "Implies the AI is in-home. The primary AI server may sit off-premises, and the relay certainly does."),
    ("runs fully offline",
     "Chores/stars/safety run offline; conversation and photo checks do not. Say which."),
    ("names are stripped",
     "anonymizeText() is deleted. Nothing strips names today. Issue #166."),
    ("outbound traffic says",
     "The retracted 'outbound says Kid' claim. No name-redaction layer exists."),
    ("says 'kid'",
     "Same retracted claim without its lead-in."),
    ("stripped at home",
     "The EXIF/metadata strip is NOT shipped — room reference photos egress with GPS intact. Issue #313."),
    ("metadata is stripped",
     "Same as above. Issue #313."),
    ("separate choice from conversation",
     "There is no separate vision consent. One key, ai_fallback_consent, governs chat and photos together."),
    ("never used to train",
     "Relay retention behaviour is unverified — needs engineering verification and counsel. Reconciliation §2a gate."),
    ("never logged",
     "Same unverified relay claim. Reconciliation §2a gate."),
    ("nothing retained on our side",
     "Company-custody claim about the relay/chat path — unverified. Lex #2245."),
    ("we don't hold a copy of",
     "Same company-custody class, possessive form. Lex #2245."),
    ("on-device",
     "Nothing runs on-device. Inference is the family AI server or the Cloudflare relay."),
    ("on device",
     "Same claim without the hyphen — the spaced form reads identically to a family."),
]

# --------------------------------------------------------------------------
# Not every file is equally public, and pretending otherwise makes the guard
# either useless or unbearable:
#
#   * everything under deploy/ IS the website.  A banned claim there is a FAIL.
#   * everything else is repo furniture.  It should not be served at all -- but
#     while the Pages destination_dir is still the repo root it IS, so a hit
#     there is a WARN, printed loudly and separately.
#   * this file and the incident write-up quote the banned phrases on purpose.
#     They are skipped by name, and the skip is printed so it cannot hide.
# --------------------------------------------------------------------------
SKIP_PATHS = {
    "SOCIAL-MEDIA-RENDERS.md",                    # quotes the retracted captions on purpose
    "scripts/check-published-banned-claims.py",   # defines them
    "scripts/served-residue.json",                # records WHY each stale path is stale (quotes them)
    "scripts/test_check_published_banned_claims.py",  # pins the matcher; quotes it
}
PUBLISHED_PREFIX = "deploy/"
# .py is here because the zone SERVES the render scripts: familyos_explainer.py
# answered 200, 9,251 B and carried "The AI lives in your house." (L166) while
# the guard's own matcher would have flagged it — only this suffix gate kept
# ``--all`` green against a live defect. Caught by lizzie, AMS #2603.
SCAN_SUFFIXES = {".html", ".htm", ".md", ".txt", ".js", ".css", ".json", ".py"}
MEDIA_SUFFIXES = {".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg"}

APEX = "https://familyosai.com"
APEX_PATHS = ["/", "/privacy/", "/terms/"]

# Cloudflare serves the apex through bot protection and answers the default
# python-urllib User-Agent with 403. Sending a normal one is not evasion — the
# guard is asking for the same bytes a browser gets, which is the only input
# that matters here. Accept: */* is what keeps the beacon out of the body.
UA = "familyos-claims-guard/1.0 (+https://familyosai.com)"
ACCEPT = "*/*"

# The injected Cloudflare Web Analytics beacon. Stripped before the body is
# compared or scanned so one client shape cannot look like a content change.
BEACON_RE = re.compile(r"<script[^>]*cloudflareinsights[^>]*>.*?</script>\s*", re.S)


def strip_beacon(html: str) -> str:
    return BEACON_RE.sub("", html)


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def prose_files() -> list[pathlib.Path]:
    out = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if str(p.relative_to(ROOT)) in SKIP_PATHS:
            continue
        out.append(p)
    return out


def scan_text(label: str, text: str) -> list[str]:
    low = text.lower()
    return [f"{label}: banned claim {phrase!r} — {why}"
            for phrase, why in BANNED if phrase in low]


def scan_tree() -> tuple[list[str], list[str]]:
    """Returns (failures, warnings).

    ``failures`` are claims on the published surface; ``warnings`` are the same
    claim in a file that is only reachable through the mis-configured publish
    root. Both get printed; only failures set the exit code.
    """
    failures: list[str] = []
    warnings: list[str] = []
    files = prose_files()
    for f in files:
        rel = str(f.relative_to(ROOT))
        hits = scan_text(rel, f.read_text(errors="replace"))
        if rel.startswith(PUBLISHED_PREFIX):
            failures += hits
        else:
            warnings += hits
    published = [f for f in files if str(f.relative_to(ROOT)).startswith(PUBLISHED_PREFIX)]
    print(f"[tree] scanned {len(published)} published file(s) under deploy/ "
          f"and {len(files) - len(published)} repo file(s); "
          f"skipped by design: {', '.join(sorted(SKIP_PATHS))}")
    return failures, warnings


# --------------------------------------------------------------------------
# The wire. Everything below fetches real bytes.
# --------------------------------------------------------------------------

def _rel(p: pathlib.Path) -> str:
    """A path for humans to read. Never raises: the guard's diagnostics must not
    be able to crash it (a registry repointed outside the repo made
    ``relative_to`` raise, which the self-test caught)."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def load_residue() -> list[dict]:
    """Served paths the tree no longer has. Loud when the registry is broken:
    a silent [] would read as "nothing stale" and is the same class of lie this
    whole guard exists to prevent."""
    try:
        raw = RESIDUE_FILE.read_text()
    except FileNotFoundError:
        print(f"[wire] no residue registry at {_rel(RESIDUE_FILE)} — "
              "served-but-deleted paths are NOT checked this run")
        return []
    try:
        data = json.loads(raw)
        paths = data.get("paths") or []
        if not isinstance(paths, list):
            raise ValueError("'paths' must be a list")
        return [e for e in paths if isinstance(e, dict) and e.get("path")]
    except Exception as exc:
        print(f"[wire] residue registry {_rel(RESIDUE_FILE)} is unreadable ({exc}) — "
              "served-but-deleted paths are NOT checked this run", file=sys.stderr)
        return []


def served_text_paths() -> list[str]:
    paths = {"/" + p.relative_to(ROOT).as_posix() for p in prose_files()}
    for entry in load_residue():
        p = str(entry["path"])
        if pathlib.PurePosixPath(p).suffix.lower() in SCAN_SUFFIXES:
            paths.add(p)
    return sorted(paths)


def served_media_paths() -> list[str]:
    paths = {"/" + p.relative_to(ROOT).as_posix()
             for p in PUBLISH_ROOT.rglob("*")
             if p.is_file() and p.suffix.lower() in MEDIA_SUFFIXES}
    for entry in load_residue():
        p = str(entry["path"])
        if pathlib.PurePosixPath(p).suffix.lower() in MEDIA_SUFFIXES:
            paths.add(p)
    return sorted(paths)


def fetch(path: str, base: str = APEX, timeout: int = 25) -> bytes:
    req = urllib.request.Request(base + path, headers={"User-Agent": UA, "Accept": ACCEPT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def scan_url() -> tuple[list[str], list[str]]:
    """Returns (claim_findings, transport_failures).

    A network failure is NOT a claim finding and must not be reported as one —
    "the guard could not reach the site" and "the site says something false" are
    different incidents with different owners, and conflating them trains people
    to ignore the guard.
    """
    findings: list[str] = []
    failures: list[str] = []
    skipped: list[str] = []
    for path in APEX_PATHS + [p for p in served_text_paths() if p not in APEX_PATHS]:
        url = APEX + path
        try:
            body = fetch(path).decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                # Not served at all — nothing to read. Counted, not silent: the
                # tree-derived paths are built from the repo root, so when the
                # publish root is deploy/ every one of them 404s and the wire
                # leg's non-apex coverage is ZERO while --all still prints a
                # clean line. A caller must be able to see that.
                skipped.append(path)
                continue
            failures.append(f"{url}: HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{url}: could not fetch — {exc}")
            continue
        print(f"[live] {url}: {len(body)} bytes")
        findings += scan_text(url, strip_beacon(body))
    if skipped:
        print(f"[live] {len(skipped)} wire text path(s) answered 404 and were "
              f"skipped, not checked: {', '.join(skipped)}")
        if len(skipped) == len([p for p in served_text_paths() if p not in APEX_PATHS]):
            print("[live] WARNING — every non-apex text path 404'd, so this run's "
                  "wire text coverage is the three apex pages only. If the publish "
                  "root has moved (e.g. repo root -> deploy/), the tree-derived "
                  "paths no longer address what is served and this must be fixed "
                  "before a green here means what it reads as.")
    findings += shape_findings(failures)
    return findings, failures


def shape_findings(failures: list[str]) -> list[str]:
    """The pinned apex digest must be reproducible by any client.

    With ``Accept: */*`` Cloudflare leaves the body alone; without it, it
    injects the analytics beacon after ``</body></html>``. Stripping the beacon
    must make the two shapes identical — if it does not, a digest pinned in a
    ticket is unreproducible and the guard says so instead of pretending.
    """
    url = APEX + "/"
    try:
        star = fetch("/").decode("utf-8", "replace")
        none = fetch_no_accept("/").decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        failures.append(f"{url}: request-shape comparison could not run — {exc}")
        return []
    a, b = sha12(strip_beacon(star)), sha12(strip_beacon(none))
    # len() on the decoded str is CHARACTERS. Label it as such: the two
    # shapes differ because the beacon is stripped, and a bare "B" here
    # invited the reading that the byte count itself had moved.
    print(f"[live] {url}: shape */*={len(star)} chars/{a}  no-accept={len(none)} chars/{b}")
    if a != b:
        return [f"{url}: body differs by request shape beyond the analytics beacon "
                f"(beacon-stripped {a} vs {b}) — a pinned digest is not reproducible"]
    return []


def fetch_no_accept(path: str, timeout: int = 25) -> bytes:
    """Deliberately omit Accept — the shape a plain client (no star) gets."""
    req = urllib.request.Request(APEX + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _frames_and_ocr(data: bytes, suffix: str,
                    tools: tuple[str, str, str]) -> tuple[dict[str, list[str]], int, int, str | None]:
    """OCR one media blob. Returns ({phrase: [frames]}, nframes, unreadable, error).

    Every call gets its OWN temp directory (tempfile.mkdtemp). It used to share a
    hard-coded /tmp/banned-claims-frames and delete its *.jpg at entry, so two
    callers on one host — and the self-test is one, since it calls the real
    scan_media() — killed each other's frames mid-flight. A deleted file still
    lists in glob(), but tesseract opens it BY PATH, fails, returns empty stdout,
    and the frame scored as CLEAN. Measured: 9 banned frames -> 0, err=None.
    A guard whose whole reason to exist is "the tree scan was green while the
    wire served banned pixels" must not have a race that turns red into green.

    A frame whose OCR fails is now counted in `unreadable`, never in `hits`, and
    the caller turns a non-zero count into a NOT CHECKED finding. An unreadable
    frame is not a clean frame.
    """
    ffmpeg, _ffprobe, tesseract = tools
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="banned-claims-"))
    src = tmp / f"src{suffix or '.bin'}"
    src.write_bytes(data)
    if suffix.lower() in {".mp4", ".mov", ".webm"}:
        # one frame per second: captions in these videos sit for 2-5s, so
        # per-second sampling cannot step over one.
        cmd = [ffmpeg, "-v", "error", "-i", str(src), "-vf", "fps=1,scale=1100:-1",
               "-q:v", "4", str(tmp / "f_%04d.jpg")]
    else:
        # stills need -frames:v 1 / -update 1 or ffmpeg refuses the single
        # fixed output name ("Cannot write more than one file with the same
        # name") and the frame is silently never produced.
        cmd = [ffmpeg, "-v", "error", "-i", str(src), "-frames:v", "1", "-update", "1",
               "-vf", "scale=1100:-1", "-q:v", "4", str(tmp / "f_0001.jpg")]
    r = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return {}, 0, 0, f"ffmpeg failed ({r.returncode}): {r.stderr.strip()[:160]}"
    frames = sorted(tmp.glob("*.jpg"))
    if not frames:
        shutil.rmtree(tmp, ignore_errors=True)
        return {}, 0, 0, "0 frames extracted"
    hits: dict[str, list[str]] = {}
    unreadable = 0
    for fr in frames:
        rr = subprocess.run([tesseract, str(fr), "-", "--psm", "6"],
                            capture_output=True, text=True)
        if rr.returncode != 0:
            # Unlinked mid-flight, or tesseract genuinely failed. Either way the
            # frame was NOT read, so it cannot score as clean.
            unreadable += 1
            continue
        low = " ".join(rr.stdout.split()).lower()
        for phrase, _why in BANNED:
            if phrase in low:
                hits.setdefault(phrase, []).append(fr.name)
    shutil.rmtree(tmp, ignore_errors=True)
    return hits, len(frames), unreadable, None


def scan_media() -> tuple[list[str], list[str]]:
    """OCR rendered media, locally and on the wire. Returns (problems, transport).

    It is deliberately noisy about what it could not check: a guard that
    silently skips media reads as green and is worse than no guard.
    """
    ffmpeg, ffprobe, tesseract = (shutil.which(x) for x in ("ffmpeg", "ffprobe", "tesseract"))
    if not all((ffmpeg, ffprobe, tesseract)):
        print("[media] SKIPPED — need ffmpeg, ffprobe and tesseract on PATH; "
              "this guard did NOT check rendered media.")
        return [], []
    tools = (ffmpeg, ffprobe, tesseract)
    problems: list[str] = []
    transport: list[str] = []

    def report(label: str, hits: dict[str, list[str]], nframes: int, unreadable: int,
               note: str) -> None:
        for phrase, where in hits.items():
            problems.append(f"{label}: on-screen caption {phrase!r} in {len(where)} frame(s) "
                            f"({', '.join(where[:5])}) — {dict(BANNED)[phrase]}")
        # An unreadable frame is a NOT CHECKED finding, not a clean one: if OCR
        # could not read a frame, the phrase could be sitting in it unseen.
        if unreadable:
            problems.append(f"{label}: NOT CHECKED — {unreadable} of {nframes} frame(s) could not "
                            f"be read (tesseract failed); those frames were NOT cleared")
        tail = "clean" if not hits else "BANNED TEXT"
        if unreadable:
            tail += f", {unreadable} frame(s) UNREADABLE — not cleared"
        print(f"[media] {label}: {nframes} frame(s), {tail}{note}")

    # Leg 1 — the working tree. Catches a bad render BEFORE it is published.
    local = [p for p in PUBLISH_ROOT.rglob("*")
             if p.is_file() and p.suffix.lower() in MEDIA_SUFFIXES]
    if not local:
        print("[media] no rendered media in the working tree (expected on this branch: "
              "the outputs were deleted) — so the WIRE below is the whole check")
    for p in local:
        rel = str(p.relative_to(ROOT))
        data = p.read_bytes()
        hits, nframes, unreadable, err = _frames_and_ocr(data, p.suffix, tools)
        if err:
            problems.append(f"{rel}: NOT CHECKED — {err}")
            print(f"[media] {rel}: NOT CHECKED — {err}")
            continue
        report(rel, hits, nframes, unreadable, "")

    # Leg 2 — the wire. Catches a stale zone entry the tree cannot see at all.
    for path in served_media_paths():
        url = APEX + path
        try:
            data = fetch(path)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                print(f"[media] {url}: 404 — not served")
                continue
            transport.append(f"{url}: HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            transport.append(f"{url}: could not fetch — {exc}")
            continue
        hits, nframes, unreadable, err = _frames_and_ocr(data, pathlib.PurePosixPath(path).suffix, tools)
        if err:
            problems.append(f"{url}: NOT CHECKED — {err}")
            print(f"[media] {url}: NOT CHECKED — {err}")
            continue
        report(url, hits, nframes, unreadable, f" — {len(data)} bytes served")

    if transport:
        print("\n[media] media URLs that could not be fetched (treat as unrun, not clean):")
        for t in transport:
            print(f"  ? {t}")
    return problems, transport


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", action="store_true", help="also fetch and scan the live wire (apex + served text)")
    ap.add_argument("--media", action="store_true", help="also OCR rendered media, tree and wire (needs ffmpeg+tesseract)")
    ap.add_argument("--all", action="store_true", help="--url and --media together")
    # The module docstring has always advertised ``--tree (default)``, but
    # argparse defined only --url/--media/--all, so the documented flag exited 2
    # with "unrecognized arguments". Bare invocation did scan the tree, so only
    # the doc/CLI pairing was wrong (dana, AMS #2685). Accept it explicitly.
    ap.add_argument("--tree", action="store_true",
                    help="scan the working tree only — the default; accepted so the flag the "
                         "docstring advertises actually exists")
    args = ap.parse_args()

    problems, warnings = scan_tree()
    transport: list[str] = []
    if args.url or args.all:
        found, transport = scan_url()
        problems += found
    if args.media or args.all:
        media_problems, media_transport = scan_media()
        problems += media_problems
        transport += media_transport

    if warnings:
        print(f"\nWARN — {len(warnings)} banned-claim finding(s) OUTSIDE the publish root.\n"
              "Not served once destination_dir=deploy/, but the Pages project currently\n"
              "publishes the repo root, so these are live at familyosai.com today:\n")
        for w in warnings:
            print(f"  ! {w}")

    if transport:
        print(f"\nCOULD NOT RUN — {len(transport)} endpoint(s) unreachable:\n", file=sys.stderr)
        for t in transport:
            print(f"  ? {t}", file=sys.stderr)
        print("\nThis is a transport failure, not a claim finding. Treat the live check\n"
              "as UNRUN — do not read it as clean.", file=sys.stderr)
        return 2

    if problems:
        print(f"\nFAIL — {len(problems)} banned-claim finding(s):\n", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\nIf a claim has become TRUE, ship the proof and remove it from BANNED "
              "in this file AND in familyos-app tests/website-claims.test.ts.\n"
              "If the claim ships in bytes the tree no longer has, the zone still has a\n"
              "stale copy — purge it (see scripts/served-residue.json), then re-run.", file=sys.stderr)
        return 1
    print("\nOK — no banned claims found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
