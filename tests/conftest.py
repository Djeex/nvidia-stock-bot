import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)

# app/*.py open their JSON config files with plain relative paths, so the
# process cwd must be the directory the app modules live in — matches how
# the Dockerfile runs them (WORKDIR /app).
_APP_DIR = os.path.join(_REPO_ROOT, "app")
if not os.path.isfile(os.path.join(_APP_DIR, "gpu_checker.py")):
    _APP_DIR = _REPO_ROOT  # container test stage: code copied flat next to tests/

if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

os.chdir(_APP_DIR)
