#!/usr/bin/env python3
"""Candidate variants for 6.1 X post; pick longest <=280."""
import itertools

CANDS = {
    "A": (
        "Your kid isn't lazy. They can't start.\n\n"
        "Task initiation is an executive function, not a character trait. Some brains do it automatically. "
        "Others need a scaffold — not a nag.\n\n"
        "\"Three things off your bed\" beats \"clean your room.\" Not lower standards. A lower wall.\n\n"
        "familyosai.com"
    ),
    "B": (
        "Your kid isn't lazy. They can't start.\n\n"
        "Task initiation is an executive function, not a character trait. Some brains do it automatically. "
        "Others need a scaffold — not a nag.\n\n"
        "\"Three things off your bed\" beats \"clean your room.\" That's not lower standards. It's breaking the start barrier.\n\n"
        "familyosai.com"
    ),
    "C": (
        "Your kid isn't lazy. They can't start.\n\n"
        "Task initiation is an executive function, not a character trait. Some brains do it automatically. "
        "Others need a scaffold, not a nag.\n\n"
        "\"Three things off your bed\" beats \"clean your room.\" Not lower standards — a lower wall.\n\n"
        "familyosai.com"
    ),
}
for k, v in CANDS.items():
    print(f"variant {k}: {len(v)} chars {'OK' if len(v) <= 280 else 'OVER'}")

# 6.2 recheck
p62 = (
    "When your kid is stuck, sit nearby. Not hovering. Not supervising. Just present.\n\n"
    "It's called body doubling — one of the most effective, least discussed "
    "executive-function strategies. Your presence is the scaffold. "
    "A chair and a book are all it takes.\n\nfamilyosai.com"
)
print(f"6.2 final: {len(p62)} {'OK' if len(p62) <= 280 else 'OVER'}")

t = {
    "6.3 T1": "Every parent knows the chore is easy. The transition to the chore is hard. 🧵",
    "6.3 T2": "What we don't count: the transition cost. The cognitive tax of stopping one thing, switching contexts, and starting another. For neurodivergent kids, this tax is 5x higher.",
    "6.3 T3": "A neurotypical kid hears \"time to do dishes\" and the transition takes 30 seconds. Grumble, walk to kitchen, start.",
    "6.3 T4": "An ADHD kid hears \"time to do dishes\" and the transition is a wall. The current activity has momentum. The new activity has none. The brain can't shift gears without friction.",
    "6.3 T5": "Parents read this as defiance. It's not. It's the brain working as designed — just designed for a different kind of environment. One where transitions happen at nature's pace, not a clock's.",
    "6.3 T6": "What helps:\n\n1. Warn before the transition (\"5 minutes until dishes\")\n2. Make the next task concrete (\"put the forks in the dishwasher\" — not \"do the dishes\")\n3. Let them finish the current task if possible. Interruption is the most expensive transition.",
    "6.3 T7": "FamilyOS does all three: 5-minute warnings, step-by-step task breakdowns, and a routine that respects the current activity before signaling the next one.\n\nThe app carries the transition so you don't have to break momentum.\n\nfamilyosai.com",
}
for k, v in t.items():
    print(f"{k}: {len(v)} {'OK' if len(v) <= 280 else 'OVER'}")