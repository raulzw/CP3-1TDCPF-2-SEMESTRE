"""Testes da Aula 8 com test_client (o 8.2 troca a consulta ao MySQL por um dicionário em memória)."""
import logging

from werkzeug.security import generate_password_hash

import ex8_1_dashboard_xss as dash
import ex8_2_login as login

logging.disable(logging.CRITICAL)

print("=== 8.1 XSS ===")
c = dash.app.test_client()
payload = "<script>alert('xss')</script>"
c.post("/alertas", data={"tipo": "XSS", "severidade": "alta", "descricao": payload})
html = c.get("/").get_data(as_text=True)
print("Payload cru presente no HTML (executaria)?", payload in html)
print("Payload escapado presente (aparece como texto)?", "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html)

print("\n=== 8.2 Login ===")
BANCO_FAKE = {u: generate_password_hash(s) for u, s in login.USUARIOS_SEMENTE.items()}
login.buscar_hash = BANCO_FAKE.get
c = login.app.test_client()
casos = [
    {"usuario": "admin", "senha": "errada"},
    {"usuario": "naoexiste", "senha": "x"},
    {"usuario": "admin", "senha": "Cyber@2024"},
    {"usuario": "", "senha": ""},
]
for corpo in casos:
    r = c.post("/login", json=corpo)
    print(f"POST {corpo} -> {r.status_code} {r.get_json()}")

print("\nLimite de tentativas (analista, 6 senhas erradas):")
for i in range(6):
    r = c.post("/login", json={"usuario": "analista", "senha": f"chute{i}"})
    print(f"  tentativa {i + 1}: {r.status_code} {r.get_json()['erro']}")
