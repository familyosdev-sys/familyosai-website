#!/usr/bin/env python3
"""Generate Week 6 (Sep 22-28) Instagram cards for FamilyOS — brand palette.
Cards: ig-task-initiation.png, ig-body-double.png, ig-transition-cost.png
"""
from PIL import Image, ImageDraw, ImageFont
import os

W = H = 1080
BG = (21, 14, 8)        # --pg   #150e08
INK = (246, 231, 198)   # --ink  #f6e7c6
SUB = (203, 185, 148)   # --sub  #cbb994
ACC = (244, 201, 93)    # --acc  #f4c95d
LINE = (184, 145, 47)   # border gold (drawn at alpha via RGBA overlay)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

OUT = os.path.dirname(os.path.abspath(__file__))


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(path, kicker, headline, support, footnote):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # subtle warm vignette: slightly lighter center wash
    wash = Image.new("L", (W, H), 0)
    wd = ImageDraw.Draw(wash)
    wd.ellipse([140, 160, W - 140, H - 140], fill=14)
    warm = Image.new("RGB", (W, H), (48, 33, 16))
    img = Image.composite(warm, img, wash)
    d = ImageDraw.Draw(img)

    # hairline gold frame, rounded
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([44, 44, W - 44, H - 44], radius=36,
                         outline=(LINE[0], LINE[1], LINE[2], 102), width=3)
    od.rounded_rectangle([56, 56, W - 56, H - 56], radius=30,
                         outline=(LINE[0], LINE[1], LINE[2], 46), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    f_kick = ImageFont.truetype(SANS_B, 30)
    f_head = ImageFont.truetype(SERIF_B, 86)
    f_sub = ImageFont.truetype(SERIF_R, 44)
    f_foot = ImageFont.truetype(SANS_B, 30)
    f_foot2 = ImageFont.truetype(SANS, 26)

    max_w = W - 240

    # kicker (letterspaced small caps look)
    ky = 170
    kick_txt = kicker.upper()
    d.text((120, ky), kick_txt, font=f_kick, fill=ACC)
    kw = d.textlength(kick_txt, font=f_kick)
    d.line([120, ky + 48, 120 + kw, ky + 48], fill=(LINE[0], LINE[1], LINE[2]), width=2)

    # headline block centered vertically-ish
    hlines = wrap(d, headline, f_head, max_w)
    slines = wrap(d, support, f_sub, max_w)
    hh = sum(d.textbbox((0, 0), l, font=f_head)[3] - d.textbbox((0, 0), l, font=f_head)[1] + 26 for l in hlines)
    sh = sum(64 for _ in slines)
    block_h = hh + 40 + sh
    y = (H - block_h) // 2 + 30

    for l in hlines:
        d.text((120, y), l, font=f_head, fill=INK)
        bb = d.textbbox((0, 0), l, font=f_head)
        y += (bb[3] - bb[1]) + 26
    y += 40
    for l in slines:
        d.text((120, y), l, font=f_sub, fill=SUB)
        y += 64

    # footnote
    d.text((120, H - 130), "familyosai.com", font=f_foot, fill=ACC)
    d.text((120, H - 92), footnote, font=f_foot2, fill=(150, 130, 100))

    img.save(path, "PNG")
    print("wrote", path, img.size)


make_card(
    os.path.join(OUT, "ig-task-initiation.png"),
    "The friction, named",
    "Your kid isn't lazy. They can't start.",
    "Task initiation is an executive function — a process, not a character trait. Some kids need a scaffold, not a nag.",
    "One quest at a time · photo proof per step",
)

make_card(
    os.path.join(OUT, "ig-body-double.png"),
    "Executable technique · no. 2",
    "The body double: how presence helps a stuck kid start",
    "Sit nearby. Do your own task. Say: \u201cI'm just here.\u201d Your presence is the scaffold. Works today with a chair and a book.",
    "Useful with or without the app",
)

make_card(
    os.path.join(OUT, "ig-transition-cost.png"),
    "The friction, named",
    "The transition is the hard part. Not the chore.",
    "Warn before. Make the next step concrete. Let the current task finish. Interruption is the most expensive transition.",
    "The brain carries momentum — work with it",
)

# ---- X character counts ----
x_posts = {
    "6.1 X text (Mon)": (
        "Your kid isn't lazy. They can't start.\n\n"
        "Task initiation is an executive function — a neurological process, not a character trait. "
        "Some brains do it automatically. Others need a scaffold. Not a nag. A scaffold.\n\n"
        "The difference between \"go clean your room\" and \"pick up the three things on your bed, "
        "then come back\" isn't lower standards. It's breaking the start barrier.\n\n"
        "familyosai.com"
    ),
    "6.2 X condensed (Wed)": (
        "When your kid is stuck on a chore, sit nearby. Not hovering. Not supervising. Just present.\n\n"
        "It's called body doubling — one of the most effective, least talked about executive-function strategies. "
        "Your presence is the scaffold. Works today with a chair and a book.\n\n"
        "familyosai.com"
    ),
    "6.3 T1": "Every parent knows the chore is easy. The transition to the chore is hard. 🧵",
    "6.3 T2": "What we don't count: the transition cost. The cognitive tax of stopping one thing, switching contexts, and starting another. For neurodivergent kids, this tax is 5x higher.",
    "6.3 T3": "A neurotypical kid hears \"time to do dishes\" and the transition takes 30 seconds. Grumble, walk to kitchen, start.",
    "6.3 T4": "An ADHD kid hears \"time to do dishes\" and the transition is a wall. The current activity has momentum. The new activity has none. The brain can't shift gears without friction.",
    "6.3 T5": "Parents read this as defiance. It's not. It's the brain working as designed — just designed for a different kind of environment. One where transitions happen at nature's pace, not a clock's.",
    "6.3 T6": "What helps:\n\n1. Warn before the transition (\"5 minutes until dishes\")\n2. Make the next task concrete (\"put the forks in the dishwasher\" — not \"do the dishes\")\n3. Let them finish the current task if possible. Interruption is the most expensive transition.",
    "6.3 T7": "FamilyOS does all three: 5-minute warnings, step-by-step task breakdowns, and a routine that respects the current activity before signaling the next one.\n\nThe app carries the transition so you don't have to break momentum.\n\nfamilyosai.com",
}
print("\n--- X character counts (limit 280) ---")
for k, v in x_posts.items():
    n = len(v)
    flag = "OK" if n <= 280 else "OVER"
    print(f"{k}: {n} {flag}")