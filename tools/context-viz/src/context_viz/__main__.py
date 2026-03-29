"""Allow running as `python -m context_viz`."""

import sys

from .cli import main

sys.exit(main())
