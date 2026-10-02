# Social media renders — where they live and why

**Renders are not in git. The scripts that make them are.**

## What happened (2026-10-02)

`deploy/assets/social/shorts/familyos-explainer.mp4` was publicly served at
`https://familyosai.com/deploy/assets/social/shorts/familyos-explainer.mp4`. At
about 0:36 its caption read:

> The AI lives in your house. Literally.
> Local-first. Your data stays on the device in your house.
> We literally cannot see it.

Every one of those claims is on the banned list in `familyos-app`
`tests/website-claims.test.ts`, and the landing page had already struck the same
sentence in HTML. The HTML fix did not touch the video, because the video is a
*binary in the publish root* — nothing reads it, nothing reviews it, and no test
compares it to the copy. The file was still being served hours after #195
redeployed the corrected page.

Same class, same commit (`169f809`, 2026-09-12), three more files:

| File | On-screen claim | Frame |
|------|----------------|-------|
| `familyos-explainer.mp4` | "The AI lives in your house. Literally." / "We literally cannot see it." | ~0:42–0:48 |
| `short3-local-first.mp4` | "...stays on the device in your house. We literally cannot see it." + "Local-first" | ~0:05–0:09 |
| `walkthrough-familyosai.mp4` | "The AI lives in your house. Literally." / "Pictures of your children never touch a cloud" | ~0:16–0:19 |

(`short1/2/4/5/6` are clean — verified by OCR of every frame, not by reading the
scripts that generated them.)

## The rule

1. **Source scripts** (`*.py`) live in git, under `deploy/assets/social/shorts/`.
   They are reviewable and they are what you regenerate from.
2. **Renders** (`*.mp4`, large `*.png`) do **not** live in git and do **not** live
   under `deploy/`. Keep them outside the publish root — e.g.
   `~/artifacts/familyos-social/` — and upload them to the platform that hosts
   them (Instagram, YouTube, the campaign folder). If a render ever needs to be
   *served* from our own domain, that is a deliberate decision that comes with a
   caption review, not a side effect of `git add`.
3. `.gitignore` now refuses `deploy/assets/social/**/*.mp4` so rule 2 is not
   merely a convention.

## Before you regenerate

Re-read the scripts against the banned list, then render, then **screenshot the
frames with text** and check them. The failure mode here was not a bad script —
it was a good script whose output nobody looked at.

```sh
# the script that shipped the banned caption is now corrected in Scene5
python3 deploy/assets/social/shorts/familyos_explainer.py

# spot-check any render before uploading it anywhere
ffmpeg -i render.mp4 -vf fps=1 /tmp/frames/%03d.jpg
for f in /tmp/frames/*.jpg; do tesseract "$f" - --psm 6; done | grep -in "your house\|cannot see\|local-first"
```

An empty grep is the passing result.
