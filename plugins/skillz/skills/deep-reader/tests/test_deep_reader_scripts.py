"""Run upstream's own regression suite for the deep-reader scripts.

scripts/self-test.sh builds its own fixtures in a temp directory and exits
non-zero if any check fails. Checks that need pdftotext or pandoc are skipped
by the suite itself when those tools are missing.
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@unittest.skipIf(shutil.which("bash") is None, "bash is required")
class SelfTest(unittest.TestCase):
    def test_self_test_passes(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPTS / "self-test.sh")],
            capture_output=True,
            text=True,
            timeout=300,
        )
        failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL")]
        self.assertEqual(
            result.returncode,
            0,
            "self-test.sh failed:\n" + "\n".join(failures or [result.stdout[-2000:], result.stderr[-2000:]]),
        )
        self.assertEqual(failures, [])
        self.assertIn(" passed, 0 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
