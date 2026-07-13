"""Experiment modules. Each module exposes two explicit functions:

    execute(params: dict, run: RunDir) -> dict      # raw results
    evaluate(params: dict, run: RunDir, contract: Contract) -> dict

EXPERIMENTS is a plain dict — add new experiments here explicitly.
"""
from . import ttt_cycle

EXPERIMENTS = {
    "ttt_cycle": ttt_cycle,
}
