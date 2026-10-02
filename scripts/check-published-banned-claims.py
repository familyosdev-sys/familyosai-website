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

    SCOPE OF ``--url`` AND ``--media``, written down because it has already
    hidden a live banned copy: the wire legs probe the APEX and the Pages-origin
    pair only. They do NOT enumerate unrelated deployment hostnames, and any
    other alias on the same Pages project answers every path from its own
    deployment - so it can serve banned-claim HTML while this guard reads
    green. Measured 2026-10-02 (dana, AMS #2958): two live aliases,
    30c37e93.familyosai-cma.pages.dev (body sha256 6deb8617...) and
    664dd4da.familyosai-cma.pages.dev (e0f6297e...), each served the old
    landing at /, /robots.txt, /privacy/, /terms/ and /404.html AND served the
    banned explainer at the BARE path /assets/social/shorts/familyos_explainer.py
    (200 / 9,251 B / 339f229565545cf7 / "lives in your house"). Those aliases
    are not merely serving a "retracted landing": that retired landing IS
    banned-claim-serving. Running THIS guard's own BANNED list over the alias
    root bytes gives 5 occurrences from 3 distinct phrases - "lives in your
    house" x2, "runs fully offline" x2, "on-device" x1 - the same severity
    class as the zone's /deploy/ explainer (lizzie, AMS #3013; re-measured
    here 2026-10-02 against both aliases). Neither alias is
    in served-residue.json. Deliberately NOT added as registry entries: an
    unrelated-host allowlist would just hide the next alias the same way. A
    green ``--url`` means the apex and the origin are clean, nothing more.

    THE BARE PATH IS UNCHECKED TOO — one level down and for the same structural
    reason. ``scan_url`` fetches APEX_PATHS + ``served_text_paths()``, and the
    residue registry knows only the ``/deploy/assets/...`` spelling, so the
    aliases' bare ``/assets/social/shorts/familyos_explainer.py`` is never
    fetched even though the file's own BANNED matcher fires on the bytes it
    serves (200 / 9,251 B / 339f229565545cf7 — the same banned copy). A green
    ``--url`` therefore cannot be read as "the explainer is gone everywhere"; it
    means the apex, the origin and the registry's own ``/deploy/`` paths are
    clean, nothing more. (dana AMS #3119; re-measured here 2026-10-02: bare path
    200 / 9,251 B on both aliases, apex 404 / 702 B.)

