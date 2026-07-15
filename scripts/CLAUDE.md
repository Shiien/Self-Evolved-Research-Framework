# Utility Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `citation_fetch.py` | Fetch BibTeX from DBLP/CrossRef | `python citation_fetch.py "Title" [--authors "Name"] [--batch file.txt]` |
| `notify.py` | Fail-open webhook notifications | `python notify.py "Message" [--level info\|warning\|error\|success]` |
| `skill_analyzer.py` | Parse session logs for usage stats | `python skill_analyzer.py` |
| `pack.sh` | Pack framework as clean template for new projects | `bash scripts/pack.sh [VERSION]` |
| `install-skills.sh` | Install runtime-specific single-model manifests for Claude (`.claude/skills`) or Codex (`.agents/skills`) | Claude: `bash scripts/install-skills.sh [--runtime claude] [--link] [--force] [--user] [--only PATTERNS] [--exclude PATTERNS]`<br>Codex: `bash scripts/install-skills.sh --runtime codex [--force] [--only PATTERNS] [--exclude PATTERNS]` |

## Dependencies

`pip install -r requirements.txt` — mainly PyYAML. No heavy ML dependencies.

## Environment Variables

- `SER_NOTIFY_WEBHOOK_URL` — webhook URL for notify.py (optional, fail-open)
