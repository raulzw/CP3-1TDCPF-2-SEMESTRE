"""Exercício 10.3 — Enriquecedor de IPs com cache, backoff em 429 e classificação privado/público.

Usa a API pública do ipinfo.io (token opcional em IPINFO_TOKEN).
"""
import ipaddress
import os
import time

import requests

BLACKLIST = {"185.220.101.1", "45.33.32.156", "91.240.118.172"}
_cache = {}
estatisticas = {"http": 0, "cache": 0, "internos": 0, "erros": 0}


def eh_privado(ip):
    return ipaddress.ip_address(ip).is_private


def requisicao_com_retry(url, params=None, tentativas=3):
    for i in range(tentativas):
        r = requests.get(url, params=params, timeout=10)
        estatisticas["http"] += 1
        if r.status_code == 429:
            espera = 2 ** i  # 1s, 2s, 4s
            print(f"Rate limit; aguardando {espera}s...")
            time.sleep(espera)
            continue
        r.raise_for_status()
        return r.json()
    return None


def enriquecer(ip):
    """Retorna (linha_formatada, origem) onde origem é 'http', 'cache' ou 'interno'."""
    if eh_privado(ip):
        estatisticas["internos"] += 1
        return f"{ip:<15} -> Rede Interna (não consultado)", "interno"
    if ip in _cache:
        estatisticas["cache"] += 1
        return f"{ip:<15} -> [CACHE] {_cache[ip]}", "cache"

    params = {"token": os.environ["IPINFO_TOKEN"]} if os.environ.get("IPINFO_TOKEN") else None
    try:
        dados = requisicao_com_retry(f"https://ipinfo.io/{ip}/json", params)
    except requests.RequestException as e:
        estatisticas["erros"] += 1
        return f"{ip:<15} -> erro na consulta ({type(e).__name__})", "erro"
    if dados is None:
        estatisticas["erros"] += 1
        return f"{ip:<15} -> limite de requisições excedido", "erro"

    rotulo = "EXTERNO, suspeito" if ip in BLACKLIST else "EXTERNO"
    resumo = f"{dados.get('city', '?')} / {dados.get('country', '?')} / {dados.get('org', '?')} ({rotulo})"
    _cache[ip] = resumo
    return f"{ip:<15} -> {resumo}", "http"


def relatorio(ips):
    for ip in ips:
        try:
            linha, _ = enriquecer(ip)
        except ValueError:
            linha = f"{ip:<15} -> IP inválido"
        print(linha)
    print(f"=== Resumo === Consultas HTTP: {estatisticas['http']} | Cache hits: {estatisticas['cache']} "
          f"| Internos: {estatisticas['internos']} | Erros: {estatisticas['erros']}")


if __name__ == "__main__":
    relatorio(["8.8.8.8", "1.1.1.1", "185.220.101.1", "192.168.1.10", "8.8.8.8"])
