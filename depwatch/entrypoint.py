"""Package entrypoint — thin wrapper so `python -m depwatch` works."""

import sys
from depwatch.cli import main

if __name__ == "__main__":
    sys.exit(main())
