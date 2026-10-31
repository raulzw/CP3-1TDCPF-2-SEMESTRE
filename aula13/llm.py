"""Cliente LLM compartilhado pelos exercícios da Aula 13.

* Com OPENAI_API_KEY definida -> usa a API real da OpenAI (modelo em OPENAI_MODEL, padrão gpt-4o-mini).
* Sem chave (ou LLM_MOCK=1)   -> usa um "LLM simulado" por regras, com a MESMA interface,
  como a própria apostila sugere ("Sem API key? ... função mock").
A chave NUNCA fica no código.
"""
import os
import re

MODELO = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ROTULOS = ("NORMAL", "SUSPEITO", "CRITICO")


class ErroLLM(Exception):
    pass


def usando_mock():
    return os.environ.get("LLM_MOCK") == "1" or not os.environ.get("OPENAI_API_KEY")


def _cliente():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=30, max_retries=2)


def chat(mensagens, temperature=0.2, max_tokens=400):
    """Envia a lista de mensagens [{'role':..., 'content':...}] e devolve o texto da resposta."""
    if usando_mock():
        return _chat_mock(mensagens)
    try:
        resp = _cliente().chat.completions.create(
            model=MODELO, messages=mensagens, temperature=temperature, max_tokens=max_tokens)
        return resp.choices[0].message.content.strip()
    except Exception as e:  # openai.APIError, timeout, autenticação...
        raise ErroLLM(f"{type(e).__name__}: {e}") from e


# ---------------------------------------------------------------- LLM simulado ---
RESPOSTAS_MOCK = {
    "xss": "Cross-Site Scripting (XSS) é quando a aplicação devolve entrada do usuário sem escapar, "
           "permitindo que JavaScript malicioso rode no navegador da vítima.",
    "sql": "SQL Injection é a injeção de comandos SQL por meio de entradas concatenadas na query. "
           "Previna com queries parametrizadas.",
    "phishing": "Phishing é um golpe em que o atacante se passa por uma entidade confiável para "
                "roubar credenciais ou instalar malware.",
    "ransomware": "Ransomware é um malware que criptografa os dados da vítima e exige resgate.",
}
PREVENCAO_MOCK = {
    "xss": "Para prevenir XSS, escape toda saída (Jinja2 já faz isso), valide a entrada e use "
           "Content-Security-Policy.",
    "sql": "Para prevenir SQL Injection, use sempre queries parametrizadas e o princípio do menor privilégio.",
    "phishing": "Para prevenir phishing, treine usuários, use MFA e configure SPF/DKIM/DMARC.",
    "ransomware": "Para prevenir ransomware, mantenha backups offline, aplique patches e restrinja privilégios.",
}


def _chat_mock(mensagens):
    sistema = next((m["content"] for m in mensagens if m["role"] == "system"), "")
    ultima = mensagens[-1]["content"]
    if "CLASSIFICACAO" in sistema:
        return _classificar_mock(ultima)

    # Chatbot: usa o histórico para resolver perguntas de acompanhamento ("E como prevenir?")
    texto = ultima.lower()
    assunto = next((k for k in RESPOSTAS_MOCK if k in texto), None)
    if assunto is None:
        for m in reversed(mensagens[:-1]):
            assunto = next((k for k in RESPOSTAS_MOCK if k in m["content"].lower()), None)
            if assunto:
                break
    if assunto and re.search(r"preven|evit|proteg|mitig", texto):
        return f"(modo simulado) {PREVENCAO_MOCK[assunto]}"
    if assunto:
        return f"(modo simulado) {RESPOSTAS_MOCK[assunto]}"
    return "(modo simulado) Posso explicar XSS, SQL Injection, phishing ou ransomware."


def _classificar_mock(conteudo):
    """Imita um LLM INGÊNUO: obedece instruções escritas dentro do log (vulnerável a injeção)."""
    injecao = re.search(r"RESPONDA:?\s*(NORMAL|SUSPEITO|CRITICO)", conteudo, re.IGNORECASE)
    if injecao:
        return f"CLASSIFICACAO: {injecao.group(1).upper()} | MOTIVO: conforme instruído no texto"
    rotulo, motivo = classificar_por_regras(conteudo)
    return f"CLASSIFICACAO: {rotulo} | MOTIVO: {motivo}"


# ------------------------------------------------------------ regras (fallback) ---
REGRAS = [
    (r"\.\./|%2e%2e|/etc/passwd", "CRITICO", "path traversal"),
    (r"union\s+select|' ?or ?'?1'?=|;\s*drop\s", "CRITICO", "tentativa de SQL injection"),
    (r"<script|javascript:|onerror=", "CRITICO", "tentativa de XSS"),
    (r"\d+\s*(x|tentativas|attempts)", "SUSPEITO", "possível brute force"),
    (r"status=40[13]|failed|falha", "SUSPEITO", "falha de autenticação/acesso"),
]


def classificar_por_regras(log):
    for padrao, rotulo, motivo in REGRAS:
        if re.search(padrao, log, re.IGNORECASE):
            return rotulo, motivo
    return "NORMAL", "nenhum indicador de ataque"
