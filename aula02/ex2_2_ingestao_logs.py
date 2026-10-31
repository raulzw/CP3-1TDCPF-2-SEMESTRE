"""Exercício 2.2 — Ingestão do auth.log no MongoDB + top IPs por falhas (aggregation)."""
import sys
from datetime import datetime
from pathlib import Path

from conexao_mongo import get_db

ARQUIVO_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "auth.log"


def parsear_linha(linha):
    """'2025-02-20 08:15:01 FAIL usuario=admin ip=185.220.101.1' -> dict normalizado."""
    partes = linha.split()
    if len(partes) < 5:
        return None
    campos = dict(p.split("=", 1) for p in partes[3:] if "=" in p)
    return {
        "timestamp": datetime.strptime(f"{partes[0]} {partes[1]}", "%Y-%m-%d %H:%M:%S"),
        "fonte": "auth",
        "tipo": partes[2],
        "ip": campos.get("ip"),
        "detalhes": {"usuario": campos.get("usuario")},
    }


def ingerir(colecao, caminho):
    with open(caminho, encoding="utf-8") as f:
        docs = [d for d in (parsear_linha(l) for l in f if l.strip()) if d]
    if docs:
        colecao.insert_many(docs)
    return len(docs)


def top_ips_falhas(colecao, limite=5):
    pipeline = [
        {"$match": {"tipo": "FAIL"}},
        {"$group": {"_id": "$ip", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": limite},
    ]
    return list(colecao.aggregate(pipeline))


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else ARQUIVO_PADRAO
    eventos = get_db()["eventos"]
    eventos.delete_many({"fonte": "auth"})  # reexecutável sem duplicar
    eventos.create_index("ip")
    eventos.create_index([("fonte", 1), ("timestamp", -1)])
    total = ingerir(eventos, caminho)

    print("=== Top IPs por falhas de login ===")
    for linha in top_ips_falhas(eventos):
        print(f"{linha['_id']:<15} -> {linha['total']} falhas")
    print(f"Total de eventos inseridos: {total}")


if __name__ == "__main__":
    main()
