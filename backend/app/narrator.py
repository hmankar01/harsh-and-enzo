"""Harsh & Enzo's voice. Harsh is the field scout (search + scrape), Enzo is the
analyst (read + judge). Every pipeline event gets narrated through one of them."""

import random

HARSH_WARMUP = [
    "Harsh cracks his knuckles and opens seventeen LinkedIn tabs. Professionally.",
    "Harsh straightens his collar. \"Right. Let's go find your unicorn.\"",
    "Harsh boots up the radar. It makes a satisfying *ping*.",
]

ENZO_PLANNING = [
    "Enzo is translating your checkboxes into a boolean incantation…",
    "Enzo sharpens a pencil he doesn't need and drafts the search strategy.",
    "Enzo mutters \"AND… OR… NOT…\" like it's poetry. It kind of is.",
]

HARSH_SEARCHING = {
    86400: "Harsh is sweeping everything posted in the last 24 hours…",
    172800: "Harsh widens the sweep to the last 48 hours…",
    259200: "Harsh goes back 72 hours. Nothing escapes the sweep.",
}

ENZO_RELAXING = [
    "Enzo squints at zero results. \"Too niche. Dropping the domain filter — round two.\"",
    "Enzo loosens the net further. \"Broad strokes now. Someone's out there.\"",
]

HARSH_FOUND = [
    "Harsh comes back waving {n} job links like lottery tickets.",
    "Harsh: \"Got {n} candidates on the radar. Enzo, you're up.\"",
    "{n} postings acquired. Harsh does a small, dignified fist pump.",
]

HARSH_FETCHING = [
    "Harsh is pulling up job #{i} of {total}…",
    "Harsh tiptoes into posting #{i}/{total} and copies everything down.",
    "Job #{i} of {total} — Harsh has eyes on it.",
]

ENZO_READING = [
    "Enzo is reading job #{i}… adjusting his glasses…",
    "Enzo runs job #{i} through the rubric. No mercy.",
    "Enzo reads posting #{i} twice. He always reads twice.",
]

ENZO_REJECT = [
    "Enzo stamps it: NOPE — {reason}",
    "Enzo shakes his head. {reason}",
    "Rejected. Enzo's note: {reason}",
]

ENZO_MATCH = [
    "Enzo slams the APPROVED stamp: {title} at {company}!",
    "Match! Enzo circles {title} at {company} in green ink.",
    "Enzo looks up, actually smiling: {title} at {company} clears every bar.",
]

HARSH_SCRAPE_FAIL = [
    "Harsh got a door slammed in his face on that one. Moving on.",
    "That posting played hard to get. Harsh shrugs and moves to the next.",
]

RANKING = [
    "Enzo lays the matches on the desk and ranks them by freshness…",
    "Final sort: Enzo arranges the winners, newest first.",
]

IDLE_QUIPS = [
    "Harsh insists the trench coat helps him scrape faster.",
    "Enzo alphabetizes his rejection stamps while he waits.",
    "Fun fact: Enzo has never once said \"culture fit\" unironically.",
    "Harsh once found a job posting from the future. They don't talk about it.",
    "Enzo's rubric has rules. The rules have rules.",
]

LIMIT_MESSAGES = [
    "Whoa there, speed-recruiter! Harsh & Enzo run exactly two missions per day — "
    "after that the trench coats go back on the rack. Want the full, unlimited, "
    "caffeinated version of this duo? That's a conversation with the human Harsh.",
    "Two searches deep and still hungry? That's the spirit. Sadly Enzo's rubber "
    "stamp is out of ink for today — but the guy who built us restocks it. "
    "Ping him and he'll run the real thing for you.",
    "Mission limit reached! Harsh has clocked out and Enzo is doing paperwork. "
    "The good news: their creator works unlimited hours and answers messages "
    "suspiciously fast.",
]


def pick(pool: list[str], **kwargs) -> str:
    return random.choice(pool).format(**kwargs)
