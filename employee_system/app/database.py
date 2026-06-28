from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import config
import sqlite3
import os

# Используем SQLite
DATABASE_URL = config.DATABASE_URL

# Создаем engine для SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Для Native SQL (SQLite)
def get_db_connection():
    conn = sqlite3.connect('./employees.db')
    conn.row_factory = sqlite3.Row
    return conn