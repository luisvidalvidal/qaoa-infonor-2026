"""Reconstruye los coeficientes desde el CSV entregado, sin duplicar los datos."""
import csv
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "data/input_output_2016.csv").open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
SECTORS = [row[0] for row in rows[1:]]
if rows[0][1:-1] != SECTORS:
    raise ValueError("El orden de filas y columnas debe coincidir")
Z = np.array([[float(v) for v in row[1:-1]] for row in rows[1:]])
X = np.array([float(row[-1]) for row in rows[1:]])
if Z.shape != (18,18) or not np.isfinite(Z).all() or not np.isfinite(X).all() or (Z < 0).any() or (X <= 0).any():
    raise ValueError("MIP inválida")
A = Z / X[np.newaxis, :]
L = np.linalg.inv(np.eye(18) - A)
back = L.sum(axis=0); forward = L.sum(axis=1)
back_n = back / back.mean(); forward_n = forward / forward.mean()
score = 0.5 * (back_n + forward_n)
W = (L + L.T) / 2
np.fill_diagonal(W, 0)
W = W / W.max()

if __name__ == "__main__":
    order = np.argsort(-score)
    print("spectral radius", max(abs(np.linalg.eigvals(A))))
    for i in order:
        print(i+1, SECTORS[i], score[i], back_n[i], forward_n[i])
