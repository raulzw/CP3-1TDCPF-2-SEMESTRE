"""Exercício 7.3 — API de usuários com Flask + MySQL, CRUD parametrizado e tratamento de erros.

Erros tratados:
    400 corpo inválido / campos ausentes
    404 usuário inexistente
    409 email duplicado
    500 banco fora do ar -> {"erro": "serviço indisponível"} (sem traceback, sem query)

Rodar:  python ex7_3_api_usuarios_mysql.py
"""
import logging
import os

import mysql.connector
from flask import Flask, jsonify, request

from conexao_mysql import get_conexao

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("api_usuarios")

SQL_CRIAR_TABELA = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        email VARCHAR(150) NOT NULL UNIQUE,
        nivel_acesso INT NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""


class BancoIndisponivel(Exception):
    pass


def executar(sql, params=(), *, buscar=None, commit=False):
    """Abre conexão, executa (sempre parametrizado) e fecha. buscar: 'um' | 'todos' | None."""
    try:
        conexao = get_conexao()
    except mysql.connector.Error as e:
        log.error("Falha ao conectar no MySQL: %s", e)  # detalhe vai só para o log interno
        raise BancoIndisponivel() from e
    try:
        cur = conexao.cursor(dictionary=True)
        cur.execute(sql, params)
        if commit:
            conexao.commit()
        if buscar == "um":
            return cur.fetchone()
        if buscar == "todos":
            return cur.fetchall()
        return {"lastrowid": cur.lastrowid, "rowcount": cur.rowcount}
    finally:
        conexao.close()


def validar(dados, parcial=False):
    if not isinstance(dados, dict):
        return "corpo JSON inválido"
    if not parcial:
        faltando = [c for c in ("nome", "email") if not dados.get(c)]
        if faltando:
            return f"campos obrigatórios ausentes: {', '.join(faltando)}"
    if "email" in dados and (not isinstance(dados["email"], str) or "@" not in dados["email"]):
        return "email inválido"
    if "nivel_acesso" in dados:
        n = dados["nivel_acesso"]
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 5:
            return "nivel_acesso deve ser inteiro entre 1 e 5"
    return None


@app.route("/api/usuarios", methods=["GET"])
def listar():
    return jsonify(executar("SELECT id, nome, email, nivel_acesso FROM usuarios ORDER BY id",
                            buscar="todos")), 200


@app.route("/api/usuarios/<int:id_>", methods=["GET"])
def obter(id_):
    u = executar("SELECT id, nome, email, nivel_acesso FROM usuarios WHERE id = %s",
                 (id_,), buscar="um")
    return (jsonify(u), 200) if u else (jsonify({"erro": "usuário não encontrado"}), 404)


@app.route("/api/usuarios", methods=["POST"])
def criar():
    dados = request.get_json(silent=True)
    erro = validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    try:
        cur = executar("INSERT INTO usuarios (nome, email, nivel_acesso) VALUES (%s, %s, %s)",
                       (dados["nome"], dados["email"], dados.get("nivel_acesso", 1)), commit=True)
    except mysql.connector.IntegrityError:
        return jsonify({"erro": "email já cadastrado"}), 409
    return jsonify({"id": cur["lastrowid"]}), 201


@app.route("/api/usuarios/<int:id_>", methods=["PUT"])
def atualizar(id_):
    dados = request.get_json(silent=True)
    erro = validar(dados, parcial=True)
    if erro:
        return jsonify({"erro": erro}), 400
    campos = [c for c in ("nome", "email", "nivel_acesso") if c in dados]
    if not campos:
        return jsonify({"erro": "nenhum campo para atualizar"}), 400
    if not obter_existente(id_):
        return jsonify({"erro": "usuário não encontrado"}), 404
    # Os NOMES de coluna vêm de uma lista branca fixa; os VALORES vão parametrizados.
    sets = ", ".join(f"{c} = %s" for c in campos)
    try:
        executar(f"UPDATE usuarios SET {sets} WHERE id = %s",
                 tuple(dados[c] for c in campos) + (id_,), commit=True)
    except mysql.connector.IntegrityError:
        return jsonify({"erro": "email já cadastrado"}), 409
    return obter(id_)


def obter_existente(id_):
    return executar("SELECT id FROM usuarios WHERE id = %s", (id_,), buscar="um")


@app.route("/api/usuarios/<int:id_>", methods=["DELETE"])
def deletar(id_):
    cur = executar("DELETE FROM usuarios WHERE id = %s", (id_,), commit=True)
    if cur["rowcount"] == 0:
        return jsonify({"erro": "usuário não encontrado"}), 404
    return jsonify({"mensagem": "Removido"}), 200


@app.errorhandler(BancoIndisponivel)
def banco_fora(e):
    return jsonify({"erro": "serviço indisponível"}), 500


@app.errorhandler(mysql.connector.Error)
def erro_banco(e):
    log.exception("Erro de banco")  # traceback só no log do servidor
    return jsonify({"erro": "serviço indisponível"}), 500


@app.errorhandler(500)
def erro_interno(e):
    return jsonify({"erro": "erro interno do servidor"}), 500


if __name__ == "__main__":
    try:
        executar(SQL_CRIAR_TABELA, commit=True)
    except BancoIndisponivel:
        log.warning("MySQL indisponível na inicialização; a API responderá 500 até ele voltar.")
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
