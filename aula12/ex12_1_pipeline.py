"""Exercício 12.1 — Pipeline (StandardScaler + classificador) com validação cruzada de 5 folds."""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from dataset import X, y

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(random_state=42)),
])

# StratifiedKFold mantém a proporção normal/malicioso em cada fold (importante com poucos dados)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(pipeline, X, y, cv=cv)

print(f"Scores por fold: {[round(float(s), 2) for s in scores]}")
# Obs.: o dataset é pequeno e bem separável (ataques têm bytes/duração muito maiores),
# por isso a acurácia chega a 1.00 — num dataset real o número seria menor.
print(f"Acurácia: {scores.mean():.2f} (+/- {scores.std():.2f})")