Four facts a reader of this file should not have to rediscover:

  * The apex body is request-shape-dependent, and the discriminator is the
    case-SENSITIVE literal substring ``text/html`` in the raw ``Accept`` header
    — NOT a media-type token and NOT the star: Cloudflare injects a
    ``static.cloudflareinsights.com`` beacon when the raw ``Accept`` header
    carries that substring, or when the header is absent — NO HEADER AT ALL; a
    present-but-empty ``Accept:`` gets NO beacon (see the enumeration below). It
    injects nothing otherwise. The ``text/html2`` / ``text/htmlish`` /
    ``text/htmlX`` / ``xtext/html`` / ``a text/html b`` shapes match NO media
    type and still get the beacon (dana AMS #3087). Injection POSITION is
    surface-dependent: on the apex ROOT ``/`` the beacon sits after the closing
    ``</body></html>``, on the 404 path it sits before it (lex AMS #3079; dana
    #3119). The offset-free falsifier for the direction, which is why the scoped
    sentence is checkable rather than accidental: strip the beacon and ask
    whether the no-beacon body is a PREFIX of the beacon body. TRUE = pure
    append after the close tag (apex ``/``: 13,225 == beacon[:13,225]); FALSE =
    insert before it (404: 702 != beacon[:702]). The close tag moves on an
    insert, so a prefix can only hold for an append.
    NOT a star-vs-non-star rule — ``TEXT/HTML`` is non-star and gets NO beacon.
    Measured 2026-10-02 from RecRoomRig, 28 shapes x 3 reps, every reading
    stable (evidence: profiles/codey/cache/scratch/sweep_final.{py,out}). On the
    apex ROOT ``/`` (13,592 B / sha16 bcaa297f7b8f130e with the beacon, 13,225 B
    / fa31dd15248287ce without), 13 shapes get the beacon and 15 do not:
      beacon YES (13) — NO HEADER, ``text/html``, ``text/html2``,
        ``text/htmlish``, ``text/htmlX``, ``"  text/html  "``, ``xtext/html``,
        ``text/html``+trailing space, ``a text/html b``, ``text/html,*/*``,
        ``text/plain,text/html;q=0.1``, ``text/html;q=0.9``, ``text/html;q=0``;
      beacon NO (15) — ``*/*``, ``*/*;q=0.8``, ``TEXT/HTML``, ``Text/Html``,
        ``text/HTML``, ``TEXT/HTML;q=0.9``, ``text/plain``, ``text/*``,
        ``text/htm``, ``tex*/html``, ``text//html``, ``application/json``,
        ``application/xhtml+xml``, ``image/png``, and a present-but-BLANK
        ``Accept:``.
    Both sides carry NON-star shapes (``TEXT/HTML`` no, ``text/html2`` yes), so
    the star was never the axis. The dead path is the same rule on the 404 body:
    1,069 B / 829eacac57f53ed4 vs 702 B / 83972470b5674ad9, same shape split.
    The old "unless the client sends ``Accept: */*``" wording was falsified in
    both directions (dana AMS #3072, lex AMS #3061). The live check strips the
    beacon before comparing and asserts the ``*/*`` and no-Accept shapes agree
    once stripped — still a valid probe under this rule (absent -> beacon,
    ``*/*`` -> none), though the pair is NOT the general rule — instead of
    pinning a digest that only reproduces for one client shape.

    Pin the beacon-stripped DIGEST, never the byte count. The count is
    client- and RUM-dependent, and two of its reported values are ONE reading
    in two units, not two readings: star-Accept 13,225 B / 13,169 chars,
    no-Accept 13,592 B / 13,536 chars. The 56-count delta is the 32 non-ASCII
    codepoints on the page, and sha256(bytes) == sha256(chars.encode()) here.
    The stripped digest fa31dd15248287ce is identical across both units and
    both shapes, and that is the fact worth pinning. (lizzie, AMS #2645
    #2646 #3038; dana, AMS #2609 #2641 #2647; re-measured here 2026-10-02.)
  * Every tree file is checked at ``/`` + its path from the repo root. That is
    a convention, not a fact about the wire, and it has already been wrong once:
    on 2026-10-02 the publish root moved from the REPO ROOT to ``deploy/``, so
    ``/deploy/index.html`` and ``/README.md`` stopped answering (404) while
    ``/`` and ``/privacy/`` stayed 200. The tree-derived paths then addressed
    nothing that was served, and the wire text leg silently covered only the
    apex pages. ``scan_url`` now prints how many paths 404-skipped and warns
    when every non-apex path did, so a green here cannot quietly mean less than
    it reads as. (dana, AMS #2703; verified live here.)
  * The residue registry is NOT a list of dead paths, and the discriminator is
    the LAYER, on a plain GET: apex-zone vs Pages-origin
    (familyosai-cma.pages.dev). Written down because it decides what a red
    means. Measured 2026-10-02 06:17-06:45 EDT from four egresses (dana AMS
    #2763/#2811/#2812; lizzie #2778/#2801; lex #2793/#2797; re-measured here on
    RecRoomRig):
      - 5 of 15: zone 200 / origin 404 -> zone cache residue, purgeable. These
        are the real served residue: familyos-explainer.mp4 (696,581 B, main's
        blob), familyos_explainer.py (9,251 B, main's blob, carries the banned
        sentence below), concat.txt, short1-reminder-treadmill.mp4,
        familyos-logo-painted.png.
      - 4 of 15: zone 200 / origin 200, equal digests -> the deployment holds
        it. A purge can NEVER discharge these: /deploy/, /README.md,
        /.gitignore, brand/og-card.png.
      - 6 of 15: 404 at both -> short2-6, walkthrough.
    A zone-only count reads 6 both-shapes-404 / 9 plain-200, which is
    reproducible and agrees with dana — but it CONFLATES the 5 stale with the 4
    the deployment holds, so it cannot tell a live file from a stale one. That
    is why the header records the layer split, not the zone count. My own two
    served counts, 5/15 and then 6/15, were both ZONE-ONLY reads: a plain 200
    at the zone cannot separate a stale-zone copy from a live-at-both one, so
    neither vantage could see the 4/6 split at all. Both are withdrawn, both
    were mine, and the pair is frozen here on purpose — these are the numbers I
    carried on the bus, and a file that claims to be "written down, not
    inferred" must not oscillate between 5/10 and 5/15 across commits. Provenance
    for the frozen pair: it was carried in AMS #2825/#2826/#2832. The ids first
    cited in the c862f2d commit message (#2728/#2739/#2763) do NOT carry it -
    #2728 carries no residue fraction, #2739 carries 18/18 and 23/23 self-test
    counts, #2763 carries 9/15 and 15/15 - so cite the messages that actually
    held the pair. lizzie #2902 retracted the contrary "should be 6/15 -> 6/15"
    claim of #2896/#2898; the frozen line stands as written. (lizzie, AMS #2836.)
    Do NOT use "200 plain / 404 cache-busted" as the purge test: a query string
    is a ROUTE CHANGE, not a cache-buster. It 404s at the ZONE as well as at the
    ORIGIN (dana, AMS #2849), so it is not even a zone-vs-origin discriminator;
    only plain-vs-plain is a valid leg. And the route change is CONDITIONAL on
    the route, not universal: /deploy/, /README.md, /.gitignore and every
    SERVED /deploy/assets/... path answer 200 plain and 404 for any query
    string at BOTH hosts - the two images that flip AT THE ZONE are
    /deploy/assets/brand/og-card.png (29,450 B) and
    /deploy/assets/brand/familyos-logo-painted.png (1,131,556 B), and they
    do NOT share a layer: og-card is LIVE-BOTH (zone 200 / origin 200,
    equal digests 12d98bca6451 - the deployment holds it), while
    logo-painted is STALE-ZONE (zone 200 / origin 404/702/83972470b567 at
    /deploy/; its 200 is the ROOT twin /assets/brand/familyos-logo-painted.png)
    - the same 5/15 class as familyos_explainer.py. The "at BOTH hosts" half
    is true only of the ?cb 404; it is FALSE of the plain 200 for every
    stale-zone member, which is exactly the conflation L64-70 warns about.
    (lizzie #2950, re-measured here 2026-10-02.) "SERVED" is
    load-bearing, not decoration: /deploy/assets/brand/familyos-appicon.png,
    /deploy/assets/painted/themes/dino-explorer.png and
    /deploy/assets/social/ig-cover.png are already 404/702 B on PLAIN, so they
    cannot "answer 200 plain" and do not belong to the flip class - a path that
    is 404 on plain is 404 under ?cb too. (lizzie #2917, dana #2924; re-measured
    here 2026-10-02.)
    - while the ROOT routes (/, /index.html, /privacy/, /terms/, /404.html)
    and the ROOT assets (/assets/brand/og-card.png 29,450 B, appicon
    1,381,828 B, logo-painted 1,131,556 B) answer 200 under the same query
    string at BOTH hosts. Note the honest-404 reading is a REDIRECT-FOLLOWING
    one: /404.html and /index.html are 308/0 B on a plain no-redirect GET
    (location /404 and /), and answer 200 only because urllib follows
    redirects. /404 is the single-hop path if a caller ever disables redirects.
    The pin is unaffected (both paths resolve to the same 702 B bytes), but a
    no-redirect probe reads 308, not a broken 404. (dana #2924.) A leg that 404s a fully live page route
    (/deploy/) classifies live files as purged, which is how a still-served
    banned file passes a purge-acceptance check.
    Correction of my own, re-measured 2026-10-02 (three plain + three ?cb reps
    per host, both hosts): an earlier version of this bullet gave "a fully live
    brand/og-card.png" as an example of the ?cb 404, and the fix I first made
    swung to the opposite error - "live image assets keep answering 200 under
    the same query string" (dana #2891/#2893/#2895, lizzie #2899/#2901 carry
    the correct narrowing). Both are half-wrong, and the variable is the PATH,
    not asset-vs-page. /deploy/assets/brand/og-card.png is 404/702 B under ?cb
    at BOTH hosts; its ROOT twin /assets/brand/og-card.png is 200/29,450 B
    under the same query string. So the ?cb 404 is exactly the /deploy/ route
    plus the two repo-root metadata files, and nothing else; a blanket
    asset-vs-page rule would mis-predict the live og-card either way. The
    conclusion (not a purge test) is unchanged. Written down because this
    file's whole value is that its examples reproduce.
    The one path several of us argued about — short2-when-then.mp4 — is 404 on both hosts under every shape and every
    query string; my earlier "200 on the third busted variant" is withdrawn.
    Consequence for this guard: the wire leg exits 1 today on
    familyos_explainer.py (200, 9,251 B, "lives in your house" at line 166) and
    on familyos-explainer.mp4 in --media. Both are Chris-gated (a zone purge or
    PR #2's deploy). Trimming the registry cannot discharge them.
      - And the banned bytes are ``origin/main``'s, not just the zone's. The wire
        familyos_explainer.py is sha256 339f229565545cf7, byte-identical to
        origin/main's blob 80c97adf (``git cat-file blob | sha256sum``), and the
        wire explainer.mp4 is sha1 5f364e21e0830807…, identical to origin/main's
        blob bed05488. So a zone purge removes the SERVED copies without making
        the claim go away: origin/main still carries the banned render script,
        and any future publish reproduces it. The durable fix is the merge order
        (PR #2 -> PR #3); the purge is interim. (dana #2845/#2846/#2849; lex
        #2842/#2843 — each re-measured here before being written down.)
    (dana #2763/#2811; lizzie #2778/#2801/#2803; lex #2793.)
  * Read the served apex against ``origin/main``, never the local ``main``. In
    this worktree the local ``main`` ref sat at 3087f2d (deploy/index.html
    12,398 B, blob d5173b13) while ``origin/main`` was 565e022 (13,225 B, blob
    a0f6d8a8) — the blob the zone actually serves. Comparing the wire to the
    stale local ref produced a false "the live page is not main's page"
    conclusion, which flips the answer to whether a purge is safe. Same class as
    the stale-branch failures this repo has already hit; fetch before you
    compare. (dana, AMS #2810; re-measured here.)


  * Do NOT pin a digest — or a LENGTH, or a BODY — of a 403 challenge body.
    Bot protection rejects the literal, case-sensitive ``Python-urllib`` prefix
    — not ``python-urllib/3.11`` — with 403. The body is shape-dependent, NOT
    EGRESS-dependent: the two bodies are two REQUEST SHAPES through the SAME
    Cloudflare block, and either one reproduces from ANY egress if you send the
    right shape. Measured here 2026-10-02 from RecRoomRig, one egress, literal
    ``Python-urllib/3.11`` at both hosts (Accept x Accept-Encoding matrix):
      no Accept (AE: identity alone OR absent) -> 403, 17 B, ``error code: 1010\n``,
        sha256 2938e9f128418095, stable both hosts;
      Accept: */* (+ AE: identity)             -> 403, ~7.1 KB HTML managed-
        challenge, 7,145 B zone / 7,175 B origin, sha256 regenerated per request.
    The ~7,145 B body is the one the ai-lounge egress reported; this egress
    reproduces it with the SAME one-line shape change, so the split is not the
    network, it is the request. That HTML body is a TEMPLATED page carrying a
    PER-REQUEST Ray ID (a Ray-ID token at two lines plus the ``<ray>-ua45``
    signature string, all the same value), not XOR'd bytes: normalizing ONLY the
    Ray ID collapses the six zone digests to one, and the Ray ID + the one-second
    UTC stamp gives 4/4 -> 1. So do NOT describe it as "per-request-XOR" (that is
    the ``data-cfemail`` payload's mechanism, a different section) and do NOT pin
    it either way. Note the guard's own live leg sends ``Accept: */*`` — it is on
    the BIG shape, not the 17 B one. The durable pin is the PAIR (403, literal-UA
    ``Python-urllib`` — case-sensitive) and NOTHING about the body: a length pin
    is the same class of mistake as a digest pin. Two of us carried a sha16 here
    and both retracted it. (lex AMS #2842/#2843/#2906/#2907 and #2962/#2963, the
    axis correction; re-measured here 2026-10-02, 4-shape matrix.)

  * The 404 body is pinned by DIGEST, and the pin is wire-derived. Cloudflare
    serves /404.html (200) and every unknown path (404) the same bytes, but
    appends the analytics beacon on the same case-sensitive ``text/html``
    substring rule as the apex bullet above: present iff the raw ``Accept``
    header carries that literal substring, or the header is absent. The old wording
    here ("for any non-star ``Accept``") was falsified by a 15-shape sweep
    (dana AMS #3072; re-measured here 2026-10-02 from RecRoomRig, 3 reps each,
    stable); the full 13/15 split is in the apex bullet above. Endpoints at
    the apex zone: 702 B / 83972470b567 under ``*/*`` (and under the non-star
    ``TEXT/HTML``), 1,069 B / 829eacac57f53ed4 under ``text/html`` or no
    header. NON-star shapes land on BOTH sides, so the star was never the
    axis. The Pages origin injects nothing and stays 702 B / 83972470b567 on every shape
    (re-measured: no header, ``*/*``, ``text/html``, ``TEXT/HTML``,
    ``text/plain``, ``text/html2``). The beacon-stripped digest is 83972470b567
    on every reading and equal to the beacon-stripped /404.html GET. Pin THAT,
    never the byte count — the length is shape-dependent (702 vs 1,069) and
    host-dependent, which is the same failure mode the apex bullet above
    records. (lizzie AMS #2857/#2851; dana AMS #3072; re-measured here.)

Exit codes: 0 clean, 1 banned claim found OR the honest-404 contract broken,
2 the guard could not run (transport). A broken 404 contract is a finding, not
a transport blip: it removes the guard's ability to trust a 404 skip.
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
# The Pages ORIGIN behind the apex zone. The 404 pin reads BOTH layers, because
# "200 plain at the zone" cannot separate a stale zone copy from a live file and
# the origin is the layer a purge exposes (dana AMS #2849). Same reason the
# residue registry's discriminator is the layer, not the zone count.
ORIGIN = "https://familyosai-cma.pages.dev"

# The honest 404. Cloudflare serves /404.html (200) and any unknown path (404)
# as the SAME bytes, so one digest pins them together. Pin the BEACON-STRIPPED
# digest, never the byte count: the apex zone appends the cloudflareinsights
# beacon on the case-sensitive ``text/html`` substring rule in the apex bullet
# above — present iff the raw Accept
# carries the case-sensitive literal substring ``text/html``, or the header is
# absent — so the zone answers 702 B under ``Accept: */*`` and 1,069 B under
# ``text/html``, but a NON-star ``TEXT/HTML`` also gets 702 B (dana AMS #3072),
# while the Pages origin injects nothing and stays 702 B on every shape. 702 vs
# 1,069 is the exact shape-dependence the apex bullet above warns about, so the
# count is not a pin — the stripped digest is, because ``strip_beacon`` (the
# DELETE-with-\s* rule) makes it shape- AND host-independent. 83972470b567
# measured 2026-10-02 (lizzie AMS #2857; re-measured here across both the
# 4 dead paths x 4 shapes x both hosts matrix and the 15-shape Accept sweep).
# Do NOT re-pin a 404 body that also carries a cf_email span: the XOR key makes
# that digest per-request, which is why this pin is asserted only after
# ``strip_beacon`` and the served body is asserted cf-span-free
# (``normalize_request_scoped`` is a no-op on it) before the digest means
# content.
NOT_FOUND_PATH = "/404.html"
# A true ``sha256_12`` (12 hex chars — the units lizzie carried on the bus and
# the ones this repo's carried records use). NOTE: ``sha12()`` below is a
# misnomer — it returns SIXTEEN hex chars, so the pin is compared against the
# 12-char PREFIX of the digest, never the whole return value. Carrying the
# function's name as if it were its units is the same class of error the apex
# bullet above documents for ``len()`` (characters, not bytes).
NOT_FOUND_STRIPPED_SHA12 = "83972470b567"
NOT_FOUND_STRIPPED_PREFIX = len(NOT_FOUND_STRIPPED_SHA12)
# A path that answers nothing. Distinct from NOT_FOUND_PATH so the assertion
# proves *mapping*, not just that one file is served: the unknown path must
# answer 404 with the 404 body, and /404.html itself must answer 200.
NOT_FOUND_DEAD_PATH = "/__guard-no-such-path__"
APEX_PATHS = ["/", "/privacy/", "/terms/"]

# Cloudflare serves the apex through bot protection and answers the default
# python-urllib User-Agent with 403. Sending a normal one is not evasion — the
# guard is asking for the same bytes a browser gets, which is the only input
# that matters here. ``Accept: */*`` is one shape that keeps the beacon out of
# the body — the axis is the ``text/html`` substring rule above, not the star.
UA = "familyos-claims-guard/1.0 (+https://familyosai.com)"
ACCEPT = "*/*"

# The injected Cloudflare Web Analytics beacon. Stripped before the body is
# compared or scanned so one client shape cannot look like a content change.
BEACON_RE = re.compile(r"<script[^>]*cloudflareinsights[^>]*>.*?</script>\s*", re.S)

# Cloudflare Email Address Obfuscation rewrites every ``/cdn-cgi/l/email-protection``
# href with a PER-REQUEST XOR key, so a page carrying ``data-cfemail`` spans has no
# reproducible raw body digest even at a fixed length. Measured: three identical
# plain GETs of /privacy/ gave three different sha16 at 5,954 B (4 spans), and
# /terms/ likewise at 5,660 B (2 spans), first divergence inside that href. The
# apex has zero such spans, which is exactly why its digest (fa31dd15248287ce) is
# stable. Normalize the encoded payload before digesting so a digest here means
# content, not key material. (dana, AMS #2724/#2725/#2726 — verified live.)
# Both halves of the rewrite are per-request: the href payload AND the
# ``data-cfemail`` attribute on the span carry different hex on each request.
# Clearing only the href left the span different, so two requests of the same
# unchanged page still digested differently — the self-test caught exactly that.
CF_EMAIL_RE = re.compile(r'(?<=/cdn-cgi/l/email-protection#)[0-9a-fA-F]+')
CF_EMAIL_SPAN_RE = re.compile(r'(data-cfemail=")[0-9a-fA-F]*')


def strip_beacon(html: str) -> str:
    return BEACON_RE.sub("", html)


def normalize_request_scoped(html: str) -> str:
    """Remove per-request variance that is not content.

    Today only the cf_email XOR payload, and it only affects non-apex pages; the
    apex is unchanged by this (zero spans), so a digest pinned for ``/`` keeps
    meaning the same bytes.
    """
    return CF_EMAIL_SPAN_RE.sub(r"\1", CF_EMAIL_RE.sub("", html))


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


def scan_url() -> tuple[list[str], list[str], list[str]]:
    """Returns (claim_findings, transport_failures, contract_failures).

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
    # The honest-404 contract, asserted on the wire. It gets its OWN channel:
    # a wrong 404 body is the guard losing its "not served" reading (a finding,
    # exit 1), not a transport blip and not a banned claim on a page. Keeping the
    # three apart is the whole point of scan_url's split return.
    contract = not_found_findings()
    findings += shape_findings(failures)
    return findings, failures, contract


def shape_findings(failures: list[str]) -> list[str]:
    """The pinned apex digest must be reproducible by any client.

    Cloudflare injects the analytics beacon on the substring rule documented
    above. It lands AFTER the closing ``</body></html>`` on the apex ROOT ``/``
    (the shape this probe fetches) and BEFORE it on the 404 path; the position
    is surface-dependent, so do not read "after" as the general rule (lex AMS
    #3079). Offset-free check: the no-beacon body is a PREFIX of the beacon
    body exactly when the beacon is appended (apex ``/``), not when it is
    inserted before the close tag (404) — see the header bullet. The two shapes
    this probes — ``Accept: */*`` and NO ``Accept`` header — sit on opposite
    sides of it (absent ->
    beacon, ``*/*`` -> none), which is why the pair is still a valid probe.
    Stripping the beacon must make the two shapes identical — if it does not, a
    digest pinned in a ticket is unreproducible and the guard says so instead of
    pretending. The pair is NOT the general rule: ``TEXT/HTML`` is a third shape
    on the no-beacon side (dana AMS #3072).
    """
    url = APEX + "/"
    try:
        star = fetch("/").decode("utf-8", "replace")
        none = fetch_no_accept("/").decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        failures.append(f"{url}: request-shape comparison could not run — {exc}")
        return []
    a, b = (sha12(normalize_request_scoped(strip_beacon(star))),
            sha12(normalize_request_scoped(strip_beacon(none))))
    # len() on the decoded str is CHARACTERS. Label it as such: the two
    # shapes differ because the beacon is stripped, and a bare "B" here
    # invited the reading that the byte count itself had moved.
    print(f"[live] {url}: shape */*={len(star)} chars/{a}  no-accept={len(none)} chars/{b}")
    if a != b:
        return [f"{url}: body differs by request shape beyond the analytics beacon "
                f"(beacon-stripped {a} vs {b}) — a pinned digest is not reproducible"]
    return []


def _fetch_status(path: str, base: str = APEX, timeout: int = 25) -> tuple[int, bytes]:
    """Return ``(status, body)``. Unlike ``fetch``, a 404 is a READING here, not
    an exception: the honest-404 contract is *about* the body of a 404, so a
    dead path that answers 404 must yield its bytes rather than raise. Transport
    failures still propagate to the caller, which reports them as transport."""
    req = urllib.request.Request(base + path, headers={"User-Agent": UA, "Accept": ACCEPT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def not_found_findings() -> list[str]:
    """Pin the honest-404 body: a content contract, not a furniture file.

    ``deploy/404.html`` is tracked on ``main`` but NOT on this branch or
    ``origin/main`` (PR #1 removed it — ``git diff --name-status main origin/main``
    shows ``D deploy/404.html``), so there is no tree file to read here and a
    tree-digest pin would be a pin of nothing. The served bytes ARE ``main``'s,
    byte-identical (702 B, verified here), so the wire is the honest source.

    Three readings, each requiring its own status AND agreeing on the
    beacon-stripped digest:
      * the apex ZONE unknown path — must answer 404 with the 404 body;
      * the apex ZONE ``/404.html`` — must answer 200 with the same body;
      * the Pages ORIGIN (``familyosai-cma.pages.dev``) unknown path — must
        answer 404 with the same body. This is the layer discriminator: the
        origin injects no beacon, so it is what a purge would expose, and a pin
        that holds only at the zone is a pin of the beacon-injecting layer.
    A status that is merely present is not the contract — ``/404.html`` must be
    200 and a dead path must be 404; a soft-200 catch-all or a hard-500 both
    make the guard's own "not served" reading untrustworthy.
    """
    failures: list[str] = []
    readings = (
        ("zone", NOT_FOUND_DEAD_PATH, APEX, 404),
        ("canonical", NOT_FOUND_PATH, APEX, 200),
        ("origin", NOT_FOUND_DEAD_PATH, ORIGIN, 404),
    )

    def pin(blob: bytes, label: str) -> str:
        # NOTE for whoever reads a self-test log next: under the self-test this
        # line prints the FIXTURE body's length (the monkeypatched page404), not a
        # wire length. On the real wire /404.html and a dead path are 702 B /
        # 83972470b5674ad9 under Accept: */* at both hosts. Do not carry the
        # fixture's ~95 B as a served length. (dana AMS #2958/#2982.)
        text = blob.decode("utf-8", "replace")
        if normalize_request_scoped(text) != text:
            failures.append(f"{label}: 404 body carries a cf_email span, whose XOR "
                            "key is per-request — no digest here is reproducible")
            return ""
        stripped = strip_beacon(text)
        digest = sha12(stripped)
        prefix = digest[:NOT_FOUND_STRIPPED_PREFIX]
        print(f"[live] {label}: {len(stripped.encode())} B beacon-stripped/"
              f"{prefix} ({len(blob)} B raw, sha16 {digest})")
        if prefix != NOT_FOUND_STRIPPED_SHA12:
            failures.append(f"{label}: 404 body digest {prefix} != pinned "
                            f"{NOT_FOUND_STRIPPED_SHA12} "
                            f"(beacon-stripped {len(stripped.encode())} B, sha16 {digest})")
        return prefix

    digests: dict[str, str] = {}
    for label, path, base, want in readings:
        try:
            status, blob = _fetch_status(path, base)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{base}{path}: could not fetch — {exc} "
                            "— the 404 pin could not read this layer")
            continue
        if status != want:
            failures.append(f"{base}{path}: HTTP {status}, expected {want} — "
                            "the guard cannot trust its own not-served reading "
                            "while the 404 contract is broken")
            continue
        digests[label] = pin(blob, f"{base}{path} ({status})")

    zone, canon, origin = (digests.get("zone"), digests.get("canonical"),
                           digests.get("origin"))
    if zone and canon and zone != canon:
        failures.append(f"{APEX}{NOT_FOUND_DEAD_PATH} (404) body does not equal the "
                        f"/404.html GET (200) — {zone} vs {canon}")
    if zone and origin and zone != origin:
        failures.append(f"404 page is layer-dependent: zone {zone} vs origin "
                        f"{origin} — a purge would change what a dead path answers")
    return failures


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
    contract: list[str] = []
    if args.url or args.all:
        found, transport, contract = scan_url()
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

    # A broken 404 contract is a FINDING, not a transport blip: it is the guard
    # losing the ability to trust its own "404 = not served" reading. Reporting it
    # as "endpoint(s) unreachable" made a red 404 look like a network problem
    # (measured 2026-10-02: exit 2, "3 endpoint(s) unreachable"). It exits 1.
    if contract:
        print(f"\nFAIL — {len(contract)} honest-404 contract failure(s):\n", file=sys.stderr)
        for c in contract:
            print(f"  - {c}", file=sys.stderr)
        print("\nA dead path must answer 404 with the /404.html body, and /404.html itself\n"
              "must answer 200. If that contract is broken, a 404 can be a soft-200\n"
              "catch-all or a wrong page, and every 404-skipped path below is NOT a skip.\n"
              "Fix the 404 route/body before reading this run as clean.", file=sys.stderr)
        if not transport:
            return 1

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
