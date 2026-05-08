"""Allows running depwatch as `python -m depwatch`."""

import sys
from depwatch.cli import main

sys.exit(main())
