"""Portable detector entry; imports only the CLI until explicit execution."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.detect.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
