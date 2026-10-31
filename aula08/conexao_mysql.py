"""Conexão com o MySQL. Credenciais SEMPRE via variáveis de ambiente."""
import os

import mysql.connector


def get_conexao():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "seguranca"),
        connection_timeout=5,
    )
