"""Roda as sequências de teste do enunciado da Aula 6 usando o test_client do Flask (sem subir servidor)."""
import ex6_1_api_usuarios as a1
import ex6_2_analisar_senha as a2
import ex6_3_checar_ip as a3


def mostrar(metodo, rota, r):
    print(f"{metodo:<6} {rota:<45} -> {r.status_code} {r.get_json()}")


c = a1.app.test_client()
print("=== 6.1 API de usuários ===")
for corpo in ({"nome": "Ana", "email": "ana@x.com", "nivel": 5},
              {"nome": "Bia", "email": "ana@x.com", "nivel": 2},
              {"nome": "Cid", "email": "cid@x.com", "nivel": 9}):
    mostrar("POST", str(corpo), c.post("/api/usuarios", json=corpo))
mostrar("GET", "/api/usuarios/1", c.get("/api/usuarios/1"))
mostrar("GET", "/api/usuarios/99", c.get("/api/usuarios/99"))
mostrar("PUT", "/api/usuarios/1 {nivel: 4}", c.put("/api/usuarios/1", json={"nivel": 4}))
mostrar("DELETE", "/api/usuarios/1", c.delete("/api/usuarios/1"))

c = a2.app.test_client()
print("\n=== 6.2 Analisar senha ===")
mostrar("POST", '{"senha": "Cyber@2024"}', c.post("/api/analisar-senha", json={"senha": "Cyber@2024"}))
mostrar("POST", "{}", c.post("/api/analisar-senha", json={}))
mostrar("POST", "(corpo não-JSON)", c.post("/api/analisar-senha", data="abc"))

c = a3.app.test_client()
print("\n=== 6.3 Checar IP ===")
for ip in ("185.220.101.1", "192.168.1.10", "999.999.1.1"):
    mostrar("GET", f"/api/checar-ip/{ip}", c.get(f"/api/checar-ip/{ip}"))
