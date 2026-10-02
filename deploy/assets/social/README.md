# deploy/assets/social

Social assets that ship **inside the publish root**.

## What belongs here

Images and copy that are actually linked from `deploy/index.html` — currently
the brand marks under `brand/` and the painted scenes under `painted/`.

## What does NOT belong here

- **`*.mp4`** — rendered video. Keep renders outside this directory entirely.
  `git check-ignore` will refuse them (see the root `.gitignore`).
- **`*.png` that are not referenced by the site** — Instagram carousels used to
  live here and were being served; they were moved out on 2026-10-02.

The reason is not tidiness. This directory is inside the publish root, so
`git add` here == `publish to the internet`. A binary that ships from here keeps
being served after the copy it illustrates has been corrected, and nothing in CI
can see what is painted on its pixels. See `../../SOCIAL-MEDIA-RENDERS.md`.

## The Instagram cards

`ig-*.png` were removed from the publish root on 2026-10-02. They are campaign
graphics for a channel that is not this website; they now live with the rest of
the renders (see `SOCIAL-MEDIA-RENDERS.md`). Recover any of them from git:

```sh
git show 169f809:deploy/assets/social/ig-cover.png > ig-cover.png
```
