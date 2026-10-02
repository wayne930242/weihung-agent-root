"""A stand-in `npm` executable: `python3 fake_npm.py <npm arguments>`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from support.pi import fake_npm_install

fake_npm_install(sys.argv[1:])
