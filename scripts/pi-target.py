#!/usr/bin/env python3
"""Install and remove the repository-owned Pi configuration; the logic lives in scripts/pi_root/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pi_root.cli import main

if __name__ == "__main__":
    main()
