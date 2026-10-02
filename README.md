# familyosai-website

Source for **familyosai.com**.

## Layout

| Path | What it is | Published? |
|------|------------|-----------|
| `deploy/` | The site. This is the **publish root**. | yes |
| `scripts/` | Tooling (claim guard). Not built, not served. | no |
| everything else | Docs. | should be no — see below |

## Two rules that exist because we broke them

**1. `deploy/` is the publish root — nothing else is.**

The Cloudflare Pages project was originally set to publish the *repository root*,
which served `README.md` and `.gitignore` at `https://familyosai.com/` for days
(2026-10-02, recorded in `deployed-state/2026-10-02-apex/` on the
`deployed-state/apex-2026-10-02` branch). Until the project's `destination_dir`
is set to `deploy/`, assume every file in this repo is world-readable and keep
household details and internal notes out of it.

**2. Rendered media does not live in the publish root.**

The `.mp4` and `.png` under `deploy/assets/social/` were exported by hand and
committed by hand. Binary files cannot be reviewed in a diff, so they drift out
of sync with the copy that generated them — and then the *server* keeps serving
the retracted caption long after the HTML was fixed. That is exactly what
happened on 2026-10-02: a video that asserted, on screen, that the AI is inside
your house was still publicly served at
`/deploy/assets/social/shorts/familyos-explainer.mp4` while the landing page had
already struck the same claim. See `SOCIAL-MEDIA-RENDERS.md`.

## Before you push

```sh
python3 scripts/check-published-banned-claims.py
```

It scans the tree (and, with `--url`, the live apex) for claims the product does
not implement. The canonical banned list is `tests/website-claims.test.ts` in the
`familyos-app` repo; this is the website-side mirror of it.
