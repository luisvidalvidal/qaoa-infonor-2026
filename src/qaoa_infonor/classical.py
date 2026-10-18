"""Auditoría reproducible de controles clásicos y penalización del artículo."""
import json
from pathlib import Path

import numpy as np

from .experiment import ALPHA, PENALTY, SECTORS, instance


def greedy_audit(inst):
    selected = []
    steps = []
    current = 0.0
    for step in range(inst["k"]):
        candidates = []
        for j in range(inst["n"]):
            if j in selected:
                continue
            trial = selected + [j]
            x = np.zeros(inst["n"])
            x[trial] = 1.0
            value = float(inst["s"] @ x + inst["alpha"] * np.einsum(
                "i,ij,j", x, np.triu(inst["w"], 1), x
            ))
            candidates.append((value - current, value, j))
        gain, value, chosen = max(candidates, key=lambda row: (row[0], -row[2]))
        selected.append(chosen)
        current = value
        steps.append({
            "step": step + 1,
            "sector": SECTORS[int(inst["idx"][chosen])],
            "marginal_gain": gain,
            "cumulative_score": value,
        })
    state = np.zeros(inst["n"])
    state[selected] = 1.0
    state_id = int(sum(int(bit) << i for i, bit in enumerate(state)))
    return {
        "selected": [SECTORS[int(inst["idx"][j])] for j in selected],
        "steps": steps,
        "final_score": current,
        "state_id": state_id,
        "matches_exact": bool(inst["opt"][state_id]),
    }


def penalty_audit(inst):
    distance = (inst["states"].sum(axis=1) - inst["k"]) ** 2
    infeasible = ~inst["feasible"]
    thresholds = (inst["F"][infeasible] - inst["fmax"]) / distance[infeasible]
    threshold = float(max(0.0, thresholds.max()))
    best_feasible_cost = -float(inst["fmax"])
    best_infeasible_cost = float(inst["C"][infeasible].min())
    return {
        "strict_threshold": threshold,
        "penalty_used": inst["penalty"],
        "cost_gap_best_infeasible_minus_optimum": best_infeasible_cost - best_feasible_cost,
    }


def main():
    rows = []
    for n in (4, 6, 8):
        inst = instance(n)
        rows.append({
            "n": n,
            "k": inst["k"],
            "greedy": greedy_audit(inst),
            "penalty": penalty_audit(inst),
        })
    path = Path(__file__).resolve().parents[2] / "outputs/classical_audit.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
