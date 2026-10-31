"""Exercício 4.3 — Avaliação honesta com matriz de confusão."""
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)

y_verdadeiro = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]  # 8 normais, 2 ataques
y_previsto = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]    # o modelo perdeu 1 ataque

matriz = confusion_matrix(y_verdadeiro, y_previsto)
vn, fp, fn, vp = matriz.ravel()

print(f"Matriz: {matriz.tolist()}")
print(f"  VN={vn} FP={fp} FN={fn} VP={vp}")
print(f"Precisão: {precision_score(y_verdadeiro, y_previsto):.2f} | "
      f"Recall: {recall_score(y_verdadeiro, y_previsto):.2f} | "
      f"F1: {f1_score(y_verdadeiro, y_previsto):.2f} | "
      f"Acurácia: {accuracy_score(y_verdadeiro, y_previsto):.2f}")

print("""
Interpretação:
1. A acurácia de 90% parece boa só porque 80% dos dados são normais; um modelo que dissesse
   "tudo normal" já teria 80%.
2. A precisão 1.00 mostra que não houve alarme falso, mas o recall 0.50 revela que METADE dos
   ataques reais passou despercebida (1 falso negativo).
3. Num SOC, um ataque não detectado custa muito mais que um alerta falso, por isso o recall
   importa mais que a acurácia neste cenário desbalanceado.""")
