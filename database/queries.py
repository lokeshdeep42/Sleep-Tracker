# database/queries.py
from database.db_connection import get_connection
from datetime import datetime
from utils.mac_address import get_mac_address

def start_session(account_id, clock_in_time, mac_address=None):
    """Start a new session with MAC address"""
    if mac_address is None:
        mac_address = get_mac_address()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (account_id, clock_in, session_date, device_mac_address)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
    """, (account_id, clock_in_time, clock_in_time.date(), mac_address))
    session_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return session_id

def end_session(session_id, clock_out_time):
    """End session with complete sleep and idle calculation"""
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate sleep minutes
    sleep_minutes = calculate_sleep_minutes_for_session(session_id)
    
    # Calculate idle minutes
    idle_minutes = calculate_idle_minutes_simple(session_id)

    # Get clock in time
    cursor.execute("SELECT clock_in FROM sessions WHERE id = ?", (session_id,))
    clock_in = cursor.fetchone()[0]
    
    # Calculate total work minutes (total time - sleep - idle)
    total_session_minutes = int((clock_out_time - clock_in).total_seconds() / 60)
    actual_work_minutes = max(0, total_session_minutes - sleep_minutes - idle_minutes)

    # Update session with all calculated times
    cursor.execute("""
        UPDATE sessions
        SET clock_out = ?, total_work_minutes = ?, sleep_minutes = ?
        WHERE id = ?
    """, (clock_out_time, actual_work_minutes, sleep_minutes, session_id))
    
    conn.commit()
    conn.close()
    
    return actual_work_minutes

def calculate_sleep_minutes_for_session(session_id):
    """Calculate total sleep minutes for a session"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, event_time FROM sleep_events
            WHERE session_id = ? AND event_type IN ('sleep', 'resume')
            ORDER BY event_time
        """, (session_id,))
        
        events = cursor.fetchall()
        conn.close()
        
        sleep_minutes = 0
        sleep_start = None
        
        for event_type, event_time in events:
            if event_type == 'sleep':
                sleep_start = event_time
            elif event_type == 'resume' and sleep_start:
                sleep_duration = (event_time - sleep_start).total_seconds() / 60
                sleep_minutes += sleep_duration
                sleep_start = None
        
        return int(sleep_minutes)
        
    except Exception:
        return 0

def log_sleep_event(account_id, session_id, event_type, source='system'):
    """Log sleep events"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sleep_events (account_id, session_id, event_type, event_time, source)
        VALUES (?, ?, ?, ?, ?)
    """, (account_id, session_id, event_type, datetime.now(), source))
    conn.commit()
    conn.close()

def log_idle_event(account_id, session_id, event_type):
    """Log idle events to database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sleep_events (account_id, session_id, event_type, event_time, source)
            VALUES (?, ?, ?, ?, 'idle')
        """, (account_id, session_id, event_type, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception:
        try:
            conn.close()
        except:
            pass
        return False

def calculate_idle_minutes_simple(session_id):
    """Calculate total idle minutes for a session"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, event_time 
            FROM sleep_events 
            WHERE session_id = ? AND event_type IN ('idle_start', 'idle_end')
            ORDER BY event_time
        """, (session_id,))
        
        events = cursor.fetchall()
        conn.close()
        
        total_idle_minutes = 0
        idle_start = None
        
        for event_type, event_time in events:
            if event_type == 'idle_start':
                idle_start = event_time
            elif event_type == 'idle_end' and idle_start:
                idle_duration = (event_time - idle_start).total_seconds() / 60
                total_idle_minutes += idle_duration
                idle_start = None
        
        # If still idle (no end event), calculate current idle time
        if idle_start:
            current_idle = (datetime.now() - idle_start).total_seconds() / 60
            total_idle_minutes += current_idle
        
        return int(total_idle_minutes)
        
    except Exception:
        return 0

def is_session_currently_idle_simple(session_id):
    """Check if session is currently idle"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if session is still active
        cursor.execute("SELECT clock_out FROM sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        if not result or result[0] is not None:
            conn.close()
            return False  # Session is closed
        
        # Get last idle event
        cursor.execute("""
            SELECT TOP 1 event_type, event_time 
            FROM sleep_events 
            WHERE session_id = ? AND event_type IN ('idle_start', 'idle_end')
            ORDER BY event_time DESC
        """, (session_id,))
        
        last_event = cursor.fetchone()
        conn.close()
        
        return last_event and last_event[0] == 'idle_start'
        
    except Exception:
        return False

def get_current_idle_duration_minutes(session_id):
    """Get current idle duration in minutes if currently idle"""
    try:
        if not is_session_currently_idle_simple(session_id):
            return 0
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 1 event_time 
            FROM sleep_events 
            WHERE session_id = ? AND event_type = 'idle_start'
            ORDER BY event_time DESC
        """, (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            idle_start = result[0]
            current_idle = (datetime.now() - idle_start).total_seconds() / 60
            return int(current_idle)
        
        return 0
        
    except Exception:
        return 0

def fetch_all_sessions_with_idle():
    """Fetch all sessions with complete sleep and idle information"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                ISNULL(s.device_mac_address, 'Unknown') as mac_address,
                a.username,
                s.clock_in,
                s.clock_out,
                s.session_date,
                ISNULL(s.total_work_minutes, 0) as work_minutes,
                ISNULL(s.sleep_minutes, 0) as sleep_minutes,
                0 as idle_minutes,
                s.id as session_id,
                s.account_id
            FROM sessions s
            JOIN accounts a ON s.account_id = a.id
            ORDER BY s.session_date DESC, s.clock_in DESC
        """)
        
        sessions = cursor.fetchall()
        conn.close()
        
        # Calculate idle minutes for each session
        enhanced_sessions = []
        for session in sessions:
            session_list = list(session)
            session_id = session_list[8]
            
            # Calculate sleep minutes for active sessions or use stored value
            if session_list[3] is None:
                sleep_minutes = calculate_sleep_minutes_for_session(session_id)
                session_list[6] = sleep_minutes
            
            # Calculate idle minutes
            idle_minutes = calculate_idle_minutes_simple(session_id)
            session_list[7] = idle_minutes
            
            enhanced_sessions.append(tuple(session_list))
        
        return enhanced_sessions
        
    except Exception:
        return []

def get_active_sessions_with_status():
    """Get all active sessions with their current status including idle and sleep info"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, s.account_id, a.username, s.clock_in, s.device_mac_address
            FROM sessions s
            JOIN accounts a ON s.account_id = a.id
            WHERE s.clock_out IS NULL
            ORDER BY s.clock_in DESC
        """)
        
        active_sessions = cursor.fetchall()
        conn.close()
        
        sessions_with_status = []
        for session in active_sessions:
            session_id, account_id, username, clock_in, mac_address = session
            
            # Calculate current sleep and idle info
            sleep_minutes = calculate_sleep_minutes_for_session(session_id)
            idle_minutes = calculate_idle_minutes_simple(session_id)
            is_idle = is_session_currently_idle_simple(session_id)
            current_idle_duration = get_current_idle_duration_minutes(session_id) if is_idle else 0
            
            # Calculate work time
            total_session_minutes = int((datetime.now() - clock_in).total_seconds() / 60)
            work_minutes = max(0, total_session_minutes - sleep_minutes - idle_minutes)
            
            sessions_with_status.append({
                'session_id': session_id,
                'account_id': account_id,
                'username': username,
                'clock_in': clock_in,
                'mac_address': mac_address or 'Unknown',
                'is_idle': is_idle,
                'sleep_minutes': sleep_minutes,
                'idle_minutes': idle_minutes,
                'work_minutes': work_minutes,
                'total_minutes': total_session_minutes,
                'current_idle_duration': current_idle_duration
            })
        
        return sessions_with_status
        
    except Exception:
        return []

def fetch_sessions_by_date_range_with_idle(from_date, to_date):
    """Fetch sessions by date range with idle information"""
    try:
        sessions = fetch_all_sessions_with_idle()
        
        # Filter by date range
        filtered_sessions = []
        for session in sessions:
            session_date = session[4]
            if isinstance(session_date, str):
                session_date = datetime.strptime(session_date, '%Y-%m-%d').date()
            elif hasattr(session_date, 'date'):
                session_date = session_date.date()
            
            if from_date <= session_date <= to_date:
                filtered_sessions.append(session)
        
        return filtered_sessions
        
    except Exception:
        return []

def fetch_all_sessions(from_date=None, to_date=None):
    """Fetch sessions with MAC address"""
    if from_date and to_date:
        return fetch_sessions_by_date_range_with_idle(from_date, to_date)
    else:
        return fetch_all_sessions_with_idle()

def fetch_sessions_by_date_range(from_date, to_date):
    """Fetch sessions by date range"""
    return fetch_sessions_by_date_range_with_idle(from_date, to_date)

def authenticate_user(username, password):
    """Authenticate user and register MAC address"""
    mac_address = get_mac_address()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, role FROM accounts WHERE username = ? AND password = ? AND is_active = 1
    """, (username, password))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE accounts 
            SET registered_mac_address = ? 
            WHERE id = ?
        """, (mac_address, row.id))
        conn.commit()
        conn.close()
        return row.id, row.role
    
    conn.close()
    return None, None

def get_active_session(account_id):
    """Check if user has an active session"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, clock_in FROM sessions 
        WHERE account_id = ? AND clock_out IS NULL
        ORDER BY clock_in DESC
    """, (account_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row.id, row.clock_in
    return None, None

def auto_clock_out_all_sessions(account_id):
    """Automatically clock out all active sessions for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, clock_in FROM sessions 
        WHERE account_id = ? AND clock_out IS NULL
    """, (account_id,))
    
    active_sessions = cursor.fetchall()
    clock_out_time = datetime.now()
    
    for session_id, clock_in_time in active_sessions:
        end_session(session_id, clock_out_time)
    
    conn.close()
    return len(active_sessions)

def fetch_all_users():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, role,
                CASE WHEN is_active = 1 THEN 'Active' ELSE 'Disabled' END AS status,
                ISNULL(registered_mac_address, 'Not Set') as mac_address
            FROM accounts
        """)
        users = cursor.fetchall()
        conn.close()
        return users
    
    except Exception:
        return []

