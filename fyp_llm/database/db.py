import sqlite3

DB_NAME = "alzheimers.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        education TEXT,
        language TEXT,
        living_situation TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS nurse_qna (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        question TEXT,
        answer TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mmse_qna (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        question TEXT,
        answer TEXT,
        latency REAL
    )
    """)
    cur.execute("""DROP TABLE IF EXISTS mmse_qna""")
    cur.execute("""CREATE TABLE mmse_qna (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        domain TEXT,
        question TEXT,
        answer TEXT,
        latency REAL
    )""")
    


    conn.commit()
    conn.close()
