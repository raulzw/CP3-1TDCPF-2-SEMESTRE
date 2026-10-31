"""Conexão compartilhada com o MongoDB.

A URI vem da variável de ambiente MONGO_URI (nunca do código).
Se USE_MONGOMOCK=1, usa um MongoDB em memória (mongomock) — útil para testar sem servidor.
"""
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGO_DB", "seguranca")


def get_db():
    if os.environ.get("USE_MONGOMOCK") == "1":
        import mongomock
        client = mongomock.MongoClient()
    else:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")  # falha rápido se o servidor não estiver no ar
    return client[DB_NAME]
