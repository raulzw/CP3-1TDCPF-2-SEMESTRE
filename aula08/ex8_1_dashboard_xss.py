"""Exercício 8.1 — Dashboard de alertas com defesa contra XSS.

Defesas:
  * O HTML é renderizado com render_template_string (Jinja2), que ESCAPA {{ variáveis }} por padrão.
  * Nunca usamos |safe nem Markup em dados do usuário.
  * Headers de segurança, incluindo Content-Security-Policy (segunda camada: bloqueia script inline).

Rodar: python ex8_1_dashboard_xss.py  -> http://localhost:5000
Teste: cadastre a descrição  <script>alert('xss')</script>  — ela aparece como TEXTO e o alert não abre.
"""
import os

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
alertas = []
SEVERIDADES = ("baixa", "media", "alta", "critica")

PAGINA = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"><title>Dashboard de Alertas</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { border-bottom: 1px solid #ddd; padding: .5rem; text-align: left; }
    .critica { color: #b00020; font-weight: bold; } .alta { color: #c25100; }
    form { display: grid; gap: .5rem; } .erro { color: #b00020; }
  </style>
</head>
<body>
  <h1>Dashboard de Alertas</h1>
  {% if erro %}<p class="erro">{{ erro }}</p>{% endif %}
  <form method="post" action="{{ url_for('cadastrar') }}">
    <input name="tipo" placeholder="Tipo (ex: BRUTE_FORCE)" maxlength="50" required>
    <select name="severidade">{% for s in severidades %}<option>{{ s }}</option>{% endfor %}</select>
    <input name="descricao" placeholder="Descrição" maxlength="500" required>
    <button>Cadastrar alerta</button>
  </form>
  <table>
    <tr><th>#</th><th>Tipo</th><th>Severidade</th><th>Descrição</th></tr>
    {% for a in alertas %}
    <tr><td>{{ loop.index }}</td><td>{{ a.tipo }}</td>
        <td class="{{ a.severidade }}">{{ a.severidade }}</td><td>{{ a.descricao }}</td></tr>
    {% else %}
    <tr><td colspan="4">Nenhum alerta cadastrado.</td></tr>
    {% endfor %}
  </table>
</body>
</html>"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGINA, alertas=alertas, severidades=SEVERIDADES,
                                  erro=request.args.get("erro"))


@app.route("/alertas", methods=["POST"])
def cadastrar():
    tipo = request.form.get("tipo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    severidade = request.form.get("severidade", "")
    if not tipo or not descricao or severidade not in SEVERIDADES:   # valide a entrada...
        return redirect(url_for("index", erro="Preencha todos os campos corretamente."))
    alertas.append({"tipo": tipo[:50], "descricao": descricao[:500], "severidade": severidade})
    return redirect(url_for("index"))  # ...e escape a saída (o template faz isso)


@app.after_request
def headers_seguranca(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
    return resp


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))
