"""Testa a Aula 10 SEM internet, simulando as respostas das APIs (unittest.mock).
Para o teste real, basta rodar cada ex10_*.py normalmente com internet.
"""
from unittest import mock

import requests

import ex10_1_nvd as nvd
import ex10_2_github as gh
import ex10_3_enriquecedor as enr


def resposta(status=200, json_=None, headers=None):
    r = mock.Mock(status_code=status, headers=headers or {})
    r.json.return_value = json_
    r.raise_for_status = mock.Mock(side_effect=None if status < 400 else
                                   requests.HTTPError(response=r))
    return r


LOG4SHELL = {"vulnerabilities": [{"cve": {
    "id": "CVE-2021-44228",
    "descriptions": [{"lang": "en", "value": "Apache Log4j2 JNDI features ... remote code execution ..."}],
    "metrics": {"cvssMetricV31": [{"cvssData": {"version": "3.1", "baseScore": 10.0,
                                                "baseSeverity": "CRITICAL"}}]}}}]}

print("=== 10.1 NVD ===")
with mock.patch("requests.get", side_effect=[resposta(json_=LOG4SHELL),
                                             resposta(json_={"vulnerabilities": []}),
                                             requests.Timeout()]):
    nvd.imprimir("CVE-2021-44228")
    nvd.imprimir("CVE-2099-99999")
    nvd.imprimir("CVE-2021-44228")
nvd.imprimir("isso-nao-e-cve")

print("\n=== 10.2 GitHub ===")
perfil = {"login": "torvalds", "name": "Linus Torvalds", "public_repos": 7, "followers": 230000}
repos = [{"name": "subsurface", "stargazers_count": 2200, "language": "C++"},
         {"name": "linux", "stargazers_count": 180000, "language": "C"}]
with mock.patch("requests.get", side_effect=[resposta(json_=perfil), resposta(json_=repos)]):
    gh.imprimir_perfil(gh.buscar_usuario("torvalds"))
    gh.imprimir_repos(gh.listar_repos("torvalds"))
with mock.patch("requests.get", return_value=resposta(403, {}, {"X-RateLimit-Remaining": "0",
                                                                 "X-RateLimit-Reset": "1793300000",
                                                                 "Retry-After": "0"})):
    try:
        gh.buscar_usuario("octocat")
    except gh.ErroAPI as e:
        print(f"Erro: {e}")

print("\n=== 10.3 Enriquecedor ===")
infos = {"8.8.8.8": {"city": "Mountain View", "country": "US", "org": "AS15169 Google LLC"},
         "1.1.1.1": {"city": "Brisbane", "country": "AU", "org": "AS13335 Cloudflare, Inc."},
         "185.220.101.1": {"city": "Berlin", "country": "DE", "org": "AS60729 Tor exit"}}
chamadas = []


def falso_get(url, params=None, timeout=None):
    chamadas.append(url)
    ip = url.split("/")[3]
    if ip == "1.1.1.1" and chamadas.count(url) == 1:
        return resposta(429)  # primeira tentativa bate no rate limit
    return resposta(json_=infos[ip])


with mock.patch("requests.get", side_effect=falso_get), mock.patch("time.sleep"):
    enr.relatorio(["8.8.8.8", "1.1.1.1", "185.220.101.1", "192.168.1.10", "8.8.8.8"])
