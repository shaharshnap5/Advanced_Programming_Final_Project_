from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["src", "tests", "scripts"]


def run_step(command: list[str]) -> int:
    print(f"\n> {' '.join(command)}")
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


def main() -> int:
    fix_mode = "--fix" in sys.argv

    if fix_mode:
        code = run_step([sys.executable, "-m", "black", *TARGETS])
        if code != 0:
            return code

    lint_code = run_step([sys.executable, "-m", "flake8", *TARGETS])
    if lint_code == 0:
        print("\nLint checks passed successfully ✅")
    return lint_code


if __name__ == "__main__":
    raise SystemExit(main())
