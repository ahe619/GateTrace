"""Rebuild labels and the cached reference score through the frozen CPU CLI."""

def main(argv=None):
    from scripts.resource_entry import run
    return run("reproduce.py", argv)

