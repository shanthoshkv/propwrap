"""Allow ``python -m propwrap`` as well as the ``propwrap`` console script."""

from __future__ import annotations

import sys

from propwrap.cli import main

if __name__ == "__main__":
    sys.exit(main())
