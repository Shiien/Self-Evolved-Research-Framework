"""Regression: grade_game must reproduce the gradings recorded in the
historical cycle-003 artifacts (scientific invariance of the grading path)."""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from tic_tac_toe.arena import GameRecord, MoveRecord, grade_game  # noqa: E402

GAMES = REPO_ROOT / "experiments/tic_tac_toe/history/cycle-003/games-selfplay.jsonl"


@pytest.mark.skipif(not GAMES.exists(), reason="historical artifact missing")
def test_cycle003_gradings_reproduce():
    checked = 0
    for line in GAMES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        rec = GameRecord(
            roles=d["roles"],
            moves=[
                MoveRecord(
                    symbol=m["symbol"], cell=m["cell"], raw=m.get("raw", ""),
                    retries=m.get("retries", 0), board_after=m.get("board_after", ""),
                )
                for m in d["moves"]
            ],
            winner=d["winner"],
            terminal=d["terminal"],
            forfeit_side=d.get("forfeit_side"),
            forfeit_reason=d.get("forfeit_reason"),
        )
        got = grade_game(rec)
        want = d["grading"]
        for key in ("X_moves", "O_moves", "X_mistakes", "O_mistakes"):
            assert got[key] == want[key], f"game {d.get('game_idx')}: {key}"
        checked += 1
    assert checked > 0
