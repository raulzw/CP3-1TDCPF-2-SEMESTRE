"""Exercício 4.2 — Detecção de acessos anômalos com Isolation Forest."""
import numpy as np
from sklearn.ensemble import IsolationForest

# [hora_do_dia, tentativas_login, bytes_baixados]
acessos = np.array([
    [9, 1, 200], [10, 1, 500], [14, 2, 300], [11, 1, 250], [16, 1, 400],
    [3, 40, 900000],
    [10, 1, 350], [15, 2, 280],
    [2, 55, 800000],
])

# contamination = proporção estimada de anomalias nos dados
detector = IsolationForest(contamination=0.25, random_state=42)
resultados = detector.fit_predict(acessos)  # 1 = normal, -1 = anomalia

for i, (amostra, r) in enumerate(zip(acessos, resultados)):
    status = "ANOMALIA" if r == -1 else "Normal"
    print(f"Amostra {i}: {amostra.tolist()} -> {status}")

anomalias = [i for i, r in enumerate(resultados) if r == -1]
print(f"\nAnomalias detectadas: {anomalias}")
