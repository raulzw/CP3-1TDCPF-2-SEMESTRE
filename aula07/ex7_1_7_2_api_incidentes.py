"""Exercícios 7.1 e 7.2 — API de incidentes com Flask + MongoDB.

7.1: CRUD completo, serialização do _id e validação de campos obrigatórios.
7.2: paginação, filtros por severidade/status e ordenação por criado_em (mais recentes primeiro).

Parâmetros aceitos em GET /api/incidentes:
    pagina     (int >= 1, padrão 1)
    tamanho    (int 1..100, padrão 10)
    severidade (baixa | media | alta | critica)
    status     (aberto | em_andamento | resolvido)

Rodar:  python ex7_1_7_2_api_incidentes.py
"""
import os

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, request

from conexao_mongo import get_db

app = Flask(__name__)
SEVERIDADES = ("baixa", "media", "alta", "critica")
STATUS = ("aberto", "em_andamento", "resolvido")
CAMPOS_EDITAVEIS = ("titulo", "severidade", "status", "ip_origem")

_col = None


def colecao():
    global _col
    if _col is None:
        _col = get_db()["incidentes"]
        _col.create_index([("criado_em", -1)])
    return _col


def serializar(doc):
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("criado_em"), datetime):
        doc["criado_em"] = doc["criado_em"].isoformat()
    return doc


def para_object_id(id_):
    try:
        return ObjectId(id_)
    except (InvalidId, TypeError):
        return None


def validar(dados, parcial=False):
    if not isinstance(dados, dict):
        return "corpo JSON inválido"
    if not parcial:
        faltando = [c for c in ("titulo", "severidade", "ip_origem") if not dados.get(c)]
        if faltando:
            return f"campos obrigatórios ausentes: {', '.join(faltando)}"
    if "titulo" in dados and (not isinstance(dados["titulo"], str) or not dados["titulo"].strip()):
        return "titulo inválido"
    if "severidade" in dados and dados["severidade"] not in SEVERIDADES:
        return f"severidade deve ser uma de {SEVERIDADES}"
    if "status" in dados and dados["status"] not in STATUS:
        return f"status deve ser um de {STATUS}"
    return None


def ler_int(nome, padrao, minimo, maximo):
    valor = request.args.get(nome, padrao)
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"'{nome}' deve ser inteiro")
    if not minimo <= valor <= maximo:
        raise ValueError(f"'{nome}' deve estar entre {minimo} e {maximo}")
    return valor


@app.route("/api/incidentes", methods=["GET"])
def listar():
    try:
        pagina = ler_int("pagina", 1, 1, 10_000)
        tamanho = ler_int("tamanho", 10, 1, 100)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    filtro = {}
    for campo, permitidos in (("severidade", SEVERIDADES), ("status", STATUS)):
        valor = request.args.get(campo)
        if valor is not None:
            if valor not in permitidos:
                return jsonify({"erro": f"{campo} inválido"}), 400
            filtro[campo] = valor  # só strings da lista branca entram no filtro (anti NoSQL injection)

    cursor = (colecao().find(filtro).sort("criado_em", -1)
              .skip((pagina - 1) * tamanho).limit(tamanho))
    return jsonify([serializar(d) for d in cursor]), 200


@app.route("/api/incidentes/<id_>", methods=["GET"])
def obter(id_):
    oid = para_object_id(id_)
    if oid is None:
        return jsonify({"erro": "id inválido"}), 400
    doc = colecao().find_one({"_id": oid})
    return (jsonify(serializar(doc)), 200) if doc else (jsonify({"erro": "não encontrado"}), 404)


@app.route("/api/incidentes", methods=["POST"])
def criar():
    dados = request.get_json(silent=True)
    erro = validar(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    doc = {c: dados[c] for c in CAMPOS_EDITAVEIS if c in dados}  # ignora campos extras
    doc.setdefault("status", "aberto")
    doc["criado_em"] = datetime.now(timezone.utc)
    r = colecao().insert_one(doc)
    return jsonify({"id": str(r.inserted_id)}), 201


@app.route("/api/incidentes/<id_>", methods=["PUT"])
def atualizar(id_):
    oid = para_object_id(id_)
    if oid is None:
        return jsonify({"erro": "id inválido"}), 400
    dados = request.get_json(silent=True)
    erro = validar(dados, parcial=True)
    if erro:
        return jsonify({"erro": erro}), 400
    mudancas = {c: dados[c] for c in CAMPOS_EDITAVEIS if c in dados}
    if not mudancas:
        return jsonify({"erro": "nenhum campo para atualizar"}), 400
    r = colecao().update_one({"_id": oid}, {"$set": mudancas})
    if r.matched_count == 0:
        return jsonify({"erro": "não encontrado"}), 404
    return jsonify(serializar(colecao().find_one({"_id": oid}))), 200


@app.route("/api/incidentes/<id_>", methods=["DELETE"])
def deletar(id_):
    oid = para_object_id(id_)
    if oid is None:
        return jsonify({"erro": "id inválido"}), 400
    r = colecao().delete_one({"_id": oid})
    if r.deleted_count == 0:
        return jsonify({"erro": "não encontrado"}), 404
    return jsonify({"mensagem": "Removido"}), 200


@app.errorhandler(500)
def erro_interno(e):
    return jsonify({"erro": "erro interno do servidor"}), 500


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
