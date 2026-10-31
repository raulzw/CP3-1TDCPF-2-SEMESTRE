# Exercício 8.3 — Auditoria de código

## Código auditado

```python
@app.route("/user/<nome>")
def user(nome):
    cur.execute("SELECT * FROM users WHERE nome='" + nome + "'")   # (1)
    dados = cur.fetchone()
    return f"<h1>Bem-vindo {nome}</h1>" + str(dados)               # (2)

app.run(debug=True, host="0.0.0.0")                                # (3)
SENHA_DB = "123456"                                                # (4)
# (5) nenhuma rota registra logs de acesso ou tentativa de erro
```

## Achados

| # | Vulnerabilidade | OWASP Top 10:2025 | Risco | Correção |
|---|-----------------|-------------------|-------|----------|
| 1 | **SQL Injection** — `nome` vem da URL e é concatenado na query | **A05 – Injection** | Crítico. `/user/' OR '1'='1` devolve o primeiro usuário da tabela; com `UNION SELECT` dá para ler outras tabelas. | Query parametrizada: `cur.execute("SELECT id, nome FROM users WHERE nome = %s", (nome,))` |
| 2 | **XSS refletido** — `nome` volta para o HTML sem escape | **A05 – Injection** | Alto. `/user/<script>...</script>` executa JavaScript no navegador da vítima (roubo de sessão, phishing). | `escape(nome)` do `markupsafe` ou template Jinja2 (escapa por padrão). |
| 2b | **Exposição de dados** — `str(dados)` devolve a linha inteira (`SELECT *`), possivelmente com hash de senha e e-mail | **A01 – Broken Access Control** / A04 | Alto. Vaza campos sensíveis para qualquer visitante. | Selecionar só as colunas necessárias e devolver um JSON controlado. |
| 3 | **`debug=True` com `host="0.0.0.0"`** | **A02 – Security Misconfiguration** | Crítico. O debugger do Werkzeug fica acessível na rede e permite executar código Python no servidor; erros também vazam código-fonte. | `debug=False` em produção, servir com WSGI (ex.: `gunicorn`) e controlar o modo por variável de ambiente. |
| 4 | **Segredo fixo no código** (`SENHA_DB = "123456"`), e ainda fraco | **A04 – Cryptographic Failures** / **A02** | Alto. Quem acessa o repositório (ou um vazamento do Git) obtém a senha do banco; `123456` cai em qualquer brute force. | Ler de variável de ambiente ou cofre (`os.environ["DB_PASSWORD"]`), senha forte e rotacionada, `.env` no `.gitignore`. |
| 5 | **Ausência de logs** de acesso e de erro | **A09 – Security Logging & Alerting Failures** | Médio/Alto. Um ataque (como o de injeção acima) acontece sem deixar rastro e sem gerar alerta. | Módulo `logging` registrando acessos, erros e entradas suspeitas (sem dados sensíveis), enviado ao SIEM. |

Observação extra: a rota também não trata exceções (`dados` pode ser `None`, erro de banco gera stack trace) — **A10 – Mishandling of Exceptional Conditions**.

## Código corrigido

```python
import logging
import os

import mysql.connector
from flask import Flask, abort, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")


def get_conexao():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],          # (4) segredo fora do código
        database=os.environ.get("DB_NAME", "seguranca"),
    )


@app.route("/user/<nome>")
def user(nome):
    log.info("GET /user nome=%r", nome)              # (5) log de acesso
    try:
        conexao = get_conexao()
        cur = conexao.cursor(dictionary=True)
        cur.execute("SELECT id, nome FROM users WHERE nome = %s", (nome,))   # (1) parametrizado
        dados = cur.fetchone()
        conexao.close()
    except mysql.connector.Error:
        log.exception("Erro de banco em /user")      # (5) log de erro
        return jsonify({"erro": "serviço indisponível"}), 500
    if dados is None:
        abort(404)
    return jsonify({"mensagem": "Bem-vindo", "usuario": dados})   # (2) JSON, sem HTML refletido


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1")   # (3)
```
