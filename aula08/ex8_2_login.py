"""Exercício 8.2 — POST /login endurecido.

Defesas implementadas:
  * Query PARAMETRIZADA no MySQL (sem SQL Injection).
  * Senhas guardadas como HASH (werkzeug: scrypt/pbkdf2 com salt), nunca em texto puro.
  * Mensagem 401 GENÉRICA ("Credenciais inválidas") tanto para usuário inexistente quanto
    para senha errada. Se a API dissesse "usuário não existe", um atacante poderia testar nomes
    e descobrir quais contas são válidas (user enumeration — OWASP A07), reduzindo o brute force
    a adivinhar apenas a senha.
  * Hash "fantasma" verificado mesmo quando o usuário não existe: o tempo de resposta fica
    parecido nos dois casos e não denuncia a existência da conta.
  * Limite de tentativas: 5 falhas em 5 minutos por IP+usuário -> 429 Too Many Requests.
  * Log de tentativas (OWASP A09), sem registrar a senha.

Preparar o banco:  python ex8_2_login.py --criar-usuarios
Rodar a API:       python ex8_2_login.py
"""
import logging
import os
import sys
import time
from collections import defaultdict, deque

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from conexao_mysql import get_conexao

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("login")

MAX_TENTATIVAS = 5
JANELA_SEGUNDOS = 300
_falhas = defaultdict(deque)  # (ip, usuario) -> timestamps das falhas
HASH_FANTASMA = generate_password_hash("senha-que-nao-existe")

USUARIOS_SEMENTE = {"admin": "Cyber@2024", "analista": "S3gur4nca!"}


def criar_usuarios():
    conexao = get_conexao()
    cur = conexao.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS contas (
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       usuario VARCHAR(50) NOT NULL UNIQUE,
                       senha_hash VARCHAR(255) NOT NULL)""")
    for usuario, senha in USUARIOS_SEMENTE.items():
        cur.execute("INSERT INTO contas (usuario, senha_hash) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE senha_hash = VALUES(senha_hash)",
                    (usuario, generate_password_hash(senha)))
    conexao.commit()
    conexao.close()
    print("Tabela 'contas' pronta com usuários admin e analista.")


def buscar_hash(usuario):
    conexao = get_conexao()
    try:
        cur = conexao.cursor()
        cur.execute("SELECT senha_hash FROM contas WHERE usuario = %s", (usuario,))
        linha = cur.fetchone()
        return linha[0] if linha else None
    finally:
        conexao.close()


def bloqueado(chave):
    agora = time.monotonic()
    fila = _falhas[chave]
    while fila and agora - fila[0] > JANELA_SEGUNDOS:
        fila.popleft()
    return len(fila) >= MAX_TENTATIVAS


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    if not isinstance(usuario, str) or not isinstance(senha, str) or not usuario.strip() or not senha:
        return jsonify({"erro": "usuario e senha são obrigatórios"}), 400

    chave = (request.remote_addr, usuario.lower())
    if bloqueado(chave):
        log.warning("Login bloqueado por excesso de tentativas: usuario=%s ip=%s", usuario, request.remote_addr)
        return jsonify({"erro": "Muitas tentativas. Tente novamente mais tarde."}), 429

    try:
        senha_hash = buscar_hash(usuario)
    except Exception:
        log.exception("Falha ao consultar contas")
        return jsonify({"erro": "serviço indisponível"}), 500

    # Sempre roda check_password_hash (com hash fantasma se não existir) -> tempo semelhante
    ok = check_password_hash(senha_hash or HASH_FANTASMA, senha) and senha_hash is not None
    if not ok:
        _falhas[chave].append(time.monotonic())
        log.warning("Falha de login: usuario=%s ip=%s", usuario, request.remote_addr)
        return jsonify({"erro": "Credenciais inválidas"}), 401

    _falhas.pop(chave, None)
    log.info("Login OK: usuario=%s ip=%s", usuario, request.remote_addr)
    return jsonify({"mensagem": "Login OK"}), 200


@app.after_request
def headers_seguranca(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":
    if "--criar-usuarios" in sys.argv:
        criar_usuarios()
    else:
        app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
