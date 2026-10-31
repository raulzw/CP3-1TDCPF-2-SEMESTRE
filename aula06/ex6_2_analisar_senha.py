"""Exercício 6.2 — Endpoint POST /api/analisar-senha."""
import os
import string

from flask import Flask, jsonify, request

app = Flask(__name__)


def verificar_senha(senha):
    """Função do 1º semestre: avalia critérios e devolve (força, critérios)."""
    criterios = {
        "tamanho_min": len(senha) >= 8,
        "maiuscula": any(c.isupper() for c in senha),
        "minuscula": any(c.islower() for c in senha),
        "numero": any(c.isdigit() for c in senha),
        "especial": any(c in string.punctuation for c in senha),
    }
    pontos = sum(criterios.values())
    forca = {5: "Muito forte", 4: "Forte", 3: "Média", 2: "Fraca"}.get(pontos, "Muito fraca")
    return forca, criterios


@app.route("/api/analisar-senha", methods=["POST"])
def analisar_senha():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or "senha" not in dados:
        return jsonify({"erro": "campo 'senha' obrigatório"}), 400
    if not isinstance(dados["senha"], str) or not dados["senha"]:
        return jsonify({"erro": "campo 'senha' deve ser um texto não vazio"}), 400
    forca, criterios = verificar_senha(dados["senha"])
    # Nunca devolvemos nem registramos a senha recebida
    return jsonify({"forca": forca, "criterios": criterios}), 200


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
