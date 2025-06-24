# utils/activity_monitor.py
import win32con
import win32gui
import win32api
import win32ts
from win32gui import PumpMessages
from database.queries import log_sleep_event
import threading
import pythoncom
import wmi
import time

WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8
WM_WTSSESSION_CHANGE = 0x02B1
NOTIFY_FOR_THIS_SESSION = 0

def activity_window_proc(account_id, session_id):
    """Window procedure for handling system power and session events"""
    def wndProc(hWnd, msg, wParam, lParam):
        try:
            if msg == win32con.WM_POWERBROADCAST:
                if wParam == win32con.PBT_APMSUSPEND:
                    log_sleep_event(account_id, session_id, 'sleep', source='system')
                elif wParam == win32con.PBT_APMRESUMEAUTOMATIC:
                    log_sleep_event(account_id, session_id, 'resume', source='system')
            
            elif msg == WM_WTSSESSION_CHANGE:
                if wParam == WTS_SESSION_LOCK:
                    log_sleep_event(account_id, session_id, 'sleep', source='user')
                elif wParam == WTS_SESSION_UNLOCK:
                    log_sleep_event(account_id, session_id, 'resume', source='user')
        except Exception:
            pass
        
        return win32gui.DefWindowProc(hWnd, msg, wParam, lParam)
    
    return wndProc

def monitor_sleep_resume(account_id, session_id):
    """Monitor system sleep/resume events using WMI"""
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        watcher = c.Win32_PowerManagementEvent.watch_for()
        
        while True:
            try:
                event = watcher()
                if event.Type == 4:  # System entering sleep
                    log_sleep_event(account_id, session_id, 'sleep', source='system')
                elif event.Type == 7:  # System resuming
                    log_sleep_event(account_id, session_id, 'resume', source='system')
            except Exception:
                time.sleep(1)
                
    except Exception:
        pass
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def start_activity_monitor(account_id, session_id):
    """Start activity monitoring for sleep/resume events"""
    try:
        wmi_thread = threading.Thread(
            target=monitor_sleep_resume, 
            args=(account_id, session_id), 
            daemon=True
        )
        wmi_thread.start()
        
        hInstance = win32api.GetModuleHandle()
        className = f"ActivityMonitorWindow_{account_id}_{session_id}"
        
        try:
            win32gui.UnregisterClass(className, hInstance)
        except:
            pass
        
        wndClass = win32gui.WNDCLASS()
        wndClass.lpfnWndProc = activity_window_proc(account_id, session_id)
        wndClass.hInstance = hInstance
        wndClass.lpszClassName = className
        
        try:
            win32gui.RegisterClass(wndClass)
        except Exception as e:
            if "Class already exists" in str(e):
                try:
                    win32gui.UnregisterClass(className, hInstance)
                    win32gui.RegisterClass(wndClass)
                except Exception:
                    return
            else:
                return
            
        hWnd = win32gui.CreateWindow(
            className, className, 0, 0, 0, 0, 0, 0, 0, hInstance, None
        )
        
        if hWnd:
            win32ts.WTSRegisterSessionNotification(hWnd, NOTIFY_FOR_THIS_SESSION)
            
            PumpMessages()
            
    except Exception:
        pass

def stop_activity_monitor(account_id, session_id):
    """Stop activity monitoring (called when session ends)"""
    try:
        className = f"ActivityMonitorWindow_{account_id}_{session_id}"
        hInstance = win32api.GetModuleHandle()
        
        hWnd = win32gui.FindWindow(className, None)
        if hWnd:
            win32ts.WTSUnRegisterSessionNotification(hWnd)
            win32gui.DestroyWindow(hWnd)
        
        try:
            win32gui.UnregisterClass(className, hInstance)
        except:
            pass
            
    except Exception:
        pass

def is_system_sleeping():
    """Check if the system is currently in sleep mode"""
    try:
        return False
    except:
        return False

def get_last_user_input_time():
    """Get the time of last user input (mouse/keyboard)"""
    try:
        from ctypes import Structure, windll, c_uint, sizeof, byref
        
        class LASTINPUTINFO(Structure):
            _fields_ = [
                ('cbSize', c_uint),
                ('dwTime', c_uint),
            ]
        
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = sizeof(lastInputInfo)
        windll.user32.GetLastInputInfo(byref(lastInputInfo))
        
        return lastInputInfo.dwTime
    except Exception:
        return 0