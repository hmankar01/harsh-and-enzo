"""Harsh & Enzo's voice. Harsh is the field agent (search + scrape); Enzo is his
detective dog — the analyst with the nose. Every pipeline event gets narrated
through one of them. The `agent` field also drives the frontend's animated scene."""

import random

HARSH_WARMUP = [
    "Harsh clips on Enzo's tactical collar. Mission is a go.",
    "Harsh straightens his collar. Enzo stretches. \"Right. Let's find your unicorn.\"",
    "Harsh boots up the field scanner. Enzo's ears are already up.",
]

ENZO_PLANNING = [
    "Enzo sniffs the criteria form thoroughly. Twice. He has the scent now.",
    "Enzo circles the brief three times before committing it to memory. Protocol.",
    "Harsh reads the checkboxes aloud; Enzo memorizes the scent profile.",
]

HARSH_SEARCHING = {
    86400: "Harsh sweeps everything posted in the last 24 hours…",
    172800: "Harsh widens the sweep to the last 48 hours…",
    259200: "Harsh goes back 72 hours. Nothing escapes the sweep.",
}

ENZO_RELAXING = [
    "Zero hits. Enzo tilts his head at the radar. \"Too niche,\" Harsh agrees — dropping the domain filter.",
    "Harsh loosens the net further. Enzo paws at the broadest role terms. Someone's out there.",
]

HARSH_FOUND = [
    "Harsh comes back waving {n} job links. Enzo's tail starts a slow warm-up wag.",
    "\"{n} postings on the scanner. Enzo — nose time.\"",
    "{n} postings acquired. Enzo does a full-body shake to prepare.",
]

HARSH_FETCHING = [
    "Harsh pulls up job #{i} of {total}…",
    "Harsh slides posting #{i}/{total} under Enzo's nose.",
    "Job #{i} of {total} — Harsh has it on screen.",
]

ENZO_READING = [
    "Enzo presses his nose to posting #{i}… sniff… sniff…",
    "Enzo runs job #{i} through the sniff test. No mercy.",
    "Enzo reads posting #{i} twice. He always sniffs twice.",
]

ENZO_REJECT = [
    "Enzo growls softly and steps back: {reason}",
    "Enzo buries it in the backyard. {reason}",
    "Ears down. Not the one — {reason}",
]

ENZO_MATCH = [
    "Enzo's tail goes nuclear: {title} at {company}!",
    "WOOF. Full point, tail up: {title} at {company} smells exactly right.",
    "Enzo sits, paw raised, extremely proud: {title} at {company} clears every bar.",
]

HARSH_SCRAPE_FAIL = [
    "That posting slammed the door on Harsh. Enzo barks once at it; they move on.",
    "Posting played hard to get. Harsh shrugs, Enzo shakes it off. Next.",
]

RANKING = [
    "Enzo arranges the winners by freshness, sniffing each one twice more…",
    "Final sort: Harsh lays the matches on the desk; Enzo noses them into order, newest first.",
]

IDLE_QUIPS = [
    "Enzo insists the collar is tactical, not decorative.",
    "Harsh does the paperwork. Enzo does the sniffing. It works.",
    "Enzo has never once accepted a treat from a bad job posting.",
    "Fun fact: Enzo can smell 'fast-paced environment' from three tabs away.",
    "Enzo's sniff test has rules. The rules have rules.",
]

LIMIT_MESSAGES = [
    "Whoa there, speed-recruiter! Harsh & Enzo only run two missions per visitor, ever — "
    "the trench coat's on the rack and Enzo is asleep in his basket. Want the full, "
    "unlimited, caffeinated version of this duo? That's a conversation with the human Harsh.",
    "Two searches deep and still hungry? That's the spirit. Sadly Enzo's nose is officially "
    "off duty, permanently — but the guy who built us never runs out. Ping him and he'll "
    "run the real thing for you.",
    "Mission limit reached! Harsh has clocked out and Enzo got a chew toy for excellent "
    "service. The good news: their creator works unlimited hours and answers messages "
    "suspiciously fast.",
]


def pick(pool: list[str], **kwargs) -> str:
    return random.choice(pool).format(**kwargs)
