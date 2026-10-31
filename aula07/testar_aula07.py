"""Roda as sequências de teste da Aula 7.

    python testar_aula07.py          # usa o MongoDB real (MONGO_URI) e o MySQL real
    USE_MONGOMOCK=1 python testar_aula07.py   # MongoDB em memória
O teste de 500 da API MySQL aponta para uma porta fechada, simulando o banco derrubado.
"""
import os

import ex7_1_7_2_api_incidentes as inc
import popular_incidentes


def mostrar(metodo, rota, r, resumo=False):
    corpo = r.get_json()
    if resumo and isinstance(corpo, list):
        corpo = [f"{d['severidade']}/{d['status']} {d['criado_em'][:16]}" for d in corpo]
    print(f"{metodo:<6} {rota:<42} -> {r.status_code} {corpo}")


c = inc.app.test_client()
inc.colecao().delete_many({})
print("=== 7.1 CRUD de incidentes ===")
r = c.post("/api/incidentes", json={"titulo": "Brute force SSH", "severidade": "alta",
                                    "ip_origem": "185.220.101.1"})
mostrar("POST", "Brute force SSH", r)
id_ = r.get_json()["id"]
mostrar("POST", "(sem titulo)", c.post("/api/incidentes", json={"severidade": "alta"}))
mostrar("GET", "/api/incidentes", c.get("/api/incidentes"), resumo=True)
mostrar("GET", "/api/incidentes/id_ruim", c.get("/api/incidentes/id_ruim"))
mostrar("PUT", f"/api/incidentes/{id_} status=resolvido",
        c.put(f"/api/incidentes/{id_}", json={"status": "resolvido"}))
mostrar("DELETE", f"/api/incidentes/{id_}", c.delete(f"/api/incidentes/{id_}"))

print("\n=== 7.2 Paginação e filtros (15 incidentes) ===")
popular_incidentes.popular(inc.colecao())
for q in ("tamanho=5&pagina=1", "severidade=critica", "status=aberto&tamanho=3", "tamanho=abc"):
    mostrar("GET", f"/api/incidentes?{q}", c.get(f"/api/incidentes?{q}"), resumo=True)

print("\n=== 7.3 API MySQL com banco derrubado ===")
os.environ["MYSQL_PORT"] = "1"  # porta fechada = banco fora do ar
import ex7_3_api_usuarios_mysql as usr  # noqa: E402
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
mostrar("GET", "/api/usuarios", usr.app.test_client().get("/api/usuarios"))
mostrar("POST", "(sem email)", usr.app.test_client().post("/api/usuarios", json={"nome": "X"}))
