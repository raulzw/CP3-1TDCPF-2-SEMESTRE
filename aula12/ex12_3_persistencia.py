"""Exercício 12.3 — Persistência com joblib + verificação de integridade SHA-256.

Uso:
    python ex12_3_persistencia.py            # treina, salva, recarrega e verifica
    python ex12_3_persistencia.py --adulterar # simula alteração do .pkl para ver o alerta
"""
import hashlib
import sys
from pathlib import Path

import joblib

from ex12_2_torneio import otimizar, torneio

PASTA = Path(__file__).resolve().parent
ARQ_MODELO = PASTA / "modelo_seguranca.pkl"
ARQ_HASH = PASTA / "modelo_seguranca.sha256"


def sha256_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()


def salvar(modelo):
    joblib.dump(modelo, ARQ_MODELO)
    digest = sha256_arquivo(ARQ_MODELO)
    ARQ_HASH.write_text(digest)
    print(f"Modelo salvo: {ARQ_MODELO.name}")
    print(f"Hash SHA-256: {digest}")


def carregar_verificado():
    """Só desserializa o .pkl DEPOIS de confirmar o hash (pickle executa código ao carregar)."""
    print("Recarregando e verificando integridade...")
    esperado = ARQ_HASH.read_text().strip()
    atual = sha256_arquivo(ARQ_MODELO)
    if atual != esperado:
        print("ALERTA: arquivo do modelo foi modificado!")
        return None
    return joblib.load(ARQ_MODELO)


if __name__ == "__main__":
    salvar(otimizar(torneio()))

    if "--adulterar" in sys.argv:
        with open(ARQ_MODELO, "ab") as f:
            f.write(b"bytes maliciosos")

    modelo = carregar_verificado()
    if modelo is not None:
        previsao = modelo.predict([[58000, 4444, 16.0]])
        print(f"Hash confere: modelo íntegro. Previsão de teste: {previsao}")
