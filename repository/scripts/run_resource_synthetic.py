"""Run resource adapter and frozen inspection tests using synthetic inputs only."""
from pathlib import Path
import subprocess
import sys
from resource_entry import REPOSITORY, cpu_environment

def main():
    if sys.flags.optimize:
        raise SystemExit("Run without -O")
    commands = (
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_resource_adapters.py", "-v"],
        [sys.executable, "-B", str(REPOSITORY / "core/tests/test_inspection_synthetic.py")],
    )
    for command in commands:
        result = subprocess.run(command, cwd=REPOSITORY, env=cpu_environment(), check=False)
        if result.returncode:
            return result.returncode
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

