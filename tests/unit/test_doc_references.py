"""Every tracker ID cited in docs and experiment code must resolve (session-17 defect class D21).

Five times in one session an ID was written into a document before the issue existed. Each
was caught by hand. This makes the class structurally impossible to merge where filigree runs.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CITED = re.compile(r"simic-[0-9a-f]{10}")


def cited_ids() -> set[str]:
    files = [
        REPO / "AGENTS.md",
        REPO / "README.md",
        *(REPO / "docs").rglob("*.md"),
        *(REPO / "docs").rglob("*.json"),
        *(REPO / "experiments").glob("*.py"),
    ]
    return {match for path in files if path.is_file() for match in CITED.findall(path.read_text(errors="replace"))}


@pytest.mark.skipif(shutil.which("filigree") is None, reason="filigree CLI not installed; the guard runs where the tracker does")
def test_every_cited_tracker_id_resolves() -> None:
    unresolved = sorted(
        i for i in cited_ids() if subprocess.run(["filigree", "show", i], cwd=REPO, capture_output=True, check=False).returncode != 0
    )
    assert not unresolved, f"tracker IDs cited but not found: {unresolved}"
