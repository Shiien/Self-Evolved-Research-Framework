"""Minimal research harness.

One canonical path for every experiment:

    resolved config -> setup -> execute -> evaluate -> artifacts in runs/<id>/

Layers:
    contract.py     experiment contract (required before any run)
    rundir.py       self-contained run directory
    experiments/    one module per experiment: execute() + evaluate()
    cli.py          setup | smoke-test | run | evaluate | resume | compare | loop
    loop.py         optional research loop (state machine over EXPERIMENTS.json)
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = REPO_ROOT / "runs"
