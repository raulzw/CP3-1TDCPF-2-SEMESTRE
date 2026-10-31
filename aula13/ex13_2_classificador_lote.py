"""Exercício 13.2 — Classificador automático de logs em lote, com fallback por regras.

Uso:
    python ex13_2_classificador_lote.py                 # usa os 3 logs do enunciado
    python ex13_2_classificador_lote.py ../dados/auth.log  # classifica as linhas suspeitas de um arquivo
"""
import sys
from collections import Counter

from classificador import classificar_seguro
from llm import ROTULOS, usando_mock

LOGS_EXEMPLO = [
    "GET /index.html ip=192.168.1.10 status=200",
    "GET /../../etc/passwd ip=91.240.118.172 status=400",
    "POST /login ip=185.220.101.1 status=401 (5x seguidas)",
]


def ler_arquivo(caminho):
    """Agrupa falhas repetidas por IP (5x seguidas vira uma linha) para não gastar chamadas à toa."""
    falhas, outras = Counter(), []
    with open(caminho, encoding="utf-8") as f:
        for linha in (l.strip() for l in f if l.strip()):
            if " FAIL " in linha:
                ip = linha.rsplit("ip=", 1)[-1]
                falhas[ip] += 1
            else:
                outras.append(linha)
    agregadas = [f"Failed login ip={ip} ({n}x seguidas)" for ip, n in falhas.items()]
    return agregadas + outras


def main():
    logs = ler_arquivo(sys.argv[1]) if len(sys.argv) > 1 else LOGS_EXEMPLO
    if usando_mock():
        print("(sem OPENAI_API_KEY — usando LLM simulado)\n")
    contagem = Counter()
    for log in logs:
        rotulo, motivo, origem = classificar_seguro(log)
        contagem[rotulo] += 1
        print(f"{'[' + rotulo + ']':<11}{log[:55]:<57}({motivo}) <{origem}>")
    print("=== Resumo === " + " | ".join(f"{r}:{contagem[r]}" for r in ROTULOS))


if __name__ == "__main__":
    main()
