from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agents_protocol_exposes_v6_state_owners_and_contract_gate():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for required in (
        ".agents/skills/",
        "RESEARCH_STATE.md",
        "EXPERIMENTS.json",
        "IDEA_BACKLOG.md",
        "runs/",
        "contract",
        "evaluation",
    ):
        assert required in text


def test_agents_protocol_remains_codex_native():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for forbidden in ("/codex:", "mcp__codex__codex", ".claude/skills"):
        assert forbidden not in text
