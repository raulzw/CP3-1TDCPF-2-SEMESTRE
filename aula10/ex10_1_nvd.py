"""Exercício 10.1 — Cliente para a API do NVD (CVEs).

Uso:  python ex10_1_nvd.py CVE-2021-44228 CVE-2099-99999
Opcional: defina NVD_API_KEY (variável de ambiente) para ter um limite de requisições maior.
"""
import os
import re
import sys

import requests

URL_NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PADRAO_CVE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


class CVENaoEncontrada(Exception):
    pass


def extrair_cvss(metricas):
    """Pega a métrica mais recente disponível (v4.0 > v3.1 > v3.0 > v2)."""
    for chave in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if metricas.get(chave):
            m = metricas[chave][0]
            dados = m["cvssData"]
            severidade = dados.get("baseSeverity") or m.get("baseSeverity", "N/A")
            return dados["baseScore"], severidade, dados.get("version", chave)
    return None, "N/A", None


def buscar_cve(cve_id, timeout=30):
    if not PADRAO_CVE.match(cve_id):
        raise ValueError(f"Formato de CVE inválido: {cve_id}")
    headers = {}
    if os.environ.get("NVD_API_KEY"):
        headers["apiKey"] = os.environ["NVD_API_KEY"]
    r = requests.get(URL_NVD, params={"cveId": cve_id.upper()}, headers=headers, timeout=timeout)
    if r.status_code == 404:
        raise CVENaoEncontrada(cve_id)
    r.raise_for_status()
    vulns = r.json().get("vulnerabilities", [])
    if not vulns:  # o NVD costuma responder 200 com lista vazia para CVE inexistente
        raise CVENaoEncontrada(cve_id)
    cve = vulns[0]["cve"]
    descricao = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
    score, severidade, versao = extrair_cvss(cve.get("metrics", {}))
    return {"id": cve["id"], "descricao": descricao, "cvss": score,
            "severidade": severidade, "versao_cvss": versao}


def imprimir(cve_id):
    try:
        info = buscar_cve(cve_id)
    except CVENaoEncontrada:
        print(f"{cve_id}: CVE não encontrada")
    except ValueError as e:
        print(e)
    except requests.Timeout:
        print(f"{cve_id}: tempo esgotado ao consultar o NVD (timeout)")
    except requests.ConnectionError:
        print(f"{cve_id}: sem conexão com o NVD")
    except requests.HTTPError as e:
        print(f"{cve_id}: erro HTTP {e.response.status_code} do NVD")
    else:
        print(info["id"])
        print(f"  CVSS: {info['cvss']} ({info['severidade']})  [v{info['versao_cvss']}]")
        print(f"  Descrição: {info['descricao']}")


if __name__ == "__main__":
    for cve in (sys.argv[1:] or ["CVE-2021-44228", "CVE-2099-99999"]):
        imprimir(cve)
