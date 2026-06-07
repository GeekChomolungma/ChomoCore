from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database


class MongoClientFactory:
    """
    URI-based MongoClient factory with per-URI singleton caching.

    Usage:
        db = MongoClientFactory.get_db(uri="mongodb://localhost:27017", db_name="market_info")

    One MongoClient per URI is kept alive for the lifetime of the process.
    Call close_all() on shutdown if you need explicit cleanup (optional —
    pymongo closes connections on GC).
    """

    _clients: dict[str, MongoClient] = {}

    @classmethod
    def get_client(cls, uri: str) -> MongoClient:
        if uri not in cls._clients:
            cls._clients[uri] = MongoClient(uri)
        return cls._clients[uri]

    @classmethod
    def get_db(cls, uri: str, db_name: str) -> Database:
        return cls.get_client(uri)[db_name]

    @classmethod
    def close_all(cls) -> None:
        for client in cls._clients.values():
            client.close()
        cls._clients.clear()
