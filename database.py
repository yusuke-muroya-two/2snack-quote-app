# データベース管理モジュール（SQLite）

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# データベースファイルのパス
DB_PATH = Path(__file__).parent / "quote_history.db"


def get_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """データベースの初期化（テーブル作成）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            quote_date DATE NOT NULL,
            recipient TEXT NOT NULL,
            retailer TEXT,
            staff TEXT NOT NULL,
            sales_area TEXT NOT NULL,
            products_json TEXT NOT NULL,
            notes TEXT,
            pdf_filename TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_quote(quote_date, recipient, retailer, staff, sales_area, products, notes=""):
    """見積データを保存"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quotes (quote_date, recipient, retailer, staff, sales_area, products_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        quote_date,
        recipient,
        retailer,
        staff,
        sales_area,
        json.dumps(products, ensure_ascii=False),
        notes
    ))

    quote_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return quote_id


def get_all_quotes():
    """全ての見積履歴を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM quotes ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    quotes = []
    for row in rows:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        quotes.append(quote)

    return quotes


def get_quote_by_id(quote_id):
    """IDで見積を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        return quote
    return None


def delete_quote(quote_id):
    """見積を削除"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))

    conn.commit()
    conn.close()


def search_quotes(keyword=None, start_date=None, end_date=None, staff=None):
    """見積を検索"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM quotes WHERE 1=1"
    params = []

    if keyword:
        query += " AND (recipient LIKE ? OR retailer LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if start_date:
        query += " AND quote_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND quote_date <= ?"
        params.append(end_date)

    if staff:
        query += " AND staff = ?"
        params.append(staff)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    quotes = []
    for row in rows:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        quotes.append(quote)

    return quotes


# 初期化を実行
init_db()
