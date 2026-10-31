"""Exercício 2.1 — CRUD de inventário de ativos no MongoDB (menu)."""
from pymongo.errors import DuplicateKeyError

from conexao_mongo import get_db

ATIVOS_INICIAIS = [
    {"nome": "SRV-WEB01", "tipo": "servidor", "ip": "192.168.1.10", "status": "ativo"},
    {"nome": "PC-RH03", "tipo": "estacao", "ip": "192.168.1.45", "status": "ativo"},
    {"nome": "SW-CORE01", "tipo": "switch", "ip": "192.168.1.1", "status": "inativo"},
]


def preparar_colecao(db):
    col = db["ativos"]
    col.create_index("ip", unique=True)  # impede IP duplicado no próprio banco
    if col.count_documents({}) == 0:
        col.insert_many([dict(a) for a in ATIVOS_INICIAIS])
    return col


def cadastrar(col, nome, tipo, ip, status="ativo"):
    try:
        col.insert_one({"nome": nome, "tipo": tipo, "ip": ip, "status": status})
        return "Ativo cadastrado!"
    except DuplicateKeyError:
        return "Erro: IP já cadastrado!"


def listar(col):
    return list(col.find({}, {"_id": 0}).sort("nome", 1))


def buscar_por_ip(col, ip):
    return col.find_one({"ip": ip}, {"_id": 0})


def atualizar_status(col, ip, status):
    r = col.update_one({"ip": ip}, {"$set": {"status": status}})
    return "Status atualizado!" if r.matched_count else "Erro: ativo não encontrado."


def remover(col, ip):
    r = col.delete_one({"ip": ip})
    return "Ativo removido!" if r.deleted_count else "Erro: ativo não encontrado."


def imprimir_tabela(ativos):
    print(f"{'NOME':<12}{'TIPO':<10}{'IP':<16}STATUS")
    for a in ativos:
        print(f"{a['nome']:<12}{a['tipo']:<10}{a['ip']:<16}{a['status']}")
    print(f"Total: {len(ativos)}")


def menu():
    col = preparar_colecao(get_db())
    while True:
        print("\n[1] Cadastrar [2] Listar [3] Buscar por IP [4] Atualizar status [5] Remover [6] Sair")
        op = input("Opção: ").strip()
        if op == "1":
            print(cadastrar(col, input("Nome: "), input("Tipo: "), input("IP: ")))
        elif op == "2":
            imprimir_tabela(listar(col))
        elif op == "3":
            ativo = buscar_por_ip(col, input("IP: "))
            print(ativo if ativo else "Ativo não encontrado.")
        elif op == "4":
            print(atualizar_status(col, input("IP: "), input("Novo status: ")))
        elif op == "5":
            print(remover(col, input("IP: ")))
        elif op == "6":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
