"""Inspect per-event support through the frozen CPU CLI."""

def main(argv=None):
    from scripts.resource_entry import run
    return run("inspect_event.py", argv)

