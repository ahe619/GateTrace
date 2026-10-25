"""Score MOTChallenge tracks or run the bundled panel regression on CPU."""

def main(argv=None):
    from scripts.resource_entry import run
    return run("score_tracker.py", argv)

