"""Exercício 6.1 — API CRUD de usuários em memória (Flask).

Rodar:  python ex6_1_api_usuarios.py   -> http://localhost:5000/api/usuarios
"""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)
usuarios = []
proximo_id = 1


def buscar(id_):
    return next((u for u in usuarios if u["id"] == id_), None)


def email_em_uso(email, ignorar_id=None):
    return any(u["email"].lower() == email.lower() and u["id"] != ignorar_id for u in usuarios)


def validar(dados, parcial=False, ignorar_id=None):
    """Retorna mensagem de erro ou None se estiver tudo ok."""
    if not isinstance(dados, dict):
        return "corpo JSON inválido"
    if not parcial:
        faltando = [c for c in ("nome", "email", "nivel") if c not in dados]
        if faltando:
            return f"campos obrigatórios ausentes: {', '.join(faltando)}"
    if "nome" in dados and (not isinstance(dados["nome"], str) or not dados["nome"].strip()):
        return "nome inválido"
    if "email" in dados:
        if not isinstance(dados["email"], str) or "@" not in dados["email"]:
            return "email inválido"
        if email_em_uso(dados["email"], ignorar_id):
            return "email já existe"
    if "nivel" in dados:
        nivel = dados["nivel"]
        if not isinstance(nivel, int) or isinstance(nivel, bool) or not 1 <= nivel <= 5:
            return "nível inválido"
    return None


@app.route("/api/usuarios", methods=["GET"])
def listar():
    return jsonify(usuarios), 200


@app.route("/api/usuarios/<int:id_>", methods=["GET"])
def obter(id_):
    u = buscar(id_)
    return (jsonify(u), 200) if u else (jsonify({"erro": "Usuário não encontrado"}), 404)


@app.route("/api/usuarios", methods=["POST"])
def criar():
    global proximo_id
    dados = request.get_json(silent=True)
    erro = validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    usuario = {"id": proximo_id, "nome": dados["nome"].strip(),
               "email": dados["email"].strip(), "nivel": dados["nivel"]}
    usuarios.append(usuario)
    proximo_id += 1
    return jsonify(usuario), 201


@app.route("/api/usuarios/<int:id_>", methods=["PUT"])
def atualizar(id_):
    u = buscar(id_)
    if not u:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    dados = request.get_json(silent=True)
    erro = validar(dados, parcial=True, ignorar_id=id_)
    if erro:
        return jsonify({"erro": erro}), 400
    u.update({k: dados[k] for k in ("nome", "email", "nivel") if k in dados})
    return jsonify(u), 200


@app.route("/api/usuarios/<int:id_>", methods=["DELETE"])
def deletar(id_):
    u = buscar(id_)
    if not u:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    usuarios.remove(u)
    return jsonify({"mensagem": "Removido"}), 200


@app.errorhandler(404)
def rota_inexistente(e):
    return jsonify({"erro": "Rota não existe"}), 404


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
