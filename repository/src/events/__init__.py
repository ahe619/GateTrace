"""Derive events and score MOTChallenge tracks through the frozen CPU CLI."""

def main(argv=None):
    from scripts.resource_entry import run
    return run("score_tracker.py", argv)

