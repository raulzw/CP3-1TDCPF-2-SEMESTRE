"""Exercício 3.3 — Relatório de alertas por severidade, tipo e top IPs (GROUP BY / ORDER BY)."""
from conexao_mysql import get_conexao

ALERTAS = [
    ("BRUTE_FORCE", "10 falhas SSH", "185.220.101.1", "critica"),
    ("BRUTE_FORCE", "15 falhas RDP", "185.220.101.1", "critica"),
    ("BRUTE_FORCE", "8 falhas web", "185.220.101.1", "alta"),
    ("BRUTE_FORCE", "6 falhas SSH", "91.240.118.172", "alta"),
    ("PORT_SCAN", "scan 1-1024", "45.33.32.156", "alta"),
    ("PORT_SCAN", "scan furtivo", "45.33.32.156", "media"),
    ("PORT_SCAN", "scan UDP", "185.220.101.1", "baixa"),
    ("XSS", "script na URL", "45.33.32.156", "alta"),
    ("XSS", "payload em form", "10.0.0.7", "media"),
    ("SQLI", "' OR 1=1 no login", "91.240.118.172", "critica"),
]


def popular(conexao):
    cur = conexao.cursor()
    cur.execute("DROP TABLE IF EXISTS alertas")
    cur.execute("""
        CREATE TABLE alertas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo VARCHAR(50), descricao TEXT, ip_origem VARCHAR(45),
            severidade ENUM('baixa','media','alta','critica'),
            status VARCHAR(20) DEFAULT 'aberto',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.executemany(
        "INSERT INTO alertas (tipo, descricao, ip_origem, severidade) VALUES (%s, %s, %s, %s)", ALERTAS)
    conexao.commit()
    cur.close()


def consultar(conexao, sql, params=()):
    cur = conexao.cursor()
    cur.execute(sql, params)
    linhas = cur.fetchall()
    cur.close()
    return linhas


if __name__ == "__main__":
    conexao = get_conexao()
    try:
        popular(conexao)
        por_sev = consultar(conexao, """
            SELECT severidade, COUNT(*) FROM alertas GROUP BY severidade
            ORDER BY FIELD(severidade, 'critica', 'alta', 'media', 'baixa')""")
        por_tipo = consultar(conexao, """
            SELECT tipo, COUNT(*) AS total FROM alertas GROUP BY tipo ORDER BY total DESC, tipo""")
        top_ips = consultar(conexao, """
            SELECT ip_origem, COUNT(*) AS total FROM alertas GROUP BY ip_origem
            ORDER BY total DESC LIMIT %s""", (5,))
    finally:
        conexao.close()

    print("=== Por severidade ===  " + " | ".join(f"{s}: {n}" for s, n in por_sev))
    print("=== Por tipo ===        " + " | ".join(f"{t}: {n}" for t, n in por_tipo))
    print("=== Top IPs de origem ===")
    for ip, n in top_ips:
        print(f"{ip:<15}-> {n} alertas")
