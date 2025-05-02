import sqlite3

def create_table():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            code TEXT PRIMARY KEY,
            player1 TEXT,
            player2 TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_room(code, player1):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("INSERT INTO rooms (code, player1) VALUES (?, ?)", (code, player1))
    conn.commit()
    conn.close()

def join_room_by_code(code, player2):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("UPDATE rooms SET player2=? WHERE code=?", (player2, code))
    conn.commit()
    conn.close()

def get_room(code):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("SELECT * FROM rooms WHERE code=?", (code,))
    result = c.fetchone()
    conn.close()
    return result
