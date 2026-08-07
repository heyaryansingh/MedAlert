"""Make the backend importable however the suite is invoked.

Some test modules import ``utils.auth_security`` and others import
``backend.utils.adherence_analytics``. With pytest's default import mode only
the test file's own directory lands on ``sys.path``, so the first style broke
collection for the whole suite unless pytest happened to be run from inside
``backend/``. Put both roots on the path so either spelling resolves from any
working directory.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

for root in (BACKEND_DIR.parent, BACKEND_DIR):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
