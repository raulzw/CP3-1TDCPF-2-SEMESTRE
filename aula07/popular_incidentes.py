"""Popula 15 incidentes variados (para o Exercício 7.2). Rode com o MongoDB no ar."""
import random
from datetime import datetime, timedelta, timezone

from conexao_mongo import get_db

TITULOS = ["Brute force SSH", "Port scan externo", "XSS no portal", "SQLi no login",
           "Malware em estação", "Phishing reportado", "Exfiltração suspeita"]
IPS = ["185.220.101.1", "45.33.32.156", "91.240.118.172", "10.0.0.7", "192.168.1.45"]


def gerar(n=15, seed=42):
    rnd = random.Random(seed)
    agora = datetime.now(timezone.utc)
    return [{
        "titulo": rnd.choice(TITULOS),
        "severidade": rnd.choice(["baixa", "media", "alta", "critica"]),
        "status": rnd.choice(["aberto", "em_andamento", "resolvido"]),
        "ip_origem": rnd.choice(IPS),
        "criado_em": agora - timedelta(hours=i * 3),
    } for i in range(n)]


def popular(colecao, n=15):
    colecao.delete_many({})
    colecao.insert_many(gerar(n))
    return n


if __name__ == "__main__":
    print(f"{popular(get_db()['incidentes'])} incidentes inseridos.")
