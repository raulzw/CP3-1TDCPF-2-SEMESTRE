"""Exercício 4.1 — Classificador de phishing com Random Forest."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split

# Features: [qtd_links, tem_anexo, urgencia_no_assunto, dominio_suspeito, erros_gramaticais]
X = np.array([
    [1, 0, 0, 0, 0], [0, 0, 0, 0, 1], [2, 1, 0, 0, 0], [1, 0, 0, 0, 0],
    [8, 1, 1, 1, 5], [12, 0, 1, 1, 8], [6, 1, 1, 1, 3], [10, 1, 1, 1, 6],
    [0, 0, 0, 0, 0], [15, 1, 1, 1, 9],
])
y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 0, 1])  # 0=legítimo, 1=phishing

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)
prev = modelo.predict(X_test)

print(f"Acurácia: {accuracy_score(y_test, prev):.2f}")
print(f"Precisão: {precision_score(y_test, prev, zero_division=0):.2f}")
print(f"Recall:   {recall_score(y_test, prev, zero_division=0):.2f}")
print(f"F1:       {f1_score(y_test, prev, zero_division=0):.2f}")
print(classification_report(y_test, prev, target_names=["legitimo", "phishing"], zero_division=0))

novo = [[11, 1, 1, 1, 7]]
rotulo = "Phishing" if modelo.predict(novo)[0] == 1 else "Legítimo"
print(f"Caso novo {novo[0]} -> {rotulo}")
