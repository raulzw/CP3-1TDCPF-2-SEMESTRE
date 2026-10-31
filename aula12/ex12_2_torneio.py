"""Exercício 12.2 — Torneio RandomForest x SVM x KNN + GridSearch no vencedor."""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from dataset import X, y

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Cada modelo dentro de um Pipeline com scaler: SVM e KNN são sensíveis à escala
MODELOS = {
    "RandomForest": RandomForestClassifier(random_state=42),
    "SVM": SVC(),
    "KNN": KNeighborsClassifier(),
}
GRADES = {
    "RandomForest": {"clf__n_estimators": [50, 100, 200], "clf__max_depth": [None, 5, 10]},
    "SVM": {"clf__C": [0.1, 1, 10], "clf__kernel": ["linear", "rbf"]},
    "KNN": {"clf__n_neighbors": [1, 3, 5], "clf__weights": ["uniform", "distance"]},
}


def montar(modelo):
    return Pipeline([("scaler", StandardScaler()), ("clf", modelo)])


def torneio():
    resultados = {}
    for nome, modelo in MODELOS.items():
        resultados[nome] = cross_val_score(montar(modelo), X, y, cv=CV).mean()
        print(f"{nome + ':':<14}{resultados[nome]:.2f}")
    # Empate -> fica o primeiro da lista (RandomForest), que é o mais robusto
    vencedor = max(resultados, key=resultados.get)
    print(f"Vencedor: {vencedor}")
    return vencedor


def otimizar(nome):
    busca = GridSearchCV(montar(MODELOS[nome]), GRADES[nome], cv=CV)
    busca.fit(X, y)
    params = {k.replace("clf__", ""): v for k, v in busca.best_params_.items()}
    print(f"Melhores parâmetros: {params}")
    print(f"Melhor score: {busca.best_score_:.2f}")
    return busca.best_estimator_


if __name__ == "__main__":
    otimizar(torneio())
