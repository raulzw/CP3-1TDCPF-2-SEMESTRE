"""Testa TODOS os exercícios do CP3 de verdade e confere com a saída esperada da apostila.

* Roda cada script como você rodaria no terminal (com as entradas do menu já digitadas).
* Sobe cada API Flask numa porta livre e faz as requisições HTTP reais (como o curl da aula).
* Usa MySQL e MongoDB REAIS, num banco separado chamado "cp3_teste" (não mexe no seu "seguranca").
* Aula 10 usa a internet de verdade (NVD, GitHub, ipinfo) e também um teste offline simulado.
* Aula 13 roda o LLM simulado e, se OPENAI_API_KEY estiver definida, também a OpenAI real.

Uso (na pasta raiz do projeto, com o venv ativado):
    python testar_tudo.py

Configuração: lê o arquivo .env (copie de .env.example) ou as variáveis de ambiente
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MONGO_URI e, opcionalmente, OPENAI_API_KEY.
Sem MySQL ou sem MongoDB no ar, os testes que dependem deles aparecem como PULADO.
"""
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
BANCO_TESTE = "cp3_teste"
resultados = []  # (aula, nome, status, detalhe)


# ------------------------------------------------------------------ ambiente ---
def carregar_env():
    env = dict(os.environ)
    arq = RAIZ / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                if v.strip() and k.strip() not in env:
                    env[k.strip()] = v.strip()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               MYSQL_DATABASE=BANCO_TESTE, MONGO_DB=BANCO_TESTE)
    env.pop("USE_MONGOMOCK", None)
    return env


ENV = carregar_env()


def conectar_mysql(com_banco=True):
    import mysql.connector
    kw = dict(host=ENV.get("MYSQL_HOST", "localhost"), port=int(ENV.get("MYSQL_PORT", "3306")),
              user=ENV.get("MYSQL_USER", "root"), password=ENV.get("MYSQL_PASSWORD", ""),
              connection_timeout=5)
    if com_banco:
        kw["database"] = BANCO_TESTE
    return mysql.connector.connect(**kw)


def preparar_mysql():
    try:
        c = conectar_mysql(com_banco=False)
        cur = c.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {BANCO_TESTE}")
        cur.execute(f"CREATE DATABASE {BANCO_TESTE}")
        c.close()
        return None
    except Exception as e:
        return f"MySQL indisponível ({type(e).__name__}: {e})"


def mongo_db():
    from pymongo import MongoClient
    cli = MongoClient(ENV.get("MONGO_URI", "mongodb://localhost:27017/"), serverSelectionTimeoutMS=3000)
    cli.admin.command("ping")
    return cli, cli[BANCO_TESTE]


def preparar_mongo():
    try:
        cli, _ = mongo_db()
        cli.drop_database(BANCO_TESTE)
        return None
    except Exception as e:
        return f"MongoDB indisponível ({type(e).__name__})"


SITES = {
    "NVD": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=1",
    "GitHub": "https://api.github.com/users/octocat",
    "ipinfo": "https://ipinfo.io/8.8.8.8/json",
}


def sites_acessiveis():
    """Devolve {nome: None se acessível, ou o motivo de não estar}."""
    estado = {}
    for nome, url in SITES.items():
        try:
            r = requests.get(url, timeout=10)
            estado[nome] = None if r.status_code < 400 else f"{nome} respondeu HTTP {r.status_code}"
        except requests.RequestException as e:
            estado[nome] = f"{nome} inacessível ({type(e).__name__})"
    return estado


# ------------------------------------------------------------------- helpers ---
def registrar(aula, nome, ok, detalhe=""):
    status = "OK" if ok else "FALHOU"
    resultados.append((aula, nome, status, detalhe))
    print(f"  [{status:^6}] {nome}" + (f"  -> {detalhe}" if detalhe and not ok else ""))


def pular(aula, nome, motivo):
    resultados.append((aula, nome, "PULADO", motivo))
    print(f"  [PULADO] {nome}  ({motivo})")


def rodar(pasta, script, *args, entrada=None, env=None, timeout=300):
    r = subprocess.run([sys.executable, script, *args], cwd=RAIZ / pasta, input=entrada,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env or ENV, timeout=timeout)
    return r.stdout + r.stderr


def contem(aula, nome, saida, *esperados, regex=False):
    faltando = [e for e in esperados if not (re.search(e, saida) if regex else e in saida)]
    registrar(aula, nome, not faltando,
              f"não encontrado: {faltando[0]!r}\n--- saída ---\n{saida[-1500:]}" if faltando else "")
    return not faltando


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def servidor(pasta, script, env_extra=None):
    porta = porta_livre()
    env = dict(ENV, PORT=str(porta), **(env_extra or {}))
    log = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, script], cwd=RAIZ / pasta, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(150):
            if proc.poll() is not None:
                log.seek(0)
                raise RuntimeError(f"{script} encerrou ao iniciar:\n{log.read()[-1500:]}")
            try:
                socket.create_connection(("127.0.0.1", porta), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        yield f"http://127.0.0.1:{porta}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()


def http(aula, nome, metodo, url, status, corpo_contem=None, **kw):
    """Faz a requisição e confere status e (opcional) um trecho/condição do JSON."""
    try:
        r = requests.request(metodo, url, timeout=15, **kw)
    except requests.RequestException as e:
        registrar(aula, nome, False, str(e))
        return None
    try:
        dados = r.json()
    except ValueError:
        dados = r.text
    ok = r.status_code == status
    if ok and corpo_contem is not None:
        ok = corpo_contem(dados) if callable(corpo_contem) else corpo_contem in json.dumps(dados, ensure_ascii=False)
    registrar(aula, nome, ok, f"recebido {r.status_code} {dados}")
    return dados


def executar_sql(arquivo):
    """Executa um .sql (trocando o banco 'seguranca' pelo de teste) e devolve os resultados dos SELECTs."""
    sql = (RAIZ / arquivo).read_text(encoding="utf-8")
    sql = re.sub(r"--[^\n]*", "", sql).replace("seguranca", BANCO_TESTE)
    conexao = conectar_mysql(com_banco=False)
    cur = conexao.cursor()
    selects = []
    for comando in (c.strip() for c in sql.split(";")):
        if comando:
            cur.execute(comando)
            if cur.with_rows:
                selects.append([tuple(str(v) for v in linha) for linha in cur.fetchall()])
    conexao.commit()
    conexao.close()
    return selects


# --------------------------------------------------------------------- aulas ---
def aula01(sem_mysql):
    A = "Aula 1"
    print(f"\n=== {A} — SQL e CAP ===")
    if sem_mysql:
        pular(A, "1.1 schema de vulnerabilidades", sem_mysql)
        pular(A, "1.2 CRUD SQL", sem_mysql)
    else:
        try:
            sel = executar_sql("aula01/ex1_1_schema_vulns.sql")
            linha = sel[-1][0]
            registrar(A, "1.1 schema roda sem erro e SRV-WEB01 tem CVE-2024-001 (Alta, 8.5)",
                      linha[0] == "SRV-WEB01" and linha[2] == "CVE-2024-001" and linha[3] == "Alta"
                      and linha[4] == "8.5", str(linha))
        except Exception as e:
            registrar(A, "1.1 schema de vulnerabilidades", False, repr(e))
        try:
            sel = executar_sql("aula01/ex1_2_crud_alertas.sql")
            registrar(A, "1.2 (b) lista só severidade 'alta' (2 alertas)",
                      len(sel[0]) == 2 and all(l[3] == "alta" for l in sel[0]), str(sel[0]))
            registrar(A, "1.2 (d) contagem: critica 1 | alta 2 | media 1",
                      sel[1] == [("critica", "1"), ("alta", "2"), ("media", "1")], str(sel[1]))
            registrar(A, "1.2 (e) apagou o alerta com mais de 90 dias (restam 3)", sel[2] == [("3",)], str(sel[2]))
        except Exception as e:
            registrar(A, "1.2 CRUD SQL", False, repr(e))
    texto = (RAIZ / "aula01/decisoes_cap.md").read_text(encoding="utf-8")
    gabarito = {1: "CP", 2: "AP", 3: "AP", 4: "CP", 5: "AP"}
    achado = {int(n): v for n, v in re.findall(r"^\|\s*(\d)\s*\|[^|]*\|\s*\*\*(CP|AP)\*\*", texto, re.M)}
    registrar(A, "1.3 decisoes_cap.md bate com o gabarito (CP, AP, AP, CP, AP)", achado == gabarito, str(achado))


def aula02(sem_mongo):
    A = "Aula 2"
    print(f"\n=== {A} — MongoDB ===")
    if sem_mongo:
        for n in ("2.1", "2.2", "2.3"):
            pular(A, n, sem_mongo)
        return
    saida = rodar("aula02", "ex2_2_ingestao_logs.py")
    contem(A, "2.2 top IPs 10/5/3 falhas e 23 eventos inseridos", saida,
           r"185\.220\.101\.1\s+-> 10 falhas", r"91\.240\.118\.172\s+-> 5 falhas",
           r"45\.33\.32\.156\s+-> 3 falhas", r"Total de eventos inseridos: 23", regex=True)
    _, db = mongo_db()
    registrar(A, "2.2 documentos realmente gravados no MongoDB (23)", db.eventos.count_documents({}) == 23)

    entrada = ("1\nSRV-DB01\nservidor\n192.168.1.20\n"
               "1\nDUPLICADO\nservidor\n192.168.1.10\n"
               "3\n192.168.1.45\n"
               "4\n192.168.1.1\nativo\n"
               "2\n6\n")
    saida = rodar("aula02", "ex2_1_inventario.py", entrada=entrada)
    contem(A, "2.1 cadastrar SRV-DB01 -> 'Ativo cadastrado!'", saida, "Ativo cadastrado!")
    contem(A, "2.1 IP duplicado -> 'Erro: IP já cadastrado!'", saida, "Erro: IP já cadastrado!")
    contem(A, "2.1 buscar 192.168.1.45 -> PC-RH03", saida, "'nome': 'PC-RH03'")
    contem(A, "2.1 atualizar status -> 'Status atualizado!'", saida, "Status atualizado!")
    contem(A, "2.1 listar -> 4 ativos, SW-CORE01 agora ativo", saida,
           r"SW-CORE01\s+switch\s+192\.168\.1\.1\s+ativo", r"Total: 4", regex=True)

    saida = rodar("aula02", "ex2_3_consulta.py")
    contem(A, "2.3 consultar(tipo='FAIL', ip='185.220.101.1') -> 10", saida, 'ip="185.220.101.1") (10 resultados)')
    contem(A, "2.3 consultar(fonte='auth') -> 23", saida, 'consultar(fonte="auth") (23 resultados)')
    contem(A, "2.3 filtro por data (desde) funciona", saida, "08:17:00) (5 resultados)")


def aula03(sem_mysql):
    A = "Aula 3"
    print(f"\n=== {A} — MySQL ===")
    if sem_mysql:
        for n in ("3.1", "3.2", "3.3"):
            pular(A, n, sem_mysql)
        return
    entrada = ("1\nCarlos Dois\ncarlos@empresa.com\n2\n"
               "1\nZe\nze@empresa.com\n9\n"
               "3\nana@empresa.com\n"
               "4\nbruno@empresa.com\n4\n"
               "2\n6\n")
    saida = rodar("aula03", "ex3_1_usuarios.py", entrada=entrada)
    contem(A, "3.1 email duplicado -> 'Erro: email já existe'", saida, "Erro: email já existe")
    contem(A, "3.1 nível 9 é rejeitado", saida, "Erro: nível deve estar entre 1 e 5")
    contem(A, "3.1 buscar ana@empresa.com -> nível 5", saida, "Ana Costa | ana@empresa.com | nível 5")
    contem(A, "3.1 promover Bruno -> 'Nível atualizado!'", saida, "Nível atualizado!")
    contem(A, "3.1 listar: Carlos 3, Ana 5, Bruno 4", saida,
           r"Carlos Silva\s+\| carlos@empresa\.com\s+\| nível 3", r"Ana Costa\s+\| ana@empresa\.com\s+\| nível 5",
           r"Bruno Lima\s+\| bruno@empresa\.com\s+\| nível 4", regex=True)
    codigo = (RAIZ / "aula03/ex3_1_usuarios.py").read_text(encoding="utf-8")
    registrar(A, "3.1 nenhuma query concatena entrada (sem f-string/format/+ em execute)",
              not re.search(r"execute\(\s*f[\"']|execute\([^)]*(\.format\(|\" ?\+)", codigo))

    saida = rodar("aula03", "ex3_2_sqli_poc.py")
    contem(A, "3.2 [INSEGURO] retorna 3 usuários (vazamento demonstrado)", saida, "-> 3 usuários retornados (VAZAMENTO!)")
    contem(A, "3.2 [SEGURO] retorna 0 usuários (defesa OK)", saida, "-> 0 usuários retornados (defesa OK)")

    saida = rodar("aula03", "ex3_3_relatorio_alertas.py")
    contem(A, "3.3 por severidade: critica 3 | alta 4 | media 2 | baixa 1", saida,
           "critica: 3 | alta: 4 | media: 2 | baixa: 1")
    contem(A, "3.3 por tipo: BRUTE_FORCE 4 | PORT_SCAN 3 | XSS 2 | SQLI 1", saida,
           "BRUTE_FORCE: 4 | PORT_SCAN: 3 | XSS: 2 | SQLI: 1")
    contem(A, "3.3 top IPs: 185.220.101.1 -> 4, 45.33.32.156 -> 3", saida,
           r"185\.220\.101\.1\s+-> 4 alertas", r"45\.33\.32\.156\s+-> 3 alertas", regex=True)


def aula04():
    A = "Aula 4"
    print(f"\n=== {A} — Machine Learning ===")
    saida = rodar("aula04", "ex4_1_phishing.py")
    contem(A, "4.1 métricas impressas (acurácia, precisão, recall, F1)", saida,
           "Acurácia:", "Precisão:", "Recall:", "F1:")
    contem(A, "4.1 caso novo [11,1,1,1,7] -> Phishing", saida, "Caso novo [11, 1, 1, 1, 7] -> Phishing")
    saida = rodar("aula04", "ex4_2_anomalias.py")
    contem(A, "4.2 amostras 5 e 8 marcadas como ANOMALIA", saida,
           "Amostra 5: [3, 40, 900000] -> ANOMALIA", "Amostra 8: [2, 55, 800000] -> ANOMALIA")
    registrar(A, "4.2 demais amostras normais (só 2 anomalias)", saida.count("-> ANOMALIA") == 2)
    saida = rodar("aula04", "ex4_3_matriz_confusao.py")
    contem(A, "4.3 matriz [[8,0],[1,1]]", saida, "Matriz: [[8, 0], [1, 1]]")
    contem(A, "4.3 precisão 1.00 | recall 0.50 | F1 0.67 | acurácia 0.90", saida,
           "Precisão: 1.00 | Recall: 0.50 | F1: 0.67 | Acurácia: 0.90")


def aula06():
    A = "Aula 6"
    print(f"\n=== {A} — Flask (servidores reais + HTTP) ===")
    with servidor("aula06", "ex6_1_api_usuarios.py") as url:
        u = f"{url}/api/usuarios"
        http(A, "6.1 POST Ana -> 201 com objeto criado", "POST", u, 201, '"nome": "Ana"',
             json={"nome": "Ana", "email": "ana@x.com", "nivel": 5})
        http(A, "6.1 POST email repetido -> 400 'email já existe'", "POST", u, 400, "email já existe",
             json={"nome": "Bia", "email": "ana@x.com", "nivel": 2})
        http(A, "6.1 POST nível 9 -> 400 'nível inválido'", "POST", u, 400, "nível inválido",
             json={"nome": "Cid", "email": "cid@x.com", "nivel": 9})
        http(A, "6.1 GET /api/usuarios/1 -> 200 Ana", "GET", f"{u}/1", 200, '"nome": "Ana"')
        http(A, "6.1 GET /api/usuarios/99 -> 404", "GET", f"{u}/99", 404)
        http(A, "6.1 PUT /api/usuarios/1 nivel 4 -> 200", "PUT", f"{u}/1", 200, '"nivel": 4', json={"nivel": 4})
        http(A, "6.1 DELETE /api/usuarios/1 -> 200 'Removido'", "DELETE", f"{u}/1", 200, "Removido")
        http(A, "6.1 GET depois do DELETE -> 404", "GET", f"{u}/1", 404)
    with servidor("aula06", "ex6_2_analisar_senha.py") as url:
        u = f"{url}/api/analisar-senha"
        http(A, "6.2 'Cyber@2024' -> 200 'Muito forte' com todos os critérios",
             "POST", u, 200, lambda d: d["forca"] == "Muito forte" and all(d["criterios"].values()),
             json={"senha": "Cyber@2024"})
        http(A, "6.2 senha fraca 'abc' -> não é 'Muito forte'", "POST", u, 200,
             lambda d: d["forca"] != "Muito forte" and not d["criterios"]["tamanho_min"], json={"senha": "abc"})
        http(A, "6.2 sem campo senha -> 400", "POST", u, 400, "campo 'senha' obrigatório", json={})
        http(A, "6.2 corpo não-JSON -> 400", "POST", u, 400, data="lixo")
    with servidor("aula06", "ex6_3_checar_ip.py") as url:
        u = f"{url}/api/checar-ip"
        http(A, "6.3 185.220.101.1 -> blacklist, público", "GET", f"{u}/185.220.101.1", 200,
             lambda d: d == {"ip": "185.220.101.1", "na_blacklist": True, "tipo": "publico"})
        http(A, "6.3 192.168.1.10 -> fora da blacklist, privado", "GET", f"{u}/192.168.1.10", 200,
             lambda d: d == {"ip": "192.168.1.10", "na_blacklist": False, "tipo": "privado"})
        http(A, "6.3 999.999.1.1 -> 400 'IP inválido'", "GET", f"{u}/999.999.1.1", 400, "IP inválido")


def aula07(sem_mongo, sem_mysql):
    A = "Aula 7"
    print(f"\n=== {A} — Flask + bancos ===")
    if sem_mongo:
        pular(A, "7.1 / 7.2 API de incidentes", sem_mongo)
    else:
        _, db = mongo_db()
        db.incidentes.delete_many({})
        with servidor("aula07", "ex7_1_7_2_api_incidentes.py") as url:
            u = f"{url}/api/incidentes"
            d = http(A, "7.1 POST incidente -> 201 com id", "POST", u, 201, '"id"',
                     json={"titulo": "Brute force SSH", "severidade": "alta", "ip_origem": "185.220.101.1"})
            id_ = d["id"] if isinstance(d, dict) and "id" in d else "000000000000000000000000"
            http(A, "7.1 POST sem campos obrigatórios -> 400", "POST", u, 400, json={"severidade": "alta"})
            http(A, "7.1 POST severidade inválida -> 400", "POST", u, 400,
                 json={"titulo": "x", "severidade": "altissima", "ip_origem": "1.2.3.4"})
            http(A, "7.1 GET lista contém o incidente (_id serializado)", "GET", u, 200,
                 lambda l: len(l) == 1 and l[0]["_id"] == id_)
            http(A, "7.1 GET /<id_ruim> -> 400 'id inválido'", "GET", f"{u}/id_ruim", 400, "id inválido")
            http(A, "7.1 PUT status=resolvido -> 200", "PUT", f"{u}/{id_}", 200, '"status": "resolvido"',
                 json={"status": "resolvido"})
            http(A, "7.1 DELETE -> 200 'Removido'", "DELETE", f"{u}/{id_}", 200, "Removido")
            http(A, "7.1 GET depois do DELETE -> 404", "GET", f"{u}/{id_}", 404)

            rodar("aula07", "popular_incidentes.py")
            todos = list(db.incidentes.find())
            ordenado = lambda l: [x["criado_em"] for x in l] == sorted((x["criado_em"] for x in l), reverse=True)
            http(A, "7.2 tamanho=5&pagina=1 -> 5 mais recentes", "GET", f"{u}?tamanho=5&pagina=1", 200,
                 lambda l: len(l) == 5 and ordenado(l))
            p1 = requests.get(f"{u}?tamanho=5&pagina=1", timeout=10).json()
            http(A, "7.2 pagina=2 traz os 5 seguintes (sem repetir)", "GET", f"{u}?tamanho=5&pagina=2", 200,
                 lambda l: len(l) == 5 and not {x["_id"] for x in l} & {x["_id"] for x in p1}
                 and l[0]["criado_em"] < p1[-1]["criado_em"])
            n_crit = sum(1 for x in todos if x["severidade"] == "critica")
            http(A, f"7.2 severidade=critica -> só críticos ({n_crit})", "GET", f"{u}?severidade=critica", 200,
                 lambda l: len(l) == n_crit and all(x["severidade"] == "critica" for x in l))
            http(A, "7.2 status=aberto&tamanho=3 -> 3 abertos mais recentes", "GET",
                 f"{u}?status=aberto&tamanho=3", 200,
                 lambda l: len(l) == 3 and all(x["status"] == "aberto" for x in l) and ordenado(l))
            http(A, "7.2 parâmetro inválido (tamanho=abc) -> 400", "GET", f"{u}?tamanho=abc", 400)

    if sem_mysql:
        pular(A, "7.3 API de usuários MySQL", sem_mysql)
        return
    with servidor("aula07", "ex7_3_api_usuarios_mysql.py") as url:
        u = f"{url}/api/usuarios"
        http(A, "7.3 POST email já existente -> 409", "POST", u, 409, "email já cadastrado",
             json={"nome": "Outro", "email": "carlos@empresa.com"})
        http(A, "7.3 GET /api/usuarios/999 -> 404", "GET", f"{u}/999", 404)
        http(A, "7.3 POST sem email -> 400", "POST", u, 400, json={"nome": "Sem Email"})
        d = http(A, "7.3 POST novo usuário -> 201", "POST", u, 201, '"id"',
                 json={"nome": "Dani", "email": "dani@empresa.com", "nivel_acesso": 2})
        novo = d.get("id") if isinstance(d, dict) else 0
        http(A, "7.3 GET novo usuário -> 200", "GET", f"{u}/{novo}", 200, "dani@empresa.com")
        http(A, "7.3 PUT nivel_acesso 3 -> 200", "PUT", f"{u}/{novo}", 200, '"nivel_acesso": 3',
             json={"nivel_acesso": 3})
        http(A, "7.3 DELETE -> 200", "DELETE", f"{u}/{novo}", 200, "Removido")
    with servidor("aula07", "ex7_3_api_usuarios_mysql.py", {"MYSQL_PORT": str(porta_livre())}) as url:
        http(A, "7.3 MySQL fora do ar -> 500 'serviço indisponível' sem vazar detalhes", "GET",
             f"{url}/api/usuarios", 500,
             lambda d: d == {"erro": "serviço indisponível"})


def aula08(sem_mysql):
    A = "Aula 8"
    print(f"\n=== {A} — OWASP ===")
    payload = "<script>alert('xss')</script>"
    with servidor("aula08", "ex8_1_dashboard_xss.py") as url:
        r = requests.post(f"{url}/alertas", data={"tipo": "XSS", "severidade": "alta", "descricao": payload},
                          timeout=10)
        html = r.text
        registrar(A, "8.1 payload NÃO aparece cru no HTML (não executa)", payload not in html)
        registrar(A, "8.1 payload aparece escapado como texto",
                  "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html)
        registrar(A, "8.1 headers de segurança (CSP, X-Frame-Options, nosniff)",
                  "default-src 'self'" in r.headers.get("Content-Security-Policy", "")
                  and r.headers.get("X-Frame-Options") == "DENY"
                  and r.headers.get("X-Content-Type-Options") == "nosniff")

    if sem_mysql:
        pular(A, "8.2 login endurecido", sem_mysql)
    else:
        saida = rodar("aula08", "ex8_2_login.py", "--criar-usuarios")
        contem(A, "8.2 cria tabela 'contas' no MySQL", saida, "Tabela 'contas' pronta")
        c = conectar_mysql()
        cur = c.cursor()
        cur.execute("SELECT senha_hash FROM contas WHERE usuario = %s", ("admin",))
        h = cur.fetchone()[0]
        c.close()
        registrar(A, "8.2 senha guardada como hash (não em texto puro)",
                  h != "Cyber@2024" and h.startswith(("scrypt:", "pbkdf2:")), h[:20])
        with servidor("aula08", "ex8_2_login.py") as url:
            u = f"{url}/login"
            m1 = http(A, "8.2 senha errada -> 401 'Credenciais inválidas'", "POST", u, 401,
                      "Credenciais inválidas", json={"usuario": "admin", "senha": "errada"})
            m2 = http(A, "8.2 usuário inexistente -> mesmo 401", "POST", u, 401, "Credenciais inválidas",
                      json={"usuario": "naoexiste", "senha": "x"})
            registrar(A, "8.2 mensagens idênticas (sem user enumeration)", m1 == m2)
            http(A, "8.2 credenciais corretas -> 200 'Login OK'", "POST", u, 200, "Login OK",
                 json={"usuario": "admin", "senha": "Cyber@2024"})
            http(A, "8.2 campos vazios -> 400", "POST", u, 400, json={"usuario": "", "senha": ""})
            codigos = [requests.post(u, json={"usuario": "analista", "senha": f"chute{i}"}, timeout=10).status_code
                       for i in range(6)]
            registrar(A, "8.2 limite de tentativas: 5x 401 e depois 429", codigos == [401] * 5 + [429], str(codigos))
            http(A, "8.2 SQL injection no usuário não entra", "POST", u, 401, "Credenciais inválidas",
                 json={"usuario": "admin' -- ", "senha": "x"})

    texto = (RAIZ / "aula08/auditoria.md").read_text(encoding="utf-8")
    registrar(A, "8.3 auditoria.md cobre as 5 falhas (A05 SQLi, A05 XSS, A02, A04, A09)",
              all(k in texto for k in ("SQL Injection", "XSS", "A05", "A02", "A04", "A09", "debug=False")))


def aula10(online):
    A = "Aula 10"
    print(f"\n=== {A} — APIs REST ===")
    saida = rodar("aula10", "testar_aula10_offline.py")
    contem(A, "10.x teste offline (respostas simuladas) — NVD, GitHub, cache e backoff", saida,
           "CVSS: 10.0 (CRITICAL)", "CVE não encontrada", "timeout", "limite de requisições atingido",
           "[CACHE]", "Rate limit; aguardando", "Cache hits: 1 | Internos: 1")
    if online["NVD"]:
        pular(A, "10.1 [internet] NVD real", online["NVD"])
    else:
        saida = rodar("aula10", "ex10_1_nvd.py", "CVE-2021-44228", "CVE-2099-99999")
        contem(A, "10.1 [internet] CVE-2021-44228 -> CVSS 10.0 CRITICAL (Log4j)", saida,
               "CVSS: 10.0 (CRITICAL)", "Log4j")
        contem(A, "10.1 [internet] CVE inexistente -> 'CVE não encontrada'", saida, "CVE não encontrada")
    if online["GitHub"]:
        pular(A, "10.2 [internet] GitHub real", online["GitHub"])
    else:
        saida = rodar("aula10", "ex10_2_github.py",
                      entrada="1\noctocat\n2\noctocat\n3\noctocat\nHello-World\n4\n5\n")
        contem(A, "10.2 [internet] perfil, repositórios, detalhe e JSON salvo", saida,
               "=== Perfil: octocat ===", "=== Repositórios ===", "octocat/Hello-World",
               "Resultados salvos em github_octocat.json")
        (RAIZ / "aula10/github_octocat.json").unlink(missing_ok=True)
    if online["ipinfo"]:
        pular(A, "10.3 [internet] ipinfo real", online["ipinfo"])
    else:
        saida = rodar("aula10", "ex10_3_enriquecedor.py")
        contem(A, "10.3 [internet] relatório com cache e IP interno não consultado", saida,
               "Mountain View", "Rede Interna (não consultado)", "[CACHE]", "Cache hits: 1 | Internos: 1")


def aula12():
    A = "Aula 12"
    print(f"\n=== {A} — scikit-learn avançado ===")
    saida = rodar("aula12", "ex12_1_pipeline.py")
    contem(A, "12.1 validação cruzada 5 folds com média e desvio", saida,
           r"Acurácia: \d\.\d\d \(\+/- \d\.\d\d\)", regex=True)
    registrar(A, "12.1 5 scores (um por fold)", len(re.findall(r"\d\.\d+", saida.split("\n")[0])) == 5)
    saida = rodar("aula12", "ex12_2_torneio.py")
    contem(A, "12.2 compara RandomForest, SVM e KNN e declara vencedor", saida,
           "RandomForest:", "SVM:", "KNN:", "Vencedor:")
    contem(A, "12.2 GridSearch mostra melhores parâmetros", saida, "Melhores parâmetros:")
    saida = rodar("aula12", "ex12_3_persistencia.py")
    contem(A, "12.3 salva .pkl e mostra SHA-256 de 64 caracteres", saida,
           r"Hash SHA-256: [0-9a-f]{64}\b", regex=True)
    contem(A, "12.3 hash confere e prevê [1]", saida, "Hash confere: modelo íntegro. Previsão de teste: [1]")
    saida = rodar("aula12", "ex12_3_persistencia.py", "--adulterar")
    contem(A, "12.3 arquivo adulterado -> ALERTA e não carrega", saida, "ALERTA: arquivo do modelo foi modificado!")
    registrar(A, "12.3 modelo adulterado NÃO é usado para prever", "Previsão de teste" not in saida)
    for f in ("modelo_seguranca.pkl", "modelo_seguranca.sha256"):
        (RAIZ / "aula12" / f).unlink(missing_ok=True)


def aula13():
    A = "Aula 13"
    print(f"\n=== {A} — LLM ===")
    mock = dict(ENV, LLM_MOCK="1")
    saida = rodar("aula13", "ex13_1_chatbot.py", entrada="O que é XSS?\nE como prevenir?\n/sair\n", env=mock)
    contem(A, "13.1 [simulado] responde e usa o contexto na 2ª pergunta", saida,
           "Cross-Site Scripting", "Para prevenir XSS", "Assistente: Até logo!")
    saida = rodar("aula13", "ex13_2_classificador_lote.py", env=mock)
    contem(A, "13.2 [simulado] NORMAL / CRITICO (path traversal) / SUSPEITO (brute force)", saida,
           r"\[NORMAL\]\s+GET /index\.html", r"\[CRITICO\]\s+GET /\.\./\.\./etc/passwd",
           r"\[SUSPEITO\]\s+POST /login", "=== Resumo === NORMAL:1 | SUSPEITO:1 | CRITICO:1", regex=True)
    sem_rede = dict(ENV, OPENAI_API_KEY="sk-invalida", OPENAI_BASE_URL="http://127.0.0.1:9", LLM_MOCK="0")
    saida = rodar("aula13", "ex13_2_classificador_lote.py", env=sem_rede)
    contem(A, "13.2 fallback por regras quando a API falha", saida,
           "regras (API falhou)", "=== Resumo === NORMAL:1 | SUSPEITO:1 | CRITICO:1")
    saida = rodar("aula13", "ex13_3_prompt_injection.py", env=mock)
    contem(A, "13.3 injeção funciona no classificador ingênuo", saida, "1) Classificador ingênuo  -> NORMAL")
    contem(A, "13.3 classificador seguro resiste (SUSPEITO)", saida, "2) Classificador seguro   -> SUSPEITO")
    registrar(A, "13.3 respostas fora do formato são rejeitadas", saida.count("-> rejeitada") == 2)

    if not ENV.get("OPENAI_API_KEY"):
        pular(A, "13.x OpenAI real", "OPENAI_API_KEY não definida")
        return
    real = dict(ENV)
    real.pop("LLM_MOCK", None)
    saida = rodar("aula13", "ex13_1_chatbot.py", entrada="O que é XSS?\nE como prevenir?\n/sair\n", env=real)
    registrar(A, "13.1 [OpenAI] chatbot responde sem erro", "Até logo!" in saida and "[erro" not in saida,
              saida[-800:])
    saida = rodar("aula13", "ex13_2_classificador_lote.py", env=real)
    m = re.search(r"NORMAL:(\d) \| SUSPEITO:(\d) \| CRITICO:(\d)", saida)
    registrar(A, "13.2 [OpenAI] classifica os 3 logs e o path traversal não sai NORMAL",
              bool(m) and sum(map(int, m.groups())) == 3 and not re.search(r"\[NORMAL\]\s+GET /\.\.", saida),
              saida[-800:])
    saida = rodar("aula13", "ex13_3_prompt_injection.py", env=real)
    registrar(A, "13.3 [OpenAI] classificador seguro não aceita NORMAL para o log malicioso",
              "2) Classificador seguro   -> NORMAL" not in saida and "2) Classificador seguro" in saida, saida[-800:])


# ---------------------------------------------------------------------- main ---
def main():
    inicio = time.time()
    print("Preparando ambiente de teste...")
    sem_mysql = preparar_mysql()
    sem_mongo = preparar_mongo()
    online = sites_acessiveis()
    print(f"  MySQL:    {'OK (banco ' + BANCO_TESTE + ')' if not sem_mysql else sem_mysql}")
    print(f"  MongoDB:  {'OK (banco ' + BANCO_TESTE + ')' if not sem_mongo else sem_mongo}")
    for nome, motivo in online.items():
        print(f"  {nome + ':':<9} {motivo or 'OK'}")
    print(f"  OpenAI:   {'chave definida' if ENV.get('OPENAI_API_KEY') else 'sem chave (só modo simulado)'}")

    aula01(sem_mysql)
    aula02(sem_mongo)
    aula03(sem_mysql)
    aula04()
    aula06()
    aula07(sem_mongo, sem_mysql)
    aula08(sem_mysql)
    aula10(online)
    aula12()
    aula13()

    contagem = {s: sum(1 for r in resultados if r[2] == s) for s in ("OK", "FALHOU", "PULADO")}
    print("\n" + "=" * 70)
    print(f"RESULTADO: {contagem['OK']} OK | {contagem['FALHOU']} FALHOU | {contagem['PULADO']} PULADO"
          f"   ({time.time() - inicio:.0f}s)")
    for aula in dict.fromkeys(r[0] for r in resultados):
        linhas = [r for r in resultados if r[0] == aula]
        ok = sum(r[2] == "OK" for r in linhas)
        extra = "".join(f", {n} {s.lower()}" for s in ("FALHOU", "PULADO")
                        if (n := sum(r[2] == s for r in linhas)))
        print(f"  {aula:<8} {ok}/{len(linhas)} OK{extra}")
    if contagem["FALHOU"]:
        print("\nFalhas:")
        for aula, nome, status, det in resultados:
            if status == "FALHOU":
                print(f"  - {aula}: {nome}\n      {det[:600]}")
    sys.exit(1 if contagem["FALHOU"] else 0)


if __name__ == "__main__":
    main()
