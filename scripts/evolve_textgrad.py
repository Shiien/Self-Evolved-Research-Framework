#!/usr/bin/env python3
"""CLI entry point: run TextGrad-based TD-NL evolve-suggest backward pass.

Typical invocation at session-close (from evolve-suggest/SKILL.md):
    python scripts/evolve_textgrad.py --dry-run
    python scripts/evolve_textgrad.py --apply-proposal   # writes a PROPOSAL entry

Exit codes:
    0 = success (may or may not have produced a proposal)
    1 = no pending feedback (nothing to do)
    2 = parse / IO error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
TD_NL = SKILLS_ROOT / "td-nl"
FEEDBACK_LOG = TD_NL / "feedback-log.md"
SKILL_VALUES_DIR = TD_NL / "skill-values"
VALUE_FUNCTION = TD_NL / "value-function.md"

# allow running the script directly without installing the package
sys.path.insert(0, str(TD_NL))

from textgrad_backend import (  # noqa: E402
    USING_REAL_TEXTGRAD,
    ClaudeCodeCLIEngine,
    make_default_engine,
    run_backward,
    write_proposal,
)


def _summarize(results, engine_name: str = "none") -> dict:
    summary = {
        "backend": "textgrad" if USING_REAL_TEXTGRAD else "shim",
        "engine": engine_name,
        "sessions": [],
    }
    for r in results:
        s = {
            "session": r.session,
            "v_l_old": round(r.v_l_old, 3),
            "v_l_new": round(r.v_l_new, 3),
            "skills": {},
            "proposals": [],
        }
        for skill, agg in sorted(r.aggregates.items()):
            s["skills"][skill] = {
                "net_delta": agg.net_delta,
                "td_error": round(agg.td_error, 3),
                "strength": agg.strength,
                "V": round(agg.V, 3),
                "V_next": round(agg.V_next, 3),
                "confidence": agg.confidence,
            }
        for p in r.proposals:
            s["proposals"].append(
                {
                    "skill": p.skill,
                    "old_value": round(p.old_value, 3),
                    "new_value": round(p.new_value, 3),
                    "td_error": round(p.td_error, 3),
                    "strength": p.strength,
                }
            )
        summary["sessions"].append(s)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Run backward but do not modify feedback-log.md",
    )
    ap.add_argument(
        "--apply-proposal",
        action="store_true",
        help="Write PROPOSAL entry + move Pending->Processed in feedback-log.md",
    )
    ap.add_argument("--gamma", type=float, default=0.9)
    ap.add_argument("--json", action="store_true", help="Print JSON summary")
    ap.add_argument(
        "--no-engine",
        action="store_true",
        help="Disable the LLM engine; use deterministic shim (faster, offline).",
    )
    ap.add_argument(
        "--engine-model",
        default="haiku",
        help="Claude model for the Claude Code CLI engine (default: haiku).",
    )
    ap.add_argument(
        "--engine-timeout",
        type=float,
        default=120.0,
        help="Per-call timeout (sec) for the Claude Code CLI engine.",
    )
    # Optional path overrides so a harness run can operate on its own
    # sandboxed state. Defaults preserve the original hard-coded behavior.
    ap.add_argument("--feedback-log", type=Path, default=FEEDBACK_LOG)
    ap.add_argument("--skills-root", type=Path, default=SKILLS_ROOT)
    ap.add_argument("--skill-values-dir", type=Path, default=SKILL_VALUES_DIR)
    ap.add_argument("--value-function", type=Path, default=VALUE_FUNCTION)
    args = ap.parse_args(argv)

    feedback_log = args.feedback_log
    if not feedback_log.exists():
        print(f"[evolve-textgrad] missing {feedback_log}", file=sys.stderr)
        return 2

    if args.no_engine:
        engine = None
    else:
        engine = make_default_engine(
            model=args.engine_model, timeout=args.engine_timeout
        )

    try:
        results = run_backward(
            feedback_log=feedback_log,
            skills_root=args.skills_root,
            skill_values_dir=args.skill_values_dir,
            value_function_file=args.value_function,
            gamma=args.gamma,
            engine=engine,
        )
    except Exception as e:  # pragma: no cover
        print(f"[evolve-textgrad] backward failed: {e}", file=sys.stderr)
        return 2

    if not results:
        print("[evolve-textgrad] no pending feedback", file=sys.stderr)
        return 1

    if args.apply_proposal and not args.dry_run:
        block = write_proposal(feedback_log, results)
        if block is None:
            print("[evolve-textgrad] no proposal written (no hard-strength skills)")
        else:
            print("[evolve-textgrad] proposal written:")
            print(block)

    engine_name = "none"
    if engine is not None:
        engine_name = (
            "claude-code-cli"
            if isinstance(engine, ClaudeCodeCLIEngine)
            else type(engine).__name__
        )
    summary = _summarize(results, engine_name=engine_name)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(
            f"[evolve-textgrad] backend={summary['backend']} engine={summary['engine']}"
        )
        for s in summary["sessions"]:
            print(
                f"  session={s['session']} V^L {s['v_l_old']:.2f}->{s['v_l_new']:.2f} "
                f"skills={len(s['skills'])} proposals={len(s['proposals'])}"
            )
            for skill, d in s["skills"].items():
                print(
                    f"    {skill:<24} td={d['td_error']:+.2f} "
                    f"strength={d['strength']:<4} conf={d['confidence']}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
