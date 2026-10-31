"""Exercício 3.2 — Prova de conceito DEFENSIVA de SQL Injection (somente banco local de laboratório).

Pré-requisito: tabela 'usuarios' populada (rode o ex3_1_usuarios.py uma vez).
"""
from conexao_mysql import get_conexao


def buscar_inseguro(conexao, nome):
    """VULNERÁVEL: concatena a entrada direto na query. Não use isto em código real."""
    cur = conexao.cursor(dictionary=True)
    cur.execute(f"SELECT id, nome, email FROM usuarios WHERE nome = '{nome}'")
    linhas = cur.fetchall()
    cur.close()
    return linhas


def buscar_seguro(conexao, nome):
    """SEGURO: query parametrizada — o driver envia a entrada como dado, nunca como SQL."""
    cur = conexao.cursor(dictionary=True)
    cur.execute("SELECT id, nome, email FROM usuarios WHERE nome = %s", (nome,))
    linhas = cur.fetchall()
    cur.close()
    return linhas


if __name__ == "__main__":
    entrada_maliciosa = "' OR '1'='1"
    conexao = get_conexao()
    try:
        inseguro = buscar_inseguro(conexao, entrada_maliciosa)
        seguro = buscar_seguro(conexao, entrada_maliciosa)
    finally:
        conexao.close()

    print(f"[INSEGURO] entrada: {entrada_maliciosa}  -> {len(inseguro)} usuários retornados (VAZAMENTO!)")
    print(f"[SEGURO]   entrada: {entrada_maliciosa}  -> {len(seguro)} usuários retornados (defesa OK)")
    print("Conclusão: a query parametrizada tratou a entrada como texto literal.")
    print("Na versão insegura a query virou: ... WHERE nome = '' OR '1'='1'  (condição sempre verdadeira).")
