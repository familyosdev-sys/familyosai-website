# Deployed-state record — familyosai.com, captured 2026-10-02

> **MERGE ORDER MATTERS — do not merge this while the Pages publish root is the
> repository root.** The Pages project `familyosai` currently publishes from the
> repo root, so anything committed here becomes web-servable at
> familyosai.com/<path>. This record deliberately contains the retracted claims
> the live site still serves (`Runs fully offline` twice in `apex-root.html`), so
> merging it *before* the output directory is switched to `deploy/` would put
> banned claim text back on our own apex under `/deployed-state/...`. It is inert
> (and correct) after the redeploy, because `deploy/` is then the only published
> directory. Merge with, or after, the #195 redeploy — never before it.
>
> **On public exposure:** this repository is public, so these bytes are also
> readable on GitHub. That adds no marginal exposure — the identical bytes are
> already served publicly at `familyosai.com/` today, which is the very reason the
> record exists. They are a dated forensic capture explicitly labelled as
> superseded, not a published claim about the product.

**Why this exists.** AMS task #195 step 1: before the stale apex build is replaced,
capture the bytes that are *actually being served* so the broken state is on the
record. The apex root was published from a tree that exists in no commit, so the
only way to keep it is to save the served output itself.

**Captured** 2026-10-02 ~01:50 EDT from RecRoomRig (egress colo EWR), plain GETs,
no cache-busters. Read-only; nothing was deployed, purged, or changed.

## Files

| File | Bytes | sha256 | `Runs fully offline` |
|---|---|---|---|
| `apex-deploy-index.html` | 13592 | `bcaa297f7b8f130e1644b507c47a2a2dbd46c3dc1e5f1bcd0fd10946dfc7ef41` | 0 |
| `apex-privacy.html` | 5954 | `f753f1693473d2d080d30990415ec1eb210c1c3f49a829f2ba75838492316768` | 0 |
| `apex-root.html` | 12765 | `721fbae19bd1cb167ccc1f57a736b842bb472b60b975e7075036a61ca546b674` | 2 |
| `apex-terms.html` | 5660 | `6d80b2577f5aa87df5228e980edd5e88781d7a0b77be2ca6fa6bebde11a56700` | 0 |
| `pagesprod-deploy-index.html` | 13225 | `fa31dd15248287ce38c7336bc2cede9f14e3814c09de7e4195cb6872ada90b8f` | 0 |
| `pagesprod-root.html` | 12398 | `23b99ee4275a32888fd001ae6f36bd713dd9837f9e6afdff26d0edd4f772eec0` | 2 |

- `apex-*` — fetched from `https://familyosai.com` (the proxied zone).
- `pagesprod-*` — fetched from `https://familyosai-cma.pages.dev` (the Pages origin
  hostname, reached without the zone in front).

## What these bytes prove

1. **The apex root is the stale pre-fix landing page.** `apex-root.html` carries the
   retracted claim `Runs fully offline` twice, plus `lives in your house` and
   `on-device` — three phrases the repo's own claims guard
   (`tests/website-claims.test.ts`) bans.
2. **The served root matches no branch tip — it is blob `d5173b13`.** For the
   record, precisely: the served 12,398 B root is byte-identical to
   `deploy/index.html` at commit `3087f2d` and to the copy in the stash commit
   `351e831` (Chris's stash index "On main: stale index.html privacy-copy draft",
   2026-10-01 02:12) — i.e. the pre-`565e022` build. It is *not* on `origin/main`
   (`origin/main:deploy/index.html` is blob `a0f6d8a8` = 13,225 B =
   sha256 `fa31dd15…90b8`). The earlier note in #195 that the served bytes "match
   no git blob" was true only of the two commits compared at the time; the blob
   does exist, just not on `main`. Why it matters is unchanged: the live site
   still shows the retracted claims a month after the fix landed on `main`,
   because `main` was never republished.
3. **The homepage is visibly broken today, not merely stale.** It references
   relative assets — `assets/brand/familyos-logo-painted.png`,
   `assets/painted/backdrops/tudor-house-dusk.png`,
   `assets/brand/familyos-appicon.png` — and every one of them 404s at the apex,
   because the live root has no `/assets/`.
4. **Cloudflare Email Address Obfuscation rewrites the legal pages per response.**
   `/privacy/` and `/terms/` return the same 5,940 / 5,642 bytes but a *different*
   sha256 on every fetch: the zone rewrites each `mailto:` into
   `/cdn-cgi/l/email-protection#<random>` with a fresh random key. Do not treat
   digest drift on those two paths as origin instability; the pages are stable, the
   obfuscation is not. The Pages origin serves them without that rewriting, so use
   the `pagesprod-*` digests if a stable reference is needed.
5. **`README.md` and `.gitignore` are publicly served at the apex.** They are
   artifacts of publishing from the repository root rather than from `deploy/`.

## The fix this record is waiting on

Republish the Cloudflare Pages project `familyosai` with **output directory
`deploy/`** (not the repository root). `https://familyosai.com/deploy/` already
serves the corrected build — 13,225 B, sha256 `fa31dd15…90b8`, claims-clean,
relay disclosed, `/privacy/` and `/terms/` linked — so the content to publish is
already known and byte-verified. The Pages project has **no Git integration**
(commits to `main` since 2026-09-28 did not trigger a deploy), so publishing is a
manual step that needs a Cloudflare API token with **Pages:Edit** on account
`a9aeb517416233e71e776b29f8509955`.

No zone cache purge is required: the staleness sits in the Pages asset cache
(`cache-control: public, s-maxage=604800`), and a new deployment replaces those
assets. Purging *without* redeploying would make things worse — the Pages origin
also 404s `/privacy/`, so today's edge-cached legal pages would be replaced by
404s.
