"""Generate confirmation commands; never execute scientific stages."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.confirm.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
