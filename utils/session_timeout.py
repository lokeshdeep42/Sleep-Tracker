#utils/session_timeout.py
import threading
import time
from datetime import datetime
from database.queries import end_session

def start_timeout_monitor(account_id, session_id, clock_in_time, timeout_minutes=240):
    def monitor():
        while True:
            now = datetime.now()
            duration = (now - clock_in_time).total_seconds() / 60
            if duration > timeout_minutes:
                print(f"Auto-ending session {session_id} due to timeout.")
                end_session(session_id, now)
                break
            time.sleep(60)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
