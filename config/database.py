import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "lostlink_db"), charset="utf8mb4", use_unicode=True,
        autocommit=False,
    )

def query(sql, params=(), one=False):
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchone() if one else cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()

def execute(sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()
