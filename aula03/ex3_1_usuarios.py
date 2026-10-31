"""Exercício 3.1 — CRUD de usuários e permissões no MySQL (todas as queries parametrizadas)."""
import mysql.connector
from mysql.connector import errorcode

from conexao_mysql import get_conexao

USUARIOS_INICIAIS = [
    ("Carlos Silva", "carlos@empresa.com", 3),
    ("Ana Costa", "ana@empresa.com", 5),
    ("Bruno Lima", "bruno@empresa.com", 1),
]


def preparar(conexao):
    cur = conexao.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            nivel_acesso INT NOT NULL DEFAULT 1 CHECK (nivel_acesso BETWEEN 1 AND 5),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO usuarios (nome, email, nivel_acesso) VALUES (%s, %s, %s)",
                        USUARIOS_INICIAIS)
    conexao.commit()
    cur.close()


def nivel_valido(nivel):
    return isinstance(nivel, int) and 1 <= nivel <= 5


def cadastrar(conexao, nome, email, nivel):
    if not nivel_valido(nivel):
        return "Erro: nível deve estar entre 1 e 5"
    cur = conexao.cursor()
    try:
        cur.execute("INSERT INTO usuarios (nome, email, nivel_acesso) VALUES (%s, %s, %s)",
                    (nome, email, nivel))
        conexao.commit()
        return "Usuário cadastrado!"
    except mysql.connector.IntegrityError as e:
        conexao.rollback()
        if e.errno == errorcode.ER_DUP_ENTRY:
            return "Erro: email já existe"
        raise
    finally:
        cur.close()


def listar(conexao):
    cur = conexao.cursor(dictionary=True)
    cur.execute("SELECT id, nome, email, nivel_acesso FROM usuarios ORDER BY id")
    linhas = cur.fetchall()
    cur.close()
    return linhas


def buscar_por_email(conexao, email):
    cur = conexao.cursor(dictionary=True)
    cur.execute("SELECT id, nome, email, nivel_acesso FROM usuarios WHERE email = %s", (email,))
    linha = cur.fetchone()
    cur.close()
    return linha


def alterar_nivel(conexao, email, nivel):
    if not nivel_valido(nivel):
        return "Erro: nível deve estar entre 1 e 5"
    cur = conexao.cursor()
    cur.execute("UPDATE usuarios SET nivel_acesso = %s WHERE email = %s", (nivel, email))
    conexao.commit()
    afetadas = cur.rowcount
    cur.close()
    return "Nível atualizado!" if afetadas else "Erro: usuário não encontrado (ou nível igual)"


def remover(conexao, email):
    cur = conexao.cursor()
    cur.execute("DELETE FROM usuarios WHERE email = %s", (email,))
    conexao.commit()
    afetadas = cur.rowcount
    cur.close()
    return "Usuário removido!" if afetadas else "Erro: usuário não encontrado"


def ler_nivel():
    try:
        return int(input("Nível (1-5): "))
    except ValueError:
        return -1


def menu():
    conexao = get_conexao()
    preparar(conexao)
    try:
        while True:
            print("\n[1] Cadastrar [2] Listar [3] Buscar por email [4] Promover/rebaixar [5] Remover [6] Sair")
            op = input("Opção: ").strip()
            if op == "1":
                print(cadastrar(conexao, input("Nome: "), input("Email: "), ler_nivel()))
            elif op == "2":
                for u in listar(conexao):
                    print(f"{u['nome']:<13}| {u['email']:<19}| nível {u['nivel_acesso']}")
            elif op == "3":
                u = buscar_por_email(conexao, input("Email: "))
                print(f"{u['nome']} | {u['email']} | nível {u['nivel_acesso']}" if u else "Não encontrado.")
            elif op == "4":
                print(alterar_nivel(conexao, input("Email: "), ler_nivel()))
            elif op == "5":
                print(remover(conexao, input("Email: ")))
            elif op == "6":
                break
            else:
                print("Opção inválida.")
    finally:
        conexao.close()


if __name__ == "__main__":
    menu()
