"""Explicit development-only v11 raw-point/M4/native-event entry."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.track.native_v11 import main
if __name__ == "__main__":
    raise SystemExit(main())
