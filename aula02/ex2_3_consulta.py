"""Exercício 2.3 — Consulta com filtros dinâmicos.

Rode antes o ex2_2_ingestao_logs.py para popular a coleção 'eventos'.
"""
from datetime import datetime

from conexao_mongo import get_db


def consultar(fonte=None, tipo=None, ip=None, desde=None, colecao=None):
    """Monta o filtro só com os parâmetros informados (None é ignorado)."""
    colecao = colecao if colecao is not None else get_db()["eventos"]
    filtro = {}
    if fonte is not None:
        filtro["fonte"] = fonte
    if tipo is not None:
        filtro["tipo"] = tipo
    if ip is not None:
        filtro["ip"] = ip
    if desde is not None:
        filtro["timestamp"] = {"$gte": desde}
    return list(colecao.find(filtro, {"_id": 0}).sort("timestamp", 1))


def mostrar(titulo, docs):
    print(f"\n=== {titulo} ({len(docs)} resultados) ===")
    for d in docs:
        print(f"{d['timestamp']} {d['tipo']:<8} {d['ip']:<15} usuario={d['detalhes']['usuario']}")


if __name__ == "__main__":
    col = get_db()["eventos"]
    mostrar('consultar(tipo="FAIL", ip="185.220.101.1")', consultar(tipo="FAIL", ip="185.220.101.1", colecao=col))
    mostrar('consultar(fonte="auth")', consultar(fonte="auth", colecao=col))
    mostrar('consultar(tipo="SUCCESS", desde=2025-02-20 08:17:00)',
            consultar(tipo="SUCCESS", desde=datetime(2025, 2, 20, 8, 17), colecao=col))
