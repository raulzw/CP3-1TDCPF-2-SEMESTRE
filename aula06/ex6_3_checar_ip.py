"""Exercício 6.3 — GET /api/checar-ip/<ip>: blacklist + privado/público."""
import os

from flask import Flask, jsonify

app = Flask(__name__)

blacklist = {"185.220.101.1", "45.33.32.156", "91.240.118.172"}


def ip_valido(ip):
    partes = ip.split(".")
    if len(partes) != 4:
        return False
    for p in partes:
        if not p.isdigit() or not 0 <= int(p) <= 255 or (len(p) > 1 and p[0] == "0"):
            return False
    return True


def classificar_ip(ip):
    """Lógica do 1º semestre: faixas privadas RFC 1918 + loopback."""
    a, b, *_ = map(int, ip.split("."))
    if a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168) or a == 127:
        return "privado"
    return "publico"


@app.route("/api/checar-ip/<ip>", methods=["GET"])
def checar_ip(ip):
    if not ip_valido(ip):
        return jsonify({"erro": "IP inválido"}), 400
    return jsonify({"ip": ip, "na_blacklist": ip in blacklist, "tipo": classificar_ip(ip)}), 200


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
