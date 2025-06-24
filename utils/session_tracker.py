#utils/session_tracker.py
import datetime
from database.db_connection import get_connection

def clock_in(account_id):
    now = datetime.datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (account_id, clock_in, session_date)
        VALUES (?, ?, ?)
    """, (account_id, now, now.date()))
    conn.commit()
    conn.close()


def clock_out(account_id):
    now = datetime.datetime.now()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 1 id, clock_in FROM sessions
        WHERE account_id = ? AND clock_out IS NULL
        ORDER BY clock_in DESC
    """, (account_id,))
    session = cursor.fetchone()

    if session:
        session_id = session.id
        clock_in_time = session.clock_in
        total_minutes = int((now - clock_in_time).total_seconds() / 60)

        cursor.execute("""
            UPDATE sessions
            SET clock_out = ?, total_work_minutes = ?
            WHERE id = ?
        """, (now, total_minutes, session_id))
        conn.commit()

    conn.close()


def get_today_sessions(account_id):
    today = datetime.date.today()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sessions
        WHERE account_id = ? AND session_date = ?
        ORDER BY clock_in ASC
    """, (account_id, today))
    rows = cursor.fetchall()
    conn.close()
    return rows