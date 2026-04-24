"""
SQLite database operations для аналитического приложения.
Управляет таблицами uploads и transactions с использованием контекстных менеджеров.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "db/analytics.db")


def get_db_connection():
    """Создает подключение к SQLite базе данных с поддержкой Row фабрики."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Инициализирует базу данных, создавая таблицы uploads и transactions.
    Таблица uploads: хранит информацию о загруженных файлах.
    Таблица transactions: хранит данные о транзакциях (продукты, суммы и т.д.).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Создаем таблицу uploads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                product TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("✓ База данных инициализирована успешно")


def save_dataframe(df: pd.DataFrame, filename: str) -> int:
    """
    Сохраняет DataFrame в таблицу transactions и регистрирует загрузку в таблицу uploads.
    
    Args:
        df: pandas DataFrame с колонками (date, product, category, amount, quantity)
        filename: имя загруженного файла
    
    Returns:
        int: ID загрузки (upload_id) для последующих запросов
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Регистрируем загрузку в таблицу uploads
        cursor.execute(
            "INSERT INTO uploads (filename, uploaded_at) VALUES (?, ?)",
            (filename, datetime.now().isoformat())
        )
        upload_id = cursor.lastrowid
        
        # Вставляем данные транзакций
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO transactions 
                (upload_id, date, product, category, amount, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                upload_id,
                str(row.get('date', '')),
                str(row.get('product', '')),
                str(row.get('category', '')),
                float(row.get('amount', 0)),
                int(row.get('quantity', 0))
            ))
        
        conn.commit()
        print(f"✓ Данные сохранены (upload_id: {upload_id}, строк: {len(df)})")
        return upload_id


def get_data(upload_id: int) -> pd.DataFrame:
    """
    Получает данные транзакций для конкретной загрузки.
    
    Args:
        upload_id: ID загрузки
    
    Returns:
        pd.DataFrame: таблица с данными транзакций или пустой DataFrame если upload_id не найден
    """
    with get_db_connection() as conn:
        query = """
            SELECT id, date, product, category, amount, quantity 
            FROM transactions 
            WHERE upload_id = ?
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn, params=(upload_id,))
        print(f"✓ Загружены данные для upload_id {upload_id} ({len(df)} строк)")
        return df


def list_uploads() -> pd.DataFrame:
    """
    Возвращает список всех загруженных файлов с информацией о времени загрузки.
    
    Returns:
        pd.DataFrame: таблица с колонками (id, filename, uploaded_at, row_count)
    """
    with get_db_connection() as conn:
        query = """
            SELECT 
                u.id,
                u.filename,
                u.uploaded_at,
                COUNT(t.id) as row_count
            FROM uploads u
            LEFT JOIN transactions t ON u.id = t.upload_id
            GROUP BY u.id
            ORDER BY u.uploaded_at DESC
        """
        df = pd.read_sql_query(query, conn)
        print(f"✓ Получен список загрузок ({len(df)} файлов)")
        return df


def delete_upload(upload_id: int) -> bool:
    """
    Удаляет загрузку и все связанные транзакции.
    
    Args:
        upload_id: ID загрузки для удаления
    
    Returns:
        bool: True если успешно, False если upload_id не найден
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM uploads WHERE id = ?", (upload_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✓ Загрузка {upload_id} удалена")
            return True
        return False


def get_upload_stats(upload_id: int) -> dict:
    """
    Возвращает статистику по загрузке (сумма, количество, категории).
    
    Args:
        upload_id: ID загрузки
    
    Returns:
        dict: статистика (total_amount, total_quantity, category_count, row_count)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                SUM(amount) as total_amount,
                SUM(quantity) as total_quantity,
                COUNT(DISTINCT category) as category_count,
                COUNT(*) as row_count
            FROM transactions
            WHERE upload_id = ?
        """, (upload_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'total_amount': row[0] or 0,
                'total_quantity': row[1] or 0,
                'category_count': row[2] or 0,
                'row_count': row[3] or 0
            }
        return {'total_amount': 0, 'total_quantity': 0, 'category_count': 0, 'row_count': 0}
