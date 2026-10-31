# Coding for Security — CP3: exercícios da apostila (2º semestre)

Resolução de todos os exercícios de fim de aula da apostila do 2º semestre

## Estrutura

| Pasta | Aula | Exercícios |
|-------|------|-----------|
| `aula01/` | Bancos de dados: SQL, NoSQL e CAP | `ex1_1_schema_vulns.sql`, `ex1_2_crud_alertas.sql`, `decisoes_cap.md` |
| `aula02/` | MongoDB com PyMongo | `ex2_1_inventario.py`, `ex2_2_ingestao_logs.py`, `ex2_3_consulta.py` |
| `aula03/` | MySQL com mysql-connector | `ex3_1_usuarios.py`, `ex3_2_sqli_poc.py`, `ex3_3_relatorio_alertas.py` |
| `aula04/` | Machine Learning (scikit-learn) | `ex4_1_phishing.py`, `ex4_2_anomalias.py`, `ex4_3_matriz_confusao.py` |
| `aula06/` | APIs web com Flask | `ex6_1_api_usuarios.py`, `ex6_2_analisar_senha.py`, `ex6_3_checar_ip.py` |
| `aula07/` | Flask + MongoDB/MySQL | `ex7_1_7_2_api_incidentes.py` (7.1 e 7.2), `popular_incidentes.py`, `ex7_3_api_usuarios_mysql.py` |
| `aula08/` | Web e segurança (OWASP) | `ex8_1_dashboard_xss.py`, `ex8_2_login.py`, `auditoria.md` (8.3) |
| `aula10/` | APIs RESTful | `ex10_1_nvd.py`, `ex10_2_github.py`, `ex10_3_enriquecedor.py` |
| `aula12/` | scikit-learn avançado | `ex12_1_pipeline.py`, `ex12_2_torneio.py`, `ex12_3_persistencia.py` |
| `aula13/` | LLMs para segurança | `ex13_1_chatbot.py`, `ex13_2_classificador_lote.py`, `ex13_3_prompt_injection.py`, `prompt_injection.md` |
| `dados/` | — | `auth.log` de exemplo (23 linhas, mesmo formato da GS do 1º semestre) |

Cada pasta com APIs tem um `testar_auladXX.py` que roda a sequência de testes do enunciado
pelo `test_client` do Flask, sem precisar subir servidor nem usar `curl`.

## Testar tudo de uma vez

`testar_tudo.py` roda **todos** os exercícios e confere cada um com a saída esperada da apostila:
digita as opções dos menus, sobe cada API Flask e faz as requisições HTTP de verdade, usa MySQL e
MongoDB reais (num banco separado `cp3_teste`, sem mexer no seu `seguranca`) e consulta NVD, GitHub
e ipinfo pela internet. São cerca de 100 verificações em menos de 1 minuto.

```bash
# 1. ambiente Python
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

# 2. bancos (mesmos comandos da seção "Ambiente de Laboratório" da apostila)
docker run -d --name mongo-lab -p 27017:27017 mongo:7
docker run -d --name mysql-lab -p 3306:3306 -e MYSQL_ROOT_PASSWORD=senha -e MYSQL_DATABASE=seguranca mysql:8

# 3. configuração (o .env já vem com MYSQL_PASSWORD=senha)
copy .env.example .env            # Windows  (Linux/Mac: cp .env.example .env)

# 4. rodar
python testar_tudo.py
```

No final aparece um resumo por aula, por exemplo `Aula 7   21/21 OK`. Se algo falhar, o script
mostra o que esperava e o que o programa imprimiu. Testes que dependem de algo ausente (MySQL ou
MongoDB desligado, site fora do ar, sem `OPENAI_API_KEY`) aparecem como **PULADO**, não como falha.
Com `OPENAI_API_KEY` no `.env`, a Aula 13 também é testada com a OpenAI real.

Sem Docker, dá para instalar o MySQL Community Server e o MongoDB Community Server normalmente;
basta ajustar usuário e senha no `.env`.

## Como rodar cada exercício

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Rodando à mão, os scripts são executados **de dentro da pasta da aula** (eles importam módulos vizinhos):

```bash
cd aula04
python ex4_1_phishing.py
```

### Bancos de dados

Credenciais vêm de variáveis de ambiente (veja `.env.example`), nunca do código.

- **MongoDB** (Aulas 2 e 7): `MONGO_URI` (padrão `mongodb://localhost:27017/`).
  Sem servidor, dá para testar com `USE_MONGOMOCK=1` (MongoDB em memória).
- **MySQL** (Aulas 1, 3, 7.3 e 8.2): `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.
  Os arquivos `.sql` da Aula 1 rodam com `mysql -u root -p < aula01/ex1_1_schema_vulns.sql`.
  Ordem sugerida na Aula 3: `ex3_1` (cria e popula `usuarios`) → `ex3_2` → `ex3_3`.
  Na Aula 8.2: `python ex8_2_login.py --criar-usuarios` antes de subir a API.

### APIs externas e LLM

- Aula 10 consulta NVD, GitHub e ipinfo.io (precisa de internet). Tokens opcionais:
  `NVD_API_KEY`, `GITHUB_TOKEN`, `IPINFO_TOKEN`. `testar_aula10_offline.py` simula as respostas.
- Aula 13 usa a OpenAI se `OPENAI_API_KEY` estiver definida; sem chave, roda com um
  **LLM simulado por regras** com a mesma interface (alternativa sugerida pela própria apostila).

## Saídas obtidas (resumo)

- **2.2** Top IPs: `185.220.101.1 -> 10`, `91.240.118.172 -> 5`, `45.33.32.156 -> 3`; 23 eventos inseridos.
- **3.2** `[INSEGURO] 3 usuários retornados (VAZAMENTO!)` / `[SEGURO] 0 usuários retornados`.
- **4.1** Acurácia 1.00; caso novo `[11,1,1,1,7] -> Phishing`.
- **4.2** Anomalias nas amostras 5 e 8.
- **4.3** Matriz `[[8,0],[1,1]]`, precisão 1.00, recall 0.50, F1 0.67, acurácia 0.90.
- **6.x / 7.x / 8.x** Todos os status codes do enunciado (200, 201, 400, 401, 404, 409, 429, 500).
- **8.1** O payload `<script>alert('xss')</script>` aparece escapado como texto.
- **12.3** Hash SHA-256 confere após recarregar; com `--adulterar`, dispara o alerta.
- **13.3** Classificador ingênuo é rebaixado para NORMAL pela injeção; o endurecido mantém SUSPEITO.

## Boas práticas de segurança aplicadas

Queries sempre parametrizadas · segredos em variáveis de ambiente · `debug=False` ·
validação de entrada e escape de saída · headers de segurança · mensagens de erro genéricas
(sem traceback) · senhas com hash · limite de tentativas · verificação de integridade do `.pkl`
antes de carregar · saída de LLM validada contra lista fixa de rótulos.

### Testar uma API manualmente (como na aula)

```bash
cd aula06
python ex6_1_api_usuarios.py          # deixa rodando e abre outro terminal
curl -X POST http://localhost:5000/api/usuarios -H "Content-Type: application/json" -d "{\"nome\":\"Ana\",\"email\":\"ana@x.com\",\"nivel\":5}"
curl http://localhost:5000/api/usuarios/1
```
Para usar outra porta: defina `PORT=5001` antes de rodar (no Mac a 5000 costuma estar ocupada).
