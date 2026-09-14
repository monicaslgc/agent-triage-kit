import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentops import runbook


def test_match_picks_the_highest_scoring_issue():
    issue = runbook.match("Getting 401 unauthorized, token expired")
    assert issue is not None
    assert "auth" in issue.diagnosis.lower() or "credential" in issue.diagnosis.lower()


def test_match_returns_none_for_unrelated_text():
    assert runbook.match("The coffee machine is broken") is None
