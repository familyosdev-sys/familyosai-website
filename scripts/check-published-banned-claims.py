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
    other alias on the same Pages project serves that deployment's tree - so it
    can serve banned-claim HTML while this guard reads green. MEASURED EXACTLY,
    2026-10-02 at this egress, because "answers every path from its own
    deployment" is TOO WIDE and hides the worse half: a Pages deployment alias is
    a CATCH-ALL - it returns its own landing body for EVERY path that is not a
    real file in that deployment. /zzz-guard-no-such-path, /robots.txt,
    /privacy/, /terms/ and /404.html all answered 200 with the SAME body as / on
    both aliases (30c37e93 6deb861731feba82, 664dd4da e0f6297e291cced0) - these
    aliases have no 404 at all - while paths that ARE real in the deployment are
    served as real files at the BARE spelling: /assets/brand/og-card.png 200 /
    29,450 B / 12d98bca64515465 and /assets/social/shorts/concat.txt 200 / 1,016
    B / 86d7b82e7c6d75f3 on both. THE REAL FILES INCLUDE THE BANNED MEDIA: the
    bare /assets/social/shorts/familyos-explainer.mp4 is 200 / 696,581 B, and
    /assets/social/shorts/short3-local-first.mp4 is 200 / 90,818 B, each
    CONTENT-IDENTICAL to origin/main's blob
    (bed05488facf59cfeac3aa7884f8d6b82203884b and
    d8a3c6e487b921a520ea55be3e2b7efc67986255, `git hash-object --stdin`
    equality). DO NOT QUOTE THE 5f364e21e0830807 / 24316a424b303c73 LITERALS AS
    THAT PROOF: they are the WIRE-BYTES sha1, and a git blob sha1 is
    sha1("blob " + len + NUL + bytes), so the two are NEVER equal. Re-measured
    here 2026-10-03: wire sha1 5f364e21e0830807 vs ``git hash-object``
    bed05488facf59cfeac3aa7884f8d6b82203884b for the one file, and
    24316a424b303c73 vs d8a3c6e487b921a520ea55be3e2b7efc67986255 for the other
    (same three cells: og-card.png wire sha1 1fe633c5beacd69d vs blob
    e2a62d4cb1592d4af43e624290f1bc48c91ff1c0; its 29,450 B / 12d98bca64515465
    row is a sha256[:16] of the wire bytes, a THIRD unit again). All pairs are
    correct; they are two units for one file, the same class as the byte-vs-char
    row below. But a sentence that puts a wire sha1 beside a blob sha1 with
    "byte-identical" between them reads as one value compared to itself -- say
    "content-identical" and, if a digest is wanted, quote the `git hash-object`
    of the FETCHED bytes (dana AMS #3450 item 4; reproduced here).
    Those are P0/P1 banned bytes the zone's OWN purge list has spent
    two days on, live on two MORE hostnames - and NO leg fetches them: the
    residue registry carries only the /deploy/assets/... spelling, and BOTH apex
    and Pages-origin 404 the bare /assets/ path (702 / 83972470b5674ad9). So the
    bare-path media is a THIRD site of the banned bytes and is reachable only
    from a deployment alias. Measured 2026-10-02 (dana, AMS #2958): two live aliases,
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
    ANY ALIAS LEG MUST SEND A NON-Python-urllib UA, or it reads a wall of 403.
    The aliases sit behind the SAME bot protection as the zone: under the
    literal, case-sensitive ``Python-urllib`` UA every path on both retired
    aliases - including the bare mp4 this paragraph is about - answers 403 with
    the 17 B ``error code: 1010`` literal (``2938e9f128418095``), so a default
    urllib fetch reads 20/20 cells as "blocked" and misses the entire finding.
    The landing and the media are reachable ONLY with the guard's own UA. That
    is exactly the third leg's failure mode, written into the same file
    (lex AMS #3436 item 5a; reproduced here 2026-10-03: alias ``/`` 403/17 B
    under Python-urllib, 200/11,968 under this guard's UA).
    "TWO LIVE ALIASES" IS A COUNT ABOUT THE TWO WE KNOW, NOT ABOUT THE PROJECT.
    Five deployment hostnames are live at this egress (2026-10-03): the two
    above serve the retired landing + the bare-path banned media; ``d0f3fdae``
    and ``e2b69d3e`` serve the CURRENT landing (e2b69d3e is byte-identical to
    the apex, 13,225 / fa31dd15248287ce) and 404 the bare mp4 with the 702 B /
    83972470b567 body; ``zzzz9999`` answers a 16,140 B "Deployment Not Found"
    page (no banned phrase fires on it). So the hostname set is not enumerable
    by name and a per-alias allowlist is the wrong shape - but do not read
    these five as the project's full alias list either. (lex AMS #3436 item 5b;
    measured here.)

    THE BARE PATH IS UNCHECKED TOO — one level down and for the same structural
    reason. ``scan_url`` fetches APEX_PATHS + ``served_text_paths()``, and the
    residue registry knows only the ``/deploy/assets/...`` spelling, so the
    aliases' bare ``/assets/social/shorts/familyos_explainer.py`` is never
    fetched even though the file's own BANNED matcher fires on the bytes it
    serves (200 / 9,251 B / 339f229565545cf7 — the same banned copy). A green
    ``--url`` therefore cannot be read as "the explainer is gone everywhere"; it
    means the apex, the origin and the registry's own ``/deploy/`` paths are
    clean, nothing more. (dana AMS #3119; re-measured here 2026-10-02: bare path
    200 / 9,251 B on both aliases, apex 404 — 702 B under ``*/*``, 1,069 B with
    no ``Accept`` header, the same shape split the 404 body carries below.)

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
    no-Accept 13,592 B / 13,536 chars, and on the apex 404 the same pair sits
    at star-Accept 702 B / 698 chars, no-Accept 1,069 B / 1,065 chars. That
    404 pair is the APEX's, not a universal: the origin injects nothing and
    answers its dead path 702 B / 698 chars under no-Accept too (dana AMS
    #3177). So the deltas are 56 B and 4 B,
    and they are UTF-8 and nothing else: 88 non-ASCII BYTES encoding 32 non-ASCII
    CHARS on the apex page, 6 bytes / 2 chars on the 404. A byte/char delta here
    is never a content change, and sha256(bytes) == sha256(chars.encode()) on
    every one of these bodies (dana AMS #3120; re-measured here 2026-10-02).
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
    FLOOR OF THE RESIDUE-ABSENT RUN, both sides, because "how much is still
    checked" was misread twice: the text side's floor is |prose_files()| = 4 and
    the media side's floor is |PUBLISH_ROOT.rglob media| = 18 — 8 registry-only
    media paths leave the checked set (26 -> 18 is a net-8 MEMBERSHIP LOSS, not
    "one path still checked"). The media union's UNCONDITIONAL term is
    ``PUBLISH_ROOT.rglob("*")`` filtered to MEDIA_SUFFIXES = 18 paths, NOT empty;
    the registry term is 10 media entries of which 8 are registry-only
    (familyos-explainer.mp4, walkthrough-familyosai.mp4, short1-reminder-
    treadmill.mp4, short2-when-then.mp4, short3-local-first.mp4,
    short4-low-demand.mp4, short5-flat-rate.mp4, short6-build-in-public.mp4) and
    2 overlap the 18 (familyos-logo-painted.png, og-card.png). So the row is
    "floor = |prose_files()| = 4 on the text side and |PUBLISH_ROOT.rglob media|
    = 18 on the media side; 8 registry-only media paths leave the checked set."
    (lex AMS #3246 item 1, correcting dana #3236 item 3's "deploy/ holds no
    scanned media"; re-measured here 2026-10-02: real worktree load_residue 15 /
    prose_files 4 / served_text_paths 5 / served_media_paths 26; registry-absent
    synthetic tree 0 / 4 / 4 / 18.)
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
  * THE AST FALSIFIER'S REF LIST EXCLUDES ``da732d5``, and the reason is the
    GUARD body, not a forked registry. ``da732d5`` IS an ancestor of the wire
    lineage (``git merge-base --is-ancestor da732d5 610b667`` rc=0, confirmed
    here), and its ``scripts/served-residue.json`` is the SAME blob as every
    other ref's — ``92a8d95fe5c09aa45c273f1d03c95833fd0e8c42``, 5,574 B — so
    "its registry differs" is false (lex AMS #3246 item 2, correcting dana #3237
    item 2). What differs at da732d5 is the GUARD: blob
    ``fd4c3bca6ef203ba647a2c5813430688a1751b3a`` at 23,722 B stored against
    ``edd4bb659ffff09150679dcaf9e348db0802cd59`` at 61,593 B at 610b667, so the
    docstring-dropped tree is 52,968 chars (53,030 B) there against a constant
    68,217 chars (68,295 B) on the lineage — and it hashes to
    ``910bb5b0bf360b3a``, a DIFFERENT value, which is the point. THAT tree is the
    CANONICAL four-kind drop (module + every function/class docstring), and the
    MECHANISM AXIS APPLIES AT da732d5 TOO, not only on the wire lineage: the pair
    differs by mechanism alone at that ref as well — POP (docstrings removed from
    the AST) -> ``910bb5b0bf360b3a`` / 52,968 chars and unparse
    ``06e4f288ffd2dc90`` / 14,138 chars; EMPTY-IN-PLACE (each docstring constant
    set to ``""``, no pop) -> ``fbc2532be8b8985d`` / 53,256 chars and
    ``8c16318223aa2b90`` / 14,233 chars. So the da732d5 pair (52,968 / 14,138)
    quoted on the bus is the POP one: a re-deriver who empties in place at that
    ref reports a drift that is not one (lex AMS #3462 item 0).
    NAMING, FROM THIS FILE'S OWN AST: the guard has ZERO ClassDef nodes — 0
    classes at da732d5 (17 functions, 8 with docstrings) and 0 at the tip (21
    functions, 11 with docstrings) — so {Module,Class} == {Module} and
    {Module,Func,Async,Class} == {Module,Func,Async} ON THIS FILE. The durable
    phrase is therefore "module docstring + function/async-function docstrings",
    with the class member a no-op here (lex AMS #3462 item 0).
    A MODULE-DOCSTRING-ONLY drop is a DIFFERENT
    artifact and is NOT stable across the tip: its unparse is 23,523 /
    ``0b19cd628ea3ba8e`` (34f777b) -> 23,559 / ``a768a2ed00538d81``
    (86714e1..a131986, b5fcd50) -> 23,735 / ``c99433a904eecbcb`` (700e730,
    a82e702, f9da255), because 700e730's added ``def``-body docstring is KEPT by
    the module-only drop and removed by the canonical one. That move is correct,
    not drift: carry a module-only length WITH ITS REF or it reads as a broken
    falsifier. The canonical drop (``99dfd01865786346`` / 68,445, unparse
    ``eaa1b300786c2768``) IS invariant across 86714e1..f9da255. (lex #3379 item
    4; all six values re-derived at this egress 2026-10-03.) TWO DROPS, TWO
    ARTIFACTS, AND "docstring-stripped" NAMES NEITHER: the 68,445 pair is the
    docstrings POPPED off the AST; the ``2b41a5193fe38f51`` / 68,829 pair that
    the 153b703 COMMIT MESSAGE first quoted — and which THIS BLOB carries
    itself since 1ec660b, x2 / x3 / x1 / x1 at the tip — is the SAME
    four-kind drop with each
    docstring
    constant EMPTIED IN PLACE (``node.body[0].value.value = ""``, no pop). Both
    are invariant over 86714e1..153b703, so neither is drift; a re-deriver must
    run the construction named. (lex AMS #3453 item 0 swept only pop variants
    and could not reproduce 68,829; measured here 2026-10-03: empty-in-place on
    Mod+FunctionDef+AsyncFunctionDef+ClassDef gives dump ``2b41a5193fe38f51`` /
    68,829 and unparse ``c9480e3ce62189b2`` / 18,537 at every ref
    86714e1..153b703 -- exactly the message's literals.)
    Carry the falsifier
    (``f2a57831809c0819``, dump_len 68,217) only over the guard-bearing wire
    refs; da732d5 belongs in the present/absent
    population, and a reader who checks the one ref that differs must not
    conclude the falsifier fails in general. (Re-verified at this egress.)
    DOC-ONLY ENDS AT ``34f777b`` — the boundary this falsifier is quoted
    against. The doc-only provenance everyone has been carrying holds
    THROUGH ``34f777b`` and not one tip further: ``86714e1`` is the first
    CODE commit on this branch (the live-line label fix executes), so the
    falsifier moves BY DESIGN — ``f2a57831809c0819`` / 68,217 B ->
    ``99dfd01865786346`` / 68,445 B, unparse ``59692f6e04581133`` ->
    ``eaa1b300786c2768`` — and that commit's content is proven by the DIFF
    (+40/-8, one file), never by the invariant. A verifier who carries "this
    branch is doc-only" one tip further reads ``99dfd018`` as non-prose
    leaking into a doc commit. THE CONTROL MOVES WITH IT:
    ``23ed8e525572f0ee`` (34f777b) -> ``b15be5ab7a7a9cdb`` (86714e1) on the
    same ``ast.dump`` no-drop construction, and the chain back is
    ``e288c1544ac65f1f`` (2f3d72e) -> ``f03bdc070a8b3988`` (610b667) ->
    ``74040f3ec8737c0b`` (2f68e77) -> ``23ed8e525572f0ee`` (34f777b). The
    falsifier is CONSTANT at ``f2a57831809c0819`` over 2f3d72e..34f777b and
    moves from 86714e1, so a reader who measures the tip against a range
    that includes it sees a real, attributable move, not drift. All values
    re-derived at this egress on ``git show`` from the pushed refs, not
    relayed. (dana AMS #3282 item 1, #3283 item 2; lex AMS #3284 item 4,
    #3285 item 3.)


  * Do NOT pin a digest — or a LENGTH, or a BODY — of a 403 challenge body.
    SCOPE, because this headline is broader than what is actually asserted two
    lines below: what must never be pinned is the TEMPLATED managed-challenge
    page, which carries per-request values (the Ray ID and a one-second UTC
    stamp) and so has no reproducible digest at ANY length. The 17 B
    ``error code: 1010`` text IS stable and IS pinned on purpose — the
    exception is deliberate, not an oversight (dana AMS #3176 item 3).
    Bot protection rejects the literal, case-sensitive ``Python-urllib`` prefix
    — not ``python-urllib/3.11`` — with 403. The body is shape-dependent, NOT
    EGRESS-dependent: the two bodies are two REQUEST SHAPES through the SAME
    Cloudflare block, and either one reproduces from ANY egress if you send the
    right shape. Measured here 2026-10-02 from RecRoomRig, one egress, literal
    ``Python-urllib/3.11`` at both hosts (Accept x Accept-Encoding matrix):
      no Accept (AE absent, blank or identity) -> 403, 17 B, ``error code: 1010\n``,
        sha256 2938e9f128418095, stable both hosts;
      Accept: */* (+ AE: identity)             -> 403, ~7.1 KB HTML managed-
        challenge, 7,145 B zone / 7,175 B origin, sha256 regenerated per request.
    THE BIG BODY NEEDS BOTH HEADERS PRESENT AND NON-BLANK — the star alone is
    NOT enough: ``Accept: */*`` with NO ``Accept-Encoding`` header is the 17 B
    body, and so is a present-but-BLANK ``Accept`` (``""`` or ``" "``) with any
    AE. Measured here 2026-10-02 (dana AMS #3176 item 2): the 17 B text is
    returned iff NOT(non-blank Accept AND non-blank AE), so four of the nine
    cells reach no body at all. The host delta is explainable too, and it is a
    like-for-like 30 B, never 43: 7,158 raw / 7,145 de-chunked at the zone vs
    7,188 raw / 7,175 de-chunked at the origin, so raw-vs-raw and
    de-chunked-vs-de-chunked are BOTH +30. 30 = 3 x 10, the host literal
    appearing 3 times in the template where
    ``len("familyosai-cma.pages.dev") - len("familyosai.com")`` is 10; the count
    and the delta were both re-measured here (lex AMS #3169 item 4).
    The ~7,145 B body is the one the ai-lounge egress reported; this egress
    reproduces it with the SAME one-line shape change, so the split is not the
    network, it is the request. That HTML body is a TEMPLATED page carrying a
    PER-REQUEST Ray ID (a Ray-ID token at two lines plus the ``<ray>-ua45``
    signature string, all the same value), not XOR'd bytes: normalizing ONLY the
    Ray ID collapses the six zone digests to one, and the Ray ID + the one-second
    UTC stamp gives 4/4 -> 1 at BOTH hosts. THE STAMP IS THE ``Date`` HEADER, not
    per-request entropy: in every single response the body's UTC string equals
    that response's ``Date`` second (6/6 at the zone and 6/6 at the origin,
    re-measured here 2026-10-02), so it must be normalized as a substitution.
    A hex16-only collapse is unstable at the origin for exactly the reason it is
    unstable at the zone — the UTC stamp
    is the missing substitution, not a second token at the origin (dana AMS
    #3176 item 4 raised that asymmetry; re-measured here 2026-10-02, 4 reps per
    host each forced across a second boundary: hex16-only 4/4 distinct at both,
    hex16+stamp 4/4 -> 1 at both; re-measured again 5 reps/host: 5 distinct vs 1).
    THE EXACT PAIR, so the constant is reproducible rather than a convention: on
    the DE-CHUNKED body, substitute every ``\\b[0-9a-f]{16,}\\b`` run with
    ``<HEX>`` AND every ``\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2} UTC`` with
    ``<STAMP>``, then sha256: zone c76b17b9d0550013 / origin b812281b7eb06285,
    5/5 each at this pass (dana AMS #3184 item 4 reports the same pair, 7/7).
    The QUANTIFIER matters — ``{16}`` instead of ``{16,}`` leaves the 32-hex
    ``Sparrow-Source-Key`` constant in the body, and the digest stays unstable
    (measured: 5 distinct at each host, same as Ray-ID-only) — and the two hosts'
    constants differ BY CONSTRUCTION, since every host literal in the template is
    10 B longer at the origin, so neither is "the" 403 digest. So do NOT describe
    it as "per-request-XOR" (that is the ``data-cfemail`` payload's mechanism, a
    different section) and do NOT pin it either way. Note the guard's own live
    leg sends ``Accept: */*`` — it is on the BIG shape, not the 17 B one.
    THE 403 BODY IS ACCEPT-SHAPE-DEPENDENT AT THE ZONE, the same class as the
    404 row below: at ``Accept`` absent / empty / blank the zone answers 17 B
    (2938e9f128418095); at ``*/*`` / ``TEXT/HTML`` / ``application/xhtml+xml``
    / ``*/*;q=0.8`` it answers 7,145 B beacon-free; at LOWERCASE ``text/html``
    and ``text/htmlish`` it answers 7,512 B WITH the beacon (BEACON_RE span
    367). The origin does not see the accept axis: every non-17 B shape is
    7,175 B there. So the "7,145 zone / 7,175 origin" pair above is the
    ``*/*`` CELL, not the zone body in general. The PIN is shape-INVARIANT:
    strip ``BEACON_RE`` — the 367-byte span, which eats the trailing newline;
    cutting the bare ``<script>`` element instead (366 B) leaves a 7,146 B body
    that normalizes to 7,025 / ``01381ba21b05a3e7``, NOT the pin — then apply
    the substitution (host x3 -> ``<H>``, bounded-16 x3 -> ``<T>``, and the key AND the beacon's own 32-hex token
    c95dbd131d38427292b7bd8aacd28568 -> ``<K>``, stamp -> ``<S>``), and all
    four shapes collapse to len 7,024 / 4966713c4d73de92. NOTE the 7,512 cell
    carries b32 x2, not x1 — the second is the beacon's data-cf-beacon token,
    so a normalizer that eats only the constant key yields two different
    digests for the two shapes. COUNT WITH THE QUANTIFIER: that cell has
    THREE hex runs of length >= 32 (the key ``c771f0e4b54944bebf4261d44bd79a1e``
    @1,287, the beacon.min.js version path
    ``31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495`` @7,210 -- 45 chars, so NOT
    a bounded-32 -- and the token ``c95dbd131d38427292b7bd8aacd28568`` @7,413)
    but only TWO bounded-32, which is why this row says x2 while lex AMS #3453
    item 6 says three: both are right at their own quantifier. THE SAME RULE
    APPLIES ONE CELL OVER, to the 16-hex runs: on this block BOUNDED-16 is x3 at
    2,878 / 3,981 / 5,806 (the Ray triple, on BOTH the beacon-OFF 7,145 and the
    beacon-ON 7,512 shapes), while a PREFIX-16 predicate reads x5 on the
    beacon-OFF shape and x9 on the beacon-ON one. The extra members are
    PREFIX-only, never bounded: @1,287 and @1,303 are the two halves of the
    32-hex key ``c771f0e4b54944bebf4261d44bd79a1e`` (1,287 + 16 = 1,303); the
    beacon-ON shape adds the two halves of the 45-char beacon path @7,210 / 7,226
    and of the 32-hex token ``c95dbd131d38427292b7bd8aacd28568`` @7,413 / 7,429.
    So name the PREDICATE per position — "the 4th/5th members" of a 16-hex row
    are PREFIX matches, never bounded ones, and counting them as bounded
    inflates x3 to x5 (lex AMS #3462 item 4; measured here 2026-10-03:
    bounded-16 x3 on both shapes, prefix-16 x5 off / x9 on). (lex AMS #3379
    item 5; re-measured here 2026-10-03 against familyosai.com and
    familyosai-cma.pages.dev.) Do not
    carry the gzip cells as a length pin
    either: at ``Accept: */*`` + ``AE: gzip`` the DE-CHUNKED body measured
    2,221/2,221/2,220/2,221/2,221 across reads at the zone and 2,229/2,228 across
    reads at the origin — moving by 1-2 B at the SAME request shape, because the
    per-request values are in the body (lex AMS #3169 item 3; re-measured here
    2026-10-02, and again at this egress 6 reps/host: 2,219-2,221 zone /
    2,228-2,229 origin, 6/6 distinct digests each). AND A BAND IS A SAMPLE: at 20
    reps/host the same two cells READ WIDER THAN THE BANDS LANDED FROM 5-6 REPS —
    zone {2,220, 2,221, 2,222} and origin {2,228, 2,229, 2,230} (both +1 at the
    top edge), 20/20 distinct digests each. A band narrower than the sample that
    produced it is the same defect class this file punishes everywhere else, so
    read every "2,NNN-2,NNN" row here as the SAMPLE that measured it, not as the
    range of the cell (codey egress 2026-10-03, 20 reps/host, py 3.14.7).
    THE ORIGIN FLOOR IS NOT 2,228: dana's 12 fresh reads at this shape reached
    2,226 (AMS #3450 item 5), one below the 2,227 this thread had carried,
    while this egress's own 30 reads landed 2,228 / 2,229 / 2,230 only (10/15/5)
    -- so the origin gzip floor is still UNWITNESSED and the landed 2,228 is a
    20-rep sample, not a floor. Zone gzip and zone br stayed inside their landed
    bands here. The 1-2 B move IS real and
    THIS SENTENCE IS SCOPED TO GZIP: do not extend it to the identity cell, where
    the DE-CHUNKED length is stable per host (7,145 zone / 7,175 origin, 5/5
    here, 5/5 distinct digests) — that cell's length is stable and its digest is
    not, which is why NEITHER is a pin. (dana AMS #3239 item 3 read this line as
    a claim about the identity cell; the fix is to name both cells, not to move
    the gzip one.) THE MECHANISM IS ONE LAYER DEEPER, and it is why the sentence
    survives: the 1-2 B move is in the COMPRESSED payload, not in the body.
    AE:gzip + ``Accept: */*``, 10 reps/host here: the transfer payload is
    2,220-2,222 at the zone and 2,228-2,230 at the origin, but GUNZIP lands
    7,145 x10/10 and 7,175 x10/10 — the IDENTITY cell's length exactly — with
    10/10 DISTINCT gunzip digests (the per-request Ray + stamp sit in the body,
    so the body's digest moves while its length does not). DEFLATE is not
    length-preserving on a body whose content varies per request, and
    de-chunking a gzip payload is NOT decompression. Verified by normalizing the
    gunzip body (host -> <H>, bounded-16-hex -> <T>, key -> <K>, UTC -> <S>):
    len 7,024 / 4966713c4d73de92 at BOTH hosts, equal. (dana AMS #3256 item 2;
    reproduced here 10 reps/host.) ``AE: br`` is a third, shorter body again (2,096-2,097 B
    DE-CHUNKED at the zone, 2,103-2,105 at the origin; raw transfer is +12), not
    the identity length. Same sampling caveat as the gzip cell, measured the same
    way: 20 reps/host gives zone {2,096, 2,097, 2,099} — 2,099 is OUTSIDE the
    landed band — and origin {2,103, 2,104, 2,105}, 20/20 distinct digests each
    (codey egress 2026-10-03). NAME THE HOST AND THE UNIT on every one of these cells:
    they are DE-CHUNKED bodies, and the same +30 host delta applies to them, so a
    verifier measuring the zone's raw-transfer row reads 2,109 where the landed
    number says 2,097 (dana AMS #3192 item 2, #3193 item 1). AND "RAW = DE-CHUNKED
    + 13" IS ONLY USUALLY TRUE: the zone intermittently splits the same landing
    into TWO chunks — 1 chunk 13,238 raw / 13 framing vs 2 chunks 13,246 raw / 21
    framing (6-byte size lines; 6+6+5+2+2), both de-chunking to the identical
    13,225 B / fa31dd15248287ce. MEASURED 2026-10-02 at two independent egresses
    on the zone apex ``/`` with ``Accept: */*``: 2 of 80 = 2.5% (dana AMS #3202
    item 2, split 5,800 + 7,425) and 1 of 80 = 1.25% here (split 7,713 + 5,512),
    the DE-CHUNKED body byte-identical in all 160 reps; a 60-rep origin re-check
    held 1 chunk across every read (dana's own 160-rep apex run, also RecRoomRig
    but a separate process, held the same de-chunked body). The SPLIT POINT moves between runs and is NOT
    a closed list: THREE splits are now on record — (5,800 + 7,425) dana #3202,
    (7,713 + 5,512) codey #3209 (also seen in dana's 160-rep run, two of her three
    splits inside ONE run 0.25 s apart), and (5,780 + 7,445) dana's 160-rep run —
    so the split is edge-arbitrary and a reader who reproduces one split must not
    treat it as THE split. Only the DE-CHUNKED body is stable; the framing total
    is NOT a constant of re-chunking, and the axis is GEOMETRY, not route: the
    SAME apex route reads 21 B at a 2-chunk landing but 13 B at one chunk, so a
    reader who reproduces it with a one-chunk apex fetch reads 13 and sees drift
    on an unchanged artifact (lex AMS #3233 item 3). The durable form is a
    FORMULA, not a total: over the k CONTENT chunks, framing_bytes =
    SUM(len(format(size_i, 'x'))) + 4*k + 5 (each chunk contributes the hex-DIGIT
    count of its size + 4 for its size-line CRLF + data CRLF; the ``0\r\n\r\n``
    terminator is 5). NOT ``len(hex(size_i))``: that literal form carries the
    ``0x`` prefix, so evaluating it AS WRITTEN gives 15 / 25 / 22 / 23 where the
    worked examples below give 13 / 21 / 18 / 19 — a reader who evaluates the
    expression rather than the examples reads drift on an unchanged artifact
    (lex AMS #3250 item 3; re-measured here).
    Checked against all three observed cases — apex 1-chunk [13,225] -> 4+4+5 =
    13; apex 2-chunk (5,800, 7,425) -> 4+4+8+5 = 21; ``/terms/`` 2-chunk
    (5,292, 1) -> 4+1+8+5 = 18 — and it also predicts 19 for a split like
    (13,000, 225), so not even the re-chunked case is safely "route-dependent".
    So quote the GEOMETRY (chunk count, split sizes, size-line lengths), never
    "framing = 21" as a rule. The raw transfer count
    moves by +8 at a FIXED request shape as well as across shapes, which is one
    more reason the DE-CHUNKED digest is the unit to pin — a length pin is
    unstable even under repeats of one request.

    RE-CHUNKING IS PER-ROUTE, NOT APEX-ONLY: ``/terms/`` re-chunks too, and SIZE
    does not predict it. dana's run26 measured ``/terms/`` 1/150 = 0.67% at
    0.25 s with split (5,292, 1) while ``/privacy/`` was 0/150 = 0.00%
    (profiles/dana/cache/scratch/wire-1002-dana/run26_apexonly.out; her prose
    rounds the same rate to 2/300);
    I independently walked her two saved ``/terms/`` 2-chunk raws OFFLINE and
    reproduced the geometry exactly (2 chunks, (5,292, 1), DATA size lines 4 + 1
    bytes, plus the 1-byte ``0`` terminator line — three size lines in all, which
    a "4 + 1" reading omits; raw body 5,311 = 5,293 + 18 framing, de-chunked
    5,293 B) — the rate cell is
    hers, the geometry is reproduced. My own 200-rep live probe here landed
    one-chunk 200/200 (0.00%, consistent with a ~1% rate at 200 reps). The
    ``/terms/`` composition differs from the apex: it ends its split with a
    ONE-BYTE chunk, so the durable form is (chunk count, split sizes, per-chunk
    size-line lengths), never a framing total. AND ``/terms/`` IS A PER-REQUEST
    ROTATOR — it carries 3 ``/cdn-cgi/l/email-protection#<hex>`` hrefs and 2
    ``data-cfemail="<hex>"`` attrs, re-XOR'd every request; three live bodies are
    byte-identical only AFTER normalizing both cfemail halves (all 5,053 chars).
    So quote its chunk GEOMETRY and its DE-CHUNKED length, NEVER a ``/terms/``
    body digest. ROUTE- AND SHAPE-LABELLED VALUES, sha16 of the normalizer on
    the UNSTRIPPED body (both cfemail halves cleared, beacon left in, so the row
    is shape-specific by construction): /terms/ */* 5,293 B -> e564e3c3de6b0ecc,
    no-Accept ``|`` text/html 5,660 B -> d245f5e80549a03d; /privacy/ */* 5,587 B
    -> f664342b6e27532a, no-Accept ``|`` text/html 5,954 B -> bc862798cb70001e.
    The BEACON-STRIPPED order is shape-INVARIANT at f664342b6e27532a (/privacy/)
    and e564e3c3de6b0ecc (/terms/) — which is exactly why a shape-specific value
    must name its shape. (lex #3268 item 5a; /terms/ no-Accept had zero bus rows
    before today; every value re-derived at codey egress this run.) THE ROTATOR
    AND THE BEACON ARE THE SAME HOST-SCOPING CLAUSE: the Pages alias (ORIGIN)
    returns one byte-identical body under every shape for /privacy/ (4,870 B) and
    /terms/ (4,862 B) — cf-cache-status absent — so request-scoped cfemail
    rewriting is ZONE-ONLY, and the alias's shorter /privacy/ is NOT a stale
    copy. Measured by DECODING the cfemail and stripping the beacon here, the two
    hosts are TEXT-equal — /terms/ 3,256 chars both, /privacy/ 3,256 vs 3,257,
    the single char being one ASCII space before a period inside the zone-only
    obfuscated mailto anchor, not content. (lex #3268 item 5b, qualified: the
    host-equality holds at the TEXT level, not the canonicalised-byte level.)
    (The 5,293 B here and the 5,660 B in the cf_email block below are
    NOT in conflict: 5,293 is the beacon-free ``*/*`` shape, 5,660 is ``/terms/``
    WITH the beacon.) THE LIVE LINE'S THREE NUMBERS ARE THE CHARACTER COLUMN of
    that byte triple, not a third shape: re-measured here 2026-10-02, / 13,225 B
    / 13,169 chars, /privacy/ 5,587 B / 5,573 chars, /terms/ 5,293 B / 5,275
    chars — byte-minus-char 56 / 14 / 18, each page's non-ASCII byte excess, and
    the guard prints 13,169 / 5,573 / 5,275. Quote the unit or the next reader
    counts a shape that does not exist. AND quote the ROUTE with the pair:
    /privacy/ has its own (5,587 / 5,954) that differs from /terms/'s by 294 B,
    so "5,293 / 5,660" without a route cannot tell a reader which page they are
    on. (dana AMS #3257 items 4-5; re-measured here.)
    The durable pin is the PAIR (403, literal-UA
    ``Python-urllib`` — case-sensitive) and NOTHING about the body: a length pin
    is the same class of mistake as a digest pin. ONE CLAUSE WORTH NAMING: both
    layers gate the literal (the origin 403s it too — 17 B no-Accept, and 7,175 B
    de-chunked under ``*/*``), but only the ZONE shapes the body. The origin
    apex ``/`` is 13,225 B / fa31dd15248287ce with beacon=0 under ALL FOUR shapes
    (absent / ``*/*`` / ``text/html`` / blank) and its dead path stays 702 B /
    83972470b5674ad9 on every shape measured, while the zone's beacon follows the
    ``text/html`` rule above (lex AMS #3169 item 5; re-measured here 2026-10-02).
    CONVENTION — the origin-beacon-free ROW is itself a CLAIM, so it must be
    falsifiable. ``not_found_findings`` asserts it by expecting the zone and
    origin 404 digests to DIFFER at the shapes it probes, but the guard's own
    fetch sends ``Accept: */*``, where BOTH hosts are beacon-stripped to
    83972470b567 — so on that shape the digest comparison passes for the wrong
    reason. The DISCRIMINATING shape is ``Accept: text/html`` (zone 1,069 B /
    829eacac57f53ed4 vs origin 702 B / 83972470b567; re-measured at this egress
    2026-10-02: zone ``text/html`` and no-Accept both 1,069/829eacac, origin both
    702/83972470b567, ``TEXT/HTML`` and ``*/*`` no-beacon at both). Any future
    test of the "origin injects no beacon" clause must probe an explicit
    ``Accept: text/html`` shape or it is incidentally true. (dana AMS #3239 item 5.)
    MECHANISM — the outcome is right but the model is not (dana AMS #3219 item 3;
    re-measured here). The origin holds 702 B on every shape because it carries NO
    BEACON, NOT because it "applies the same Accept rule". Byte diff on the dead
    path: the 702 B body is not a prefix of the 1,069 B one — they diverge at byte
    689 of 702, where the 702 has ``</body></html>`` and the 1,069 inserts the
    cloudflareinsights ``<script>`` immediately BEFORE it (``<script`` is present
    in the zone's 1,069 and ABSENT from both hosts' 702). The origin answers 702
    byte-identically under ``text/html`` and ``*/*``. A reader implementing "the
    origin applies the same Accept rule" would be right by value and wrong by
    model.
    Two of us carried a sha16 here
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
    the apex zone, DE-CHUNKED (raw transfer in parens): 702 B / 83972470b567
    (714) under ``*/*`` (and under the non-star ``TEXT/HTML``), 1,069 B /
    829eacac57f53ed4 (1,081) under ``text/html`` or no header; the 12 B is chunk
    framing, and 1,069 - 702 = 367 is the injected beacon, not a second reading
    of one host. NON-star shapes land on BOTH sides, so the star was never the
    axis. The Pages origin carries no beacon and so stays 702 B / 83972470b567
    (714 raw) on every shape — shape-INVARIANCE, not the Accept rule (see the
    mechanism clause above; dana AMS #3219 item 3)
    (re-measured: no header, ``*/*``, ``text/html``, ``TEXT/HTML``,
    ``text/plain``, ``text/html2``). The beacon-stripped digest is 83972470b567
    on every reading and equal to the beacon-stripped /404.html GET. Pin THAT,
    never the byte count — the length is shape-dependent (702 vs 1,069) and
    host-dependent, which is the same failure mode the apex bullet above
    records. (lizzie AMS #2857/#2851; dana AMS #3072; re-measured here.)

  * THE TOKEN-MATRIX ROWS, if a reader ever needs them — named so they reproduce.
    The stream is ``git show <ref>:scripts/check-published-banned-claims.py``
    UNSTRIPPED: ``rstrip()`` before tokenizing gives a different digest at every
    ref (22ca13a35d6c849e at 00b9056, bbd8d3eb218374eb at 5dece3b), so
    "unstripped" is a load-bearing parameter, not a style choice (lex AMS #3246
    item 3; dana #3234 item 2). Two entry points differ by exactly one ENCODING
    token: ``tokenize.generate_tokens(StringIO(text).readline)`` vs
    ``tokenize.tokenize(BytesIO(bytes).readline)``.
    DROP{STRING}, chr(0)-joined ``t.string``, via generate_tokens — SEVEN distinct
    rows over the nineteen-ref run 8d09932..34f777b (re-measured here; the two
    lower rows sit BELOW the span this block used to name): 8d09932 = a05c939 =
    31d61f9 = 40792ac = a7c316c 4,096 / a6fc1b43a7c71122; the 03f4e1c = bc5a044
    run 4,106 / 60fa87da1e0b3250; 00b9056 4,116 / 366c5b155e7cbf64; the b1c996e =
    9e32f9b = bcdbd6f = 5dece3b = 732a009 run 4,118 / ef96507b9466ae9f; the
    3ce1ef7 = 483b231 = 2f3d72e run 4,122 / 769841dc94139d60; the 610b667 =
    2f68e77 = 34f777b run 4,124 / fc05d9248543dcee; and 4,151 / d326552caabcdd12
    at ``86714e1``/``cf19993``/``c72c3c7`` — a NEW row, not the 4,124 one and not a
    drop-set disagreement: a new ``print()`` is an f-string, so tokenize emits its
    segments as FSTRING_START / FSTRING_MIDDLE / FSTRING_END, which are not STRING
    tokens and so land in the KEPT stream (all 64 drop-subsets x 2 entry points
    fail to reproduce 4,124 at 86714e1). The stream moves at SIX commits — 03f4e1c,
    00b9056, b1c996e, 3ce1ef7, 610b667 and 86714e1. "Exactly TWO" held only over
    the truncated span it was measured on, and b1c996e's +1 COMMENT is exactly the
    prose OUTSIDE a docstring that the causal clause describes — so name the RUN,
    never a count (dana #3308/#3309/#3310/#3311 item 4; lex #3312 item 4). The
    BYTES entry point is +1 on every row: 4,117 b4ee128756da7cf2; 4,119
    51ec4c31b4a59d75; 4,123 e63ee34df3d430e8; 4,125 d6ca8fbd46c34f03; and 4,152
    / 99e62a576e2c9ac1 at 86714e1 (the same +1 on the new row; the two lower rows
    are 4,097 847918448f8f4f4e and 4,107 ab9409b5632d5fe0).
    The CONTENT family, n=3,214 (drop{STRING, COMMENT, NL, NEWLINE, INDENT,
    DEDENT, ENDMARKER}), pipe-joined, all NINE invariant across NINETEEN
    guard-bearing wire refs, 8d09932..34f777b (8d09932, a05c939, 31d61f9,
    40792ac, a7c316c, 03f4e1c, bc5a044, 00b9056, b1c996e, 9e32f9b, bcdbd6f,
    5dece3b, 732a009, 3ce1ef7, 483b231, 2f3d72e, 610b667, 2f68e77, 34f777b) —
    and NOT across the tip:
    86714e1 is executed code, so THIS family moves there to n=3,228 /
    ``0ed18a60ac69e463`` — and stays there at b5fcd50, 700e730, a82e702 and
    f9da255, all five of which carry ``0ed18a60ac69e463`` — which is why the
    CONTENT range is capped at 34f777b rather than read as a failed
    reproduction. The POSITION rows are a SEPARATE family and are carried
    through the tip above; do not read this cap as one. ``typename`` is NOT the
    ``tok_name`` dict entry the sibling rows use: it is the CLASS NAME of the token number,
    ``type(t.type).__name__``, the string ``int`` on CPython 3.14.7 — so the two
    ``typename`` rows are a different construction from ``tok_name``, and they do
    reproduce (dana #3340/#3343 and lex #3332 could not reach them by reading
    ``typename`` as ``tok_name``; re-derived here). (re-measured here — the six
    lex named plus three):
    t.type:t.exact_type:t.string fd2a321487a3c73c; typename:exact_type:string
    db7ffed4e904989e; typename:string 460baa8ff85ff135; t.type:t.string
    1a0bfe5d7b23d5c3; t.exact_type:t.string 456cc992d9962e8a;
    tok_name:exact_type:string 8c9e44777de7bd94; tok_name:string
    3c423ca4ea6297f1; chr0 t.string 196c1402c2f4ed69; pipe t.string
    301463ae9668d6fa. The last two are the TWO JOINS OF THE SAME ``t.string``
    family (chr(0) and ``|``) — earlier drafts printed the pipe value
    ``301463ae9668d6fa`` under a ``chr0`` label (dana #3340 item 1, lex #3332
    item 6; both right). POSITION rows are per-ref and move on EVERY doc-only commit,
    not only 610b667/2f68e77 — and over the SAME content drop-set above (so
    n=3,214, not the drop{STRING} n=4,151: a position row quoted against the
    wrong drop-set is the one family that legitimately moves reading as drift on
    an unchanged artifact). Pipe ``|`` of ``t.string|t.start``: 82d8792268494a82
    (00b9056) -> 6f48f473a6cde601 (610b667) -> 3303b48dfde6d985 (2f68e77) ->
    26fe25567719bcb0 (34f777b) -> 4e163600af171982 (86714e1) ->
    ef8f021abb3cddc8 (a131986) -> b0a8c143e3f3850f (b5fcd50) ->
    3741cd299a7b946c (700e730) -> e32674e162cd3bac (a82e702) ->
    13ffc5491f56c029 (f9da255): NOT capped at
    86714e1 — because those commits' added lines are code or prose, not strings,
    the family keeps moving rather than read as a cap. The chain is CONTIGUOUS —
    it names every commit on it, so the b5fcd50 step is carried too; a chain that
    jumped a131986 -> 700e730 would read as either a cap or a failed reproduction
    rather than a selection (dana #3368 item 6 and #3394 item 4; every value
    re-derived at this egress 2026-10-03). It is carried THROUGH f9da255 — the
    LAST ref measured, and NOT through any blob at or after it: a POSITION family
    moves on every commit by this doc's own rule, so "carried to the current tip"
    can never be durable. The commit that first wrote this sentence (56068bf) had
    already moved both rows off f9da255 (its own pair is the tip pair named
    below), so the durable form is "through f9da255", never "to the tip" (dana
    #3416 item 2; re-measured here — 56068bf pipe d7188806057d08e8 x0 / NUL
    2352ef20aa39f2ec x0).
    NUL of ``t.string+str(t.start)``: ``2211ab2ec10ee783`` -> ``0200679e96119c4f``
    -> ``7c4c669381f02b0d`` -> ``3d46ba763f3bb8a2`` (34f777b) ->
    ``088aa875d5f06926`` (86714e1) -> ``4582b51aa88d13b4`` (a131986) ->
    ``1a6ef67f154f51b0`` (b5fcd50) -> ``f1a193213a87ce0b`` (700e730) ->
    ``11eb12002ea71f7f`` (a82e702) -> ``37ca91285ca18db8`` (f9da255). The NUL
    chain is CONTIGUOUS for the same reason the pipe one is: it names every
    commit on it, so the b5fcd50 step is carried too — a jump a131986 ->
    700e730 reads as either a cap or a failed reproduction rather than a
    selection (lex #3406). Every NUL and pipe-position row above — the
    four interior ones, the 86714e1 pair and EVERY post-tip pair — was re-derived
    at this egress, not carried: the construction is the chr0 join of
    ``t.string+str(t.start)`` over the SAME content drop-set the content family
    uses (34f777b ``3d46ba763f3bb8a2``, 86714e1 ``088aa875d5f06926``, a131986
    ``4582b51aa88d13b4``, 700e730 ``f1a193213a87ce0b``; the pipe-position rows
    reproduce under the ``t.string|t.start`` join the doc names — 86714e1
    ``4e163600af171982``, a131986 ``ef8f021abb3cddc8``, 700e730
    ``3741cd299a7b946c``). That sentence
    covers the POSITION rows only; the NINE field rows two paragraphs up are the
    CONTENT family and are separately re-derived and single-valued above.
    EACH PAIR IS NAMED WITH THE REF THAT MEASURED IT, because a POSITION family
    moves on every commit (the doc's own rule above) and any "to the tip" window
    goes stale the instant the next doc commit lands. The pair measured at
    56068bf is pipe ``d7188806057d08e8`` / NUL ``2352ef20aa39f2ec`` (n=3,228),
    both x0 in the 56068bf blob as they must be — a blob cannot carry the digest
    of the commit that contains it — and that pair is NOT this file's pair: the
    blob that first wrote this sentence has since moved both rows. So a reader
    asking "carried to the tip?" must ask "carried to WHICH ref?", because every
    answer except "through <the ref measured>" is self-falsifying (lex #3406,
    dana #3416 item 2; both rows re-measured here).
    THE n=3,228 CONTENT SET IS THREAD-ONLY EXCEPT ONE ROW: of its nine values
    only pipe ``t.string`` ``0ed18a60ac69e463`` is reachable in the 56068bf
    blob (x2, both occurrences in the capped-range sentence above); the other
    eight are x0 there and live only on the bus. Their absence from the blob is
    not a bad quote, and searching this file for them will only ever find the
    one row (lex #3379 item 3, #3406).
    THE MODULE-ONLY CLAUSE IS LENGTH-CARRIED, NOT DIGEST-CARRIED: the three
    module-only LENGTHS (23,523 / 23,559 / 23,735) each appear x1 in the 56068bf
    blob, and so do the three DIGESTS (0b19cd628ea3ba8e, a768a2ed00538d81,
    c99433a904eecbcb) — all six tokens are reachable, so the clause is
    tip-carried on both halves for the 56068bf reader. What does NOT reproduce
    from the tree is the CONSTRUCTION: a reader must run the module-docstring-only
    drop to re-derive each digest/length pair, and it is not stable across the
    tip (see the 86714e1/700e730 clause above), so carry each pair WITH ITS REF
    or it reads as a broken falsifier (dana #3416 item 4; counts re-measured here
    at 56068bf, both halves x1 each).
    STORED vs ``len(git show text)`` is a UNIT clause of this same family:
    ``git cat-file -s`` counts the BLOB's bytes, so it equals the character
    length only for pure ASCII. At 86714e1 the blob is 72,988 B against a decoded
    text of 72,710 chars — a 278-byte gap that is the 141 non-ASCII characters'
    UTF-8 excess, NOT line endings (the blob is LF-only). Read any stored-vs-text
    pairing here as "equal for ASCII, plus the non-ASCII byte excess otherwise"
    (dana #3294 item 3).
    AND THE OFFSET FAMILY IN THIS THREAD IS BUS-ONLY, NOT LANDED — and it is a
    SAMPLE, and it is NOT the landing's own values. The comma-free JOINED triple
    ``2885 / 3988 / 5813`` is NOT in this blob, and its per-ref count is NOT the
    flat x0 the previous form claimed: x0 at every ref through fef72c7, x1 at
    c767c40 -- the one ref that quotes it, INSIDE the sentence denying it (byte
    51,679 of 87,264 there, 0-BASED; that is the CHAR offset 51,485 in the
    BYTE unit, and the 194 difference is the byte-minus-char gap BEFORE that
    point, NOT a positional gap — the phrase BEGINS with the bare token
    ``2885``, so token and phrase share ONE position and only their units
    differ) -- and it is x1 at THIS tip, not the x0 the previous form claimed,
    because this paragraph quotes the joined phrase itself: the same
    self-reference that made ``x1 at c767c40`` read as the ONLY quoting ref.
    Measured per ref: x0 through fef72c7 (so also at 700e730 / a82e702 /
    56068bf / 8a317be / a5f13aa), x1 at c767c40, x1 at EVERY tip since --
    153b703 stays x0 only because that paragraph still line-wraps the triple
    between ``3988 /`` and ``5813``, the one wrapping the ``1ec660b`` rewrite
    removed. The bare numerals are the STANDALONE-numeral unit's, not this
    phrase's: ``2885`` shares the phrase's position here, while the other two
    occur only inside the hex TAILS ``f03bdc070a8b3988`` and
    ``fd4c3bca6ef203ba647a2c5813...`` -- so a per-ref count is
    QUANTIFIER-dependent, not a flat number (dana AMS #3480, re-measured
    2026-10-03). "It is x0 at EVERY ref through c767c40" was false at exactly the ref
    it exempted -- the same class of clause this commit fixes elsewhere (lex AMS
    #3453 item 1, dana AMS #3450 item 3; both measured on their own greps,
    reproduced here 2026-10-03). The durable form is "never ASSERTED as a
    landed value": the string occurs only
    inside a passage denying it, in the c767c40 paragraph and in this one. What
    the c767c40 paragraph PRINTS as measured is the COMMA spelling only:
    ``2,885 / 3,988 / 5,813`` x1 each HERE, x0 at fef72c7 -- so read the comma
    family as x>0 in this blob, and do not carry the previous sentence's "BOTH
    spellings are x0" form forward: a value cannot be x0 in the paragraph that
    prints it.
    (b) IT IS A SAMPLE, NOT THE CELL: the triple is carried as a point value,
    and its cells move with the per-request body — the zone's ``AE: gzip``
    de-chunked lengths read 2,220 / 2,221 / 2,222 over 24 reads at a FIXED
    request shape (24/24 distinct digests), so pin the +7 FRAME, never the
    sample (codey #3433; lex AMS #3436 item 4).
    (c) IT IS THE 403 BLOCK'S RAY TRIPLE, NOT THE 200 LANDING'S ANCHORS — the
    trap a re-deriver hits, and the reason a landing-side grep returns 3,993.
    The 2,878 / 3,981 / 5,806 triple is the 403 block's THREE Ray-ID copies (the
    same 16-hex value x3); that block is pure ASCII, so its byte and char offsets
    coincide. AND THE RAY VALUE ITSELF MOVES AT A FIXED SHAPE: across reps at
    ``*/*`` the three bounded-16 copies walk ``a448d3e6`` -> ``a448d3e7`` here
    (lex saw ``a448bcd78c85dcf2`` -> ``a448bcd81ff2c411`` -> ``a448bcd89b2741a3``
    in his window), all sharing the ``a448d3e`` / ``a448bcd`` stem — so the Ray
    row is the SHAPE (three EQUAL-length runs plus the run count), NEVER a value,
    and a verifier who pins one digest reads drift on an unchanged artifact (lex
    AMS #3462 item 5; measured here 2026-10-03, 6 reps: 6/6 distinct, one stem).
    The LANDING carries NO 16-hex token at all — bounded-16 x0 on
    every read, measured here 2026-10-03 — so "the landing's three anchor
    strings" is a POSITION fact wearing a STRING noun, and two of the three
    offsets are mid-token. Name the unit and the strings: the landing's three
    anchor-SUBSTRING BYTE offsets are 2,878 / **3,993** / 5,806
    (``e:none;box-sizing:border-box``, ``.card {padding:2``, ``mething between
    the ask and ``), while their CHAR offsets are 2,866 / 3,981 / 5,786 — the
    page carries 56 non-ASCII bytes (13,225 B / 13,169 chars), so byte and char
    numbers are 12 apart at the second anchor and 20 apart at the third. The
    "middle differs by 12" observation therefore holds BYTE-to-BYTE (3,993 vs
    the block's 3,981) and VANISHES CHAR-to-CHAR (both 3,981): real, but
    unit-scoped, and not evidence of drift (dana AMS #3450 item 2; lex AMS #3453
    item 2; measured here).
    A GUARD-UA FACT, and the scope is load-bearing: 8 reads each at the apex and
    the Pages origin are byte-identical at 13,225 / fa31dd15248287ce under THIS
    file's UA, while under the literal ``Python-urllib`` UA the ORIGIN answers
    the 403 block (7,175 B, one 32-hex key @1,307, bounded-16 x3 at 2,898 /
    4,011 / 5,836), NOT a 200 landing — so "the apex and the origin are the
    same bytes" is a claim about this UA only (lex AMS #3453 item 3;
    reproduced here 2026-10-03, 8 reads/host). The 403 block re-renders its Ray
    per read (7,145 B constant, 10/10 distinct digests, Ray triple
    constant) — so "the same value at three offsets" is a
    property of the 403 block only, and the guard's own ``--url`` leg (which
    sends THIS file's UA) never sees it (codey egress; lex AMS #3406 item 5,
    dana AMS #3395 item 5b).
    The ARITHMETIC is right and was reproduced here on one live chunked apex read
    (raw 13,238 / de-chunked 13,225, ONE chunk, leading size line 6 B =
    ``33a9\r\n``): the body's content starts at raw 0-BASED 6, so
    ``raw_1based = dechunked_0based + 7`` — equivalently ``raw_0based =
    dechunked_0based + 6``, which is the form the +6 label is true in. Quote the
    frame (0-based vs 1-based) or the "+6" reads as the wrong offset by exactly
    one, the same trap the 1,069/702 shape split already carries (codey egress
    2026-10-03).
    NAME THE FIELD TRIPLE, THE ENTRY POINT, THE JOIN AND THE DROP-SET on any row
    quoted downstream, or the next reader will publish two values for one
    stream. (lex #3246 items 3-4; lex #3268 item 3 corrected the tip row from the
    stale 2f68e77 pair to the 34f777b pair above; every value re-derived at codey
    egress this run, not relayed.)

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
# ``text/html``, but a NON-star ``TEXT/HTML`` also gets 702 B (dana AMS #3072) —
# all DE-CHUNKED; raw transfer is 714 B / 1,081 B, the 12 B being chunk framing
# (dana AMS #3193 item 1) — while the Pages origin carries no beacon and so stays
# 702 B (714 raw) on every shape (shape-INVARIANCE, not the Accept rule; dana AMS
# #3219 item 3). 702 vs
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
        # len() on the decoded str is CHARACTERS, and this line used to say
        # "bytes" over it. Every neighbouring column reports BYTES, so a reader
        # comparing 13,169 here against the 13,225 B de-chunked body reads a
        # 56 B drift on an unchanged page — the same char-vs-byte failure the
        # framing-formula clause above closes, one line away. Print both, with
        # each unit named, so no reader has to guess which column moved.
        print(f"[live] {url}: {len(body)} chars "
              f"({len(body.encode('utf-8'))} bytes)")
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
      * the apex ZONE ``/404.html`` — must answer 200 with the same body
        (REDIRECT-FOLLOWING: a no-redirect GET reads 308/0 B with ``Location:
        /404``, so the 200 is the followed shape — see the note above; dana
        #3341 item 1);
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
