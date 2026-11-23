"""
SentinelX MongoDB Database Connection Manager
Provides PyMongo client pooling, Atlas / local server connection management,
and instantaneous zero-latency mock fallback when local daemon is not running.
"""

import socket
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.app.config import settings

logger = logging.getLogger("sentinelx.database")

_mongo_client = None
_database = None
_is_mock = False

def _is_local_server_running(host: str = "localhost", port: int = 27017) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.15):
            return True
    except OSError:
        return False

def get_client() -> MongoClient:
    global _mongo_client, _is_mock
    if _mongo_client is not None:
        return _mongo_client
        
    uri = settings.MONGODB_URI.strip()
    is_local = "localhost" in uri or "127.0.0.1" in uri
    
    # If configured for localhost but local port is closed, instantly fallback to mongomock
    if is_local and not _is_local_server_running():
        logger.info("Local MongoDB port 27017 inactive; initializing zero-latency in-memory PyMongo store.")
        import mongomock
        _mongo_client = mongomock.MongoClient()
        _is_mock = True
        return _mongo_client
        
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            maxPoolSize=50,
            minPoolSize=5
        )
        client.admin.command('ping')
        logger.info(f"Connected to live MongoDB cluster at {uri.split('@')[-1]}")
        _mongo_client = client
        _is_mock = False
        return _mongo_client
    except Exception as e:
        if settings.USE_MOCK_IF_NO_MONGO:
            logger.info("Live MongoDB unreachable; fallback to in-memory PyMongo store.")
            import mongomock
            _mongo_client = mongomock.MongoClient()
            _is_mock = True
            return _mongo_client
        else:
            raise e

def get_database():
    global _database
    if _database is not None:
        return _database
    client = get_client()
    _database = client[settings.DATABASE_NAME]
    return _database

def get_collection(collection_name: str):
    db = get_database()
    return db[collection_name]

def is_mock_database() -> bool:
    return _is_mock
