# utils/idle_monitor.py
import threading
import time
from datetime import datetime, timedelta
import win32gui
import win32con
from ctypes import Structure, windll, c_uint, sizeof, byref

class POINT(Structure):
    _fields_ = [("x", c_uint), ("y", c_uint)]

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def get_idle_duration():
    """Get the current idle duration in seconds"""
    try:
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = sizeof(lastInputInfo)
        result = windll.user32.GetLastInputInfo(byref(lastInputInfo))
        
        if not result:
            return 0
            
        current_tick = windll.kernel32.GetTickCount()
        idle_time = (current_tick - lastInputInfo.dwTime) / 1000.0
        
        return idle_time
        
    except Exception:
        return 0

class IdleMonitor:
    def __init__(self, account_id, session_id, idle_threshold_seconds=300):
        self.account_id = account_id
        self.session_id = session_id
        self.idle_threshold = idle_threshold_seconds
        self.is_idle = False
        self.idle_start_time = None
        self.total_idle_time = 0
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start the idle monitoring in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the idle monitoring"""
        self.monitoring = False
        
        if self.is_idle and self.idle_start_time:
            final_idle_time = (datetime.now() - self.idle_start_time).total_seconds()
            self.total_idle_time += final_idle_time
            self._log_idle_event('idle_end')
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                idle_duration = get_idle_duration()
                
                if idle_duration >= self.idle_threshold and not self.is_idle:
                    self.is_idle = True
                    self.idle_start_time = datetime.now()
                    self._log_idle_event('idle_start')
                    
                elif idle_duration < self.idle_threshold and self.is_idle:
                    self.is_idle = False
                    if self.idle_start_time:
                        idle_period = (datetime.now() - self.idle_start_time).total_seconds()
                        self.total_idle_time += idle_period
                        self._log_idle_event('idle_end')
                    self.idle_start_time = None
                    
                time.sleep(10)
                
            except Exception:
                time.sleep(5)
    
    def _log_idle_event(self, event_type):
        """Log idle events to database"""
        try:
            from database.queries import log_idle_event
            log_idle_event(self.account_id, self.session_id, event_type)
        except Exception:
            pass
    
    def get_current_status(self):
        """Get current idle status and total idle time"""
        current_idle_time = self.total_idle_time
        current_idle_duration = 0
        
        if self.is_idle and self.idle_start_time:
            current_session_idle = (datetime.now() - self.idle_start_time).total_seconds()
            current_idle_time += current_session_idle
            current_idle_duration = int(get_idle_duration())
        
        status = {
            'is_idle': self.is_idle,
            'total_idle_minutes': int(current_idle_time / 60),
            'current_idle_duration': current_idle_duration
        }
        
        return status

active_idle_monitors = {}

def start_idle_monitoring(account_id, session_id, idle_threshold_seconds=300):
    """Start idle monitoring for a session"""
    monitor_key = f"{account_id}_{session_id}"
    
    if monitor_key in active_idle_monitors:
        active_idle_monitors[monitor_key].stop_monitoring()
        del active_idle_monitors[monitor_key]
    
    test_idle = get_idle_duration()
    if test_idle is None or test_idle < 0:
        return None
    
    monitor = IdleMonitor(account_id, session_id, idle_threshold_seconds)
    monitor.start_monitoring()
    active_idle_monitors[monitor_key] = monitor
    
    return monitor

def stop_idle_monitoring(account_id, session_id):
    """Stop idle monitoring for a session"""
    monitor_key = f"{account_id}_{session_id}"
    
    if monitor_key in active_idle_monitors:
        active_idle_monitors[monitor_key].stop_monitoring()
        del active_idle_monitors[monitor_key]

def get_idle_status(account_id, session_id):
    """Get current idle status for a session"""
    monitor_key = f"{account_id}_{session_id}"
    
    if monitor_key in active_idle_monitors:
        status = active_idle_monitors[monitor_key].get_current_status()
        return status
    else:
        return {'is_idle': False, 'total_idle_minutes': 0, 'current_idle_duration': 0}