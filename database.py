# データベース管理モジュール（Supabase PostgreSQL）

import json
from datetime import datetime

import streamlit as st
import psycopg2
import psycopg2.extras


def get_connection():
    """データベース接続を取得"""
    conn = psycopg2.connect(st.secrets["database"]["url"])
    return conn


def init_db():
    """データベースの初期化（テーブル作成）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW(),
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
    cursor.close()
    conn.close()


def save_quote(quote_date, recipient, retailer, staff, sales_area, products, notes=""):
    """見積データを保存"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quotes (quote_date, recipient, retailer, staff, sales_area, products_json, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        quote_date,
        recipient,
        retailer,
        staff,
        sales_area,
        json.dumps(products, ensure_ascii=False),
        notes
    ))

    quote_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return quote_id


def get_all_quotes():
    """全ての見積履歴を取得"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM quotes ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    quotes = []
    for row in rows:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        # created_atを文字列に変換
        if quote.get('created_at'):
            quote['created_at'] = quote['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if quote.get('quote_date'):
            quote['quote_date'] = str(quote['quote_date'])
        quotes.append(quote)

    return quotes


def get_quote_by_id(quote_id):
    """IDで見積を取得"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM quotes WHERE id = %s", (quote_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        if quote.get('created_at'):
            quote['created_at'] = quote['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if quote.get('quote_date'):
            quote['quote_date'] = str(quote['quote_date'])
        return quote
    return None


def delete_quote(quote_id):
    """見積を削除"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM quotes WHERE id = %s", (quote_id,))

    conn.commit()
    cursor.close()
    conn.close()


def search_quotes(keyword=None, start_date=None, end_date=None, staff=None):
    """見積を検索"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = "SELECT * FROM quotes WHERE 1=1"
    params = []

    if keyword:
        query += " AND (recipient LIKE %s OR retailer LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if start_date:
        query += " AND quote_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND quote_date <= %s"
        params.append(end_date)

    if staff:
        query += " AND staff = %s"
        params.append(staff)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    quotes = []
    for row in rows:
        quote = dict(row)
        quote['products'] = json.loads(quote['products_json'])
        if quote.get('created_at'):
            quote['created_at'] = quote['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if quote.get('quote_date'):
            quote['quote_date'] = str(quote['quote_date'])
        quotes.append(quote)

    return quotes


# 初期化を実行
init_db()
