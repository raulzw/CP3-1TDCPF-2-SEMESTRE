"""Exercício 10.2 — Explorador da API do GitHub com menu.

Opcional: defina GITHUB_TOKEN para aumentar o limite (60 -> 5000 req/h). O token NUNCA vai no código.
"""
import json
import os
import time

import requests

API = "https://api.github.com"


class ErroAPI(Exception):
    pass


def _headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "coding-for-security-cp3"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return h


def requisitar(caminho, params=None, tentativas=3):
    """GET com tratamento de conexão, timeout, 404 e limite (403/429) com backoff exponencial."""
    for i in range(tentativas):
        try:
            r = requests.get(f"{API}{caminho}", params=params, headers=_headers(), timeout=15)
        except requests.Timeout:
            raise ErroAPI("tempo esgotado (timeout)")
        except requests.ConnectionError:
            raise ErroAPI("sem conexão com a API do GitHub")

        if r.status_code == 404:
            raise ErroAPI("não encontrado (404)")
        sem_cota = r.status_code == 429 or (r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0")
        if sem_cota:
            if i == tentativas - 1:
                reset = r.headers.get("X-RateLimit-Reset")
                quando = time.strftime("%H:%M:%S", time.localtime(int(reset))) if reset else "mais tarde"
                raise ErroAPI(f"limite de requisições atingido; tente novamente às {quando}")
            espera = int(r.headers.get("Retry-After", 2 ** i))
            print(f"Limite de requisições; aguardando {espera}s...")
            time.sleep(espera)
            continue
        if r.status_code >= 400:
            raise ErroAPI(f"erro HTTP {r.status_code}")
        return r.json()
    raise ErroAPI("falha após várias tentativas")


def buscar_usuario(usuario):
    return requisitar(f"/users/{usuario}")


def listar_repos(usuario, por_pagina=100):
    """Percorre as páginas até vir uma página vazia."""
    repos, pagina = [], 1
    while True:
        lote = requisitar(f"/users/{usuario}/repos",
                          {"page": pagina, "per_page": por_pagina, "sort": "updated"})
        if not lote:
            break
        repos.extend(lote)
        if len(lote) < por_pagina:
            break
        pagina += 1
    return sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)


def detalhar_repo(usuario, repo):
    return requisitar(f"/repos/{usuario}/{repo}")


def salvar_json(dados, arquivo):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return arquivo


def imprimir_perfil(p):
    print(f"=== Perfil: {p['login']} ===")
    print(f"Nome: {p.get('name') or '-'} | Repos públicos: {p['public_repos']} | Seguidores: {p['followers']}")


def imprimir_repos(repos):
    print("=== Repositórios ===")
    for i, r in enumerate(repos, 1):
        print(f"{i}. {r['name']:<20} ★ {r['stargazers_count']:<8} ({r.get('language') or '-'})")


def menu():
    resultados = {}
    while True:
        print("\n[1] Buscar usuário [2] Listar repositórios [3] Detalhar repositório [4] Salvar em JSON [5] Sair")
        op = input("Opção: ").strip()
        try:
            if op == "1":
                u = input("Usuário: ").strip()
                resultados["perfil"] = buscar_usuario(u)
                resultados["usuario"] = u
                imprimir_perfil(resultados["perfil"])
            elif op == "2":
                u = input("Usuário: ").strip()
                resultados["repos"] = listar_repos(u)
                resultados["usuario"] = u
                imprimir_repos(resultados["repos"])
            elif op == "3":
                d = detalhar_repo(input("Usuário: ").strip(), input("Repositório: ").strip())
                resultados["detalhe"] = d
                print(f"{d['full_name']}: {d.get('description') or '-'}")
                print(f"★ {d['stargazers_count']} | forks {d['forks_count']} | issues abertas "
                      f"{d['open_issues_count']} | linguagem {d.get('language') or '-'}")
            elif op == "4":
                if not resultados:
                    print("Nada para salvar ainda.")
                    continue
                arq = salvar_json(resultados, f"github_{resultados.get('usuario', 'resultado')}.json")
                print(f"Resultados salvos em {arq}")
            elif op == "5":
                break
            else:
                print("Opção inválida.")
        except ErroAPI as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    menu()
