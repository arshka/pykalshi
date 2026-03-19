import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sync_generation_is_up_to_date():
    """Assert _sync/ matches what the generator would produce."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "generate_sync.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"_sync/ is out of date. Run: python scripts/generate_sync.py --write\n"
        f"{result.stdout}\n{result.stderr}"
    )
