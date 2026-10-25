"""Explicit native-final-event identity scoring; no event redecoding or inference."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.score.native_v11 import main
if __name__ == "__main__":
    raise SystemExit(main())