def create_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (username, password, role, is_active)
        VALUES (?, ?, ?, 0)
    """, (username, password, role))
    conn.commit()
    conn.close()

def toggle_user_status(user_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE accounts 
        SET is_active = ? 
        WHERE id = ?
    """, (1 if new_status == 'active' else 0, user_id))
    conn.commit()
    conn.close()
    return True

def delete_user(user_id):
    """Delete a user and all associated data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM sleep_events 
            WHERE session_id IN (
                SELECT id FROM sessions WHERE account_id = ?
            )
        """, (user_id,))
        
        cursor.execute("DELETE FROM sessions WHERE account_id = ?", (user_id,))
        cursor.execute("DELETE FROM feedback WHERE account_id = ?", (user_id,))
        cursor.execute("DELETE FROM accounts WHERE id = ?", (user_id,))
        
        if cursor.rowcount == 0:
            raise Exception("User not found or could not be deleted")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def insert_feedback(account_id, mood, comment, anonymous):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (account_id, mood, comment, is_anonymous)
        VALUES (?, ?, ?, ?)
    """, (account_id, mood, comment, anonymous))
    conn.commit()
    conn.close()

def fetch_all_feedback():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, a.username, f.mood, f.comment, 
               CASE WHEN f.is_anonymous = 1 THEN 'Yes' ELSE 'No' END as anonymous,
               f.submitted_at
        FROM feedback f
        LEFT JOIN accounts a ON f.account_id = a.id
        ORDER BY f.submitted_at DESC
    """)
    results = cursor.fetchall()
    conn.close()
    return results

def fetch_filtered_feedback(start_date=None, end_date=None, mood='All', keyword=''):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT f.id, a.username, f.mood, f.comment, 
               CASE WHEN f.is_anonymous = 1 THEN 'Yes' ELSE 'No' END as anonymous,
               f.submitted_at
        FROM feedback f
        LEFT JOIN accounts a ON f.account_id = a.id
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query += " AND CAST(f.submitted_at AS DATE) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    if mood != "All":
        query += " AND f.mood = ?"
        params.append(mood)
        
    if keyword and keyword.strip():
        query += " AND (a.username LIKE ? OR f.comment LIKE ?)"
        keyword_param = f"%{keyword.strip()}%"
        params.extend([keyword_param, keyword_param])

    query += " ORDER BY f.submitted_at DESC"

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    except Exception:
        conn.close()
        return []
