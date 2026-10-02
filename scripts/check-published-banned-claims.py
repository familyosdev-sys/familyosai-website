#!/usr/bin/env python3
"""Fail if this repo publishes a claim the product does not implement.

Three of these shipped in four days (see the header of ``tests/website-claims.test.ts``
in the familyos-app repo), and the 2026-10-02 recurrence was worse than the
earlier ones: the *page* was fixed and redeployed, and the retracted sentence
kept being served anyway — painted into a video that nobody re-read.

So this guard has two modes, and you want both in CI:

  * ``--tree`` (default) — text under the publish root. Catches the HTML/copy
    class. Cheap, no network.
  * ``--url`` — the *live apex*. Catches the other class: the bytes a family
    actually receives, which is the only thing that was ever wrong on
    2026-10-02. A guard that only reads the working tree would have been green
    through the entire incident.

``--media`` additionally OCRs any rendered media it can find in the publish root
and reports captions carrying a banned fragment. It is opt-in because it needs
``ffmpeg`` and ``tesseract``; when they are missing it says so and skips rather
than reporting a false clean.

Exit codes: 0 clean, 1 banned claim found, 2 the guard could not run.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLISH_ROOT = ROOT / "deploy"

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
}
PUBLISHED_PREFIX = "deploy/"
SCAN_SUFFIXES = {".html", ".htm", ".md", ".txt", ".js", ".css", ".json"}

APEX = "https://familyosai.com"
APEX_PATHS = ["/", "/privacy/", "/terms/"]


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


# Cloudflare serves the apex through bot protection and answers the default
# python-urllib User-Agent with 403. Sending a normal one is not evasion — the
# guard is asking for the same bytes a browser gets, which is the only input
# that matters here.
UA = "familyos-claims-guard/1.0 (+https://familyosai.com)"


def scan_url() -> tuple[list[str], list[str]]:
    """Returns (claim_findings, transport_failures).

    A network failure is NOT a claim finding and must not be reported as one —
    "the guard could not reach the site" and "the site says something false" are
    different incidents with different owners, and conflating them trains people
    to ignore the guard.
    """
    findings: list[str] = []
    failures: list[str] = []
    for path in APEX_PATHS:
        url = APEX + path
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{url}: could not fetch — {exc}")
            continue
        print(f"[live] {url}: {r.status}, {len(body)} bytes")
        findings += scan_text(url, body)
    return findings, failures


def scan_media() -> list[str]:
    """OCR rendered media in the publish root and report banned captions.

    This is the mode that would have caught 2026-10-02. It is deliberately
    noisy about what it could not check: a guard that silently skips media
    reads as green and is worse than no guard.
    """
    ffmpeg, ffprobe, tesseract = (shutil.which(x) for x in ("ffmpeg", "ffprobe", "tesseract"))
    if not all((ffmpeg, ffprobe, tesseract)):
        print("[media] SKIPPED — need ffmpeg, ffprobe and tesseract on PATH; "
              "this guard did NOT check rendered media.")
        return []
    media = [p for p in PUBLISH_ROOT.rglob("*")
             if p.suffix.lower() in {".mp4", ".mov", ".webm", ".png", ".jpg"}]
    if not media:
        print("[media] no rendered media under deploy/ — nothing to check (good)")
        return []
    problems: list[str] = []
    failures: list[str] = []
    tmp = pathlib.Path("/tmp/banned-claims-frames")
    tmp.mkdir(parents=True, exist_ok=True)
    for p in media:
        for old in tmp.glob("*.jpg"):
            old.unlink()
        if p.suffix.lower() in {".mp4", ".mov", ".webm"}:
            # one frame per second: captions in these videos sit for 2-5s, so
            # per-second sampling cannot step over one.
            cmd = [ffmpeg, "-v", "error", "-i", str(p), "-vf", "fps=1,scale=1100:-1",
                   "-q:v", "4", str(tmp / "f_%04d.jpg")]
        else:
            # stills need -frames:v 1 / -update 1 or ffmpeg refuses the single
            # fixed output name ("Cannot write more than one file with the same
            # name") and the frame is silently never produced.
            cmd = [ffmpeg, "-v", "error", "-i", str(p), "-frames:v", "1", "-update", "1",
                   "-vf", "scale=1100:-1", "-q:v", "4", str(tmp / "f_0001.jpg")]
        r = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[media] {p.relative_to(ROOT)}: ffmpeg failed ({r.returncode}) — "
                  "NOT CHECKED")
            failures.append(f"{p.relative_to(ROOT)}: ffmpeg could not extract frames; "
                            "this media was not checked")
            continue
        frames = sorted(tmp.glob("*.jpg"))
        hits: dict[str, list[str]] = {}
        for fr in frames:
            r = subprocess.run([tesseract, str(fr), "-", "--psm", "6"],
                               capture_output=True, text=True)
            low = " ".join(r.stdout.split()).lower()
            for phrase, _why in BANNED:
                if phrase in low:
                    hits.setdefault(phrase, []).append(fr.name)
        rel = p.relative_to(ROOT)
        if hits:
            for phrase, where in hits.items():
                why = dict(BANNED)[phrase]
                problems.append(
                    f"{rel}: on-screen caption {phrase!r} in {len(where)} frame(s) "
                    f"({', '.join(where[:5])}) — {why}")
        if not frames:
            failures.append(f"{rel}: 0 frames extracted — this media was NOT checked")
            print(f"[media] {rel}: 0 frames extracted — NOT CHECKED")
        else:
            print(f"[media] {rel}: {len(frames)} frame(s), "
                  f"{'BANNED TEXT' if hits else 'clean'}")
    if failures:
        print("\n[media] media that could not be checked (treat as unrun, not clean):")
        for f in failures:
            print(f"  ? {f}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", action="store_true", help="also fetch and scan the live apex")
    ap.add_argument("--media", action="store_true", help="also OCR rendered media (needs ffmpeg+tesseract)")
    ap.add_argument("--all", action="store_true", help="--url and --media together")
    args = ap.parse_args()

    problems, warnings = scan_tree()
    transport: list[str] = []
    if args.url or args.all:
        found, transport = scan_url()
        problems += found
    if args.media or args.all:
        problems += scan_media()

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
              "in this file AND in familyos-app tests/website-claims.test.ts.",
              file=sys.stderr)
        return 1
    print("\nOK — no banned claims found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
