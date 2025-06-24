# gui/employee_dashboard.py
import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QApplication, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from datetime import datetime
from database.queries import (
    start_session, end_session, insert_feedback, 
    get_active_session, auto_clock_out_all_sessions,
    calculate_idle_minutes_simple, calculate_sleep_minutes_for_session
)
from utils.activity_monitor import start_activity_monitor
from utils.session_timeout import start_timeout_monitor
from utils.mac_address import get_mac_address
from utils.idle_monitor import start_idle_monitoring, stop_idle_monitoring, get_idle_status, get_idle_duration
import threading

class EmployeeDashboard(QWidget):
    def __init__(self, account_id):
        super().__init__()
        self.setWindowTitle("Employee Dashboard - Time Tracking")
        self.setFixedSize(600, 500)
        self.account_id = account_id
        self.session_id = None
        self.clock_in_time = None
        self.feedback_given = False
        self.feedback_shown = False

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #dc3545;
                color: white;
                height: 45px;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            .stats-label {
                font-size: 14px;
                color: #34495e;
                font-weight: normal;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
                margin: 2px;
            }
        """)

        self.check_and_handle_existing_session()

        self.create_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.idle_status_timer = QTimer()
        self.idle_status_timer.timeout.connect(self.update_idle_status)
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_session_stats)

    def create_ui(self):
        """Create the enhanced user interface"""
        self.header = QLabel("👷 Employee Time Tracker")
        self.status_label = QLabel("Status: Auto-Tracking Active")
        self.timer_label = QLabel("")
        
        current_mac = get_mac_address()
        self.mac_label = QLabel(f"🖥️ Device MAC: {current_mac}")
        self.mac_label.setStyleSheet("font-size: 12px; color: #666; font-weight: normal;")

        self.info_label = QLabel("ℹ️ Time tracking is automatic based on login/logout")
        self.info_label.setStyleSheet("font-size: 13px; color: #666; font-weight: normal;")
        
        self.idle_status_label = QLabel("💻 Activity Status: Active")
        self.idle_status_label.setStyleSheet("font-size: 14px; color: #2c3e50; font-weight: normal;")
        
        self.work_time_label = QLabel("💼 Work Time: Calculating...")
        self.work_time_label.setStyleSheet("font-size: 13px; color: #27ae60; font-weight: normal;")
        
        self.sleep_time_label = QLabel("😴 Sleep Time: Calculating...")
        self.sleep_time_label.setStyleSheet("font-size: 13px; color: #f39c12; font-weight: normal;")
        
        self.idle_time_label = QLabel("💤 Idle Time: Calculating...")
        self.idle_time_label.setStyleSheet("font-size: 13px; color: #e74c3c; font-weight: normal;")
        
        self.system_idle_label = QLabel("⏱️ System Idle: 0s")
        self.system_idle_label.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: normal;")

        self.logout_button = QPushButton("🚪 Logout")
        self.logout_button.clicked.connect(self.handle_logout)
        
        button_font = QFont("Arial", 14, QFont.Bold)
        self.logout_button.setFont(button_font)
        
        self.logout_button.setMinimumHeight(50)
        self.logout_button.setMaximumHeight(60)
        self.logout_button.setMinimumWidth(150)
        
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                padding: 12px 20px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #bd2130;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)
        
        layout.addWidget(self.header)
        layout.addWidget(self.status_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.mac_label)
    
        separator1 = QLabel("─" * 60)
        separator1.setStyleSheet("color: #bdc3c7; font-weight: normal;")
        layout.addWidget(separator1)
        
        layout.addWidget(self.idle_status_label)
        layout.addWidget(self.system_idle_label)
        
        separator2 = QLabel("─" * 60)
        separator2.setStyleSheet("color: #bdc3c7; font-weight: normal;")
        layout.addWidget(separator2)
        
        stats_header = QLabel("📊 Session Statistics")
        stats_header.setStyleSheet("font-size: 15px; color: #2c3e50; font-weight: bold;")
        layout.addWidget(stats_header)
        
        layout.addWidget(self.work_time_label)
        layout.addWidget(self.sleep_time_label)
        layout.addWidget(self.idle_time_label)
        
        separator3 = QLabel("─" * 60)
        separator3.setStyleSheet("color: #bdc3c7; font-weight: normal;")
        layout.addWidget(separator3)
        
        layout.addWidget(self.info_label)
        
        layout.addSpacing(10)
        layout.addWidget(self.logout_button)
        
        layout.addSpacing(10)

        self.setLayout(layout)

    def check_and_handle_existing_session(self):
        """Check for existing active session and handle auto clock-in"""
        try:
            session_id, clock_in_time = get_active_session(self.account_id)
            if session_id:
                self.session_id = session_id
                self.clock_in_time = clock_in_time
            else:
                self.auto_clock_in()
        except Exception:
            self.auto_clock_in()

    def auto_clock_in(self):
        """Automatically clock in when user logs in"""
        try:
            self.clock_in_time = datetime.now()
            self.session_id = start_session(self.account_id, self.clock_in_time)
        except Exception:
            pass

    def showEvent(self, event):
        """Update UI when window is shown"""
        super().showEvent(event)
        if self.session_id and self.clock_in_time:
            self.status_label.setText(f"Auto-tracking since {self.clock_in_time.strftime('%H:%M:%S')}")
            self.timer.start(1000)
            self.idle_status_timer.start(3000)  # Update idle status every 3 seconds
            self.stats_timer.start(10000)  # Update stats every 10 seconds
            
            try:
                start_timeout_monitor(self.account_id, self.session_id, self.clock_in_time)
                threading.Thread(
                    target=start_activity_monitor,
                    args=(self.account_id, self.session_id),
                    daemon=True
                ).start()
                
                # Start idle monitoring with 5-minute threshold
                start_idle_monitoring(self.account_id, self.session_id, 300)  # 5 minutes
                
                self.update_session_stats()
                    
            except Exception:
                pass

    def update_timer(self):
        """Update the elapsed time timer"""
        if self.clock_in_time:
            elapsed = datetime.now() - self.clock_in_time
            total_seconds = int(elapsed.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            self.timer_label.setText(f"⏱ Session Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def update_idle_status(self):
        """Update the idle status display with enhanced information"""
        if self.session_id:
            try:
                idle_status = get_idle_status(self.account_id, self.session_id)
                
                system_idle = get_idle_duration()
                
                if system_idle < 60:
                    self.system_idle_label.setText(f"⏱️ System Idle: {int(system_idle)}s")
                else:
                    minutes = int(system_idle // 60)
                    seconds = int(system_idle % 60)
                    self.system_idle_label.setText(f"⏱️ System Idle: {minutes}m {seconds}s")
                
                # Update activity status
                if idle_status and idle_status.get('is_idle'):
                    idle_duration = idle_status.get('current_idle_duration', 0)
                    if idle_duration >= 60:
                        minutes = idle_duration // 60
                        seconds = idle_duration % 60
                        self.idle_status_label.setText(f"😴 Idle for {minutes}m {seconds}s")
                    else:
                        self.idle_status_label.setText(f"😴 Idle for {idle_duration}s")
                    self.idle_status_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
                else:
                    self.idle_status_label.setText("💻 Activity Status: Active")
                    self.idle_status_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: normal;")
                    
            except Exception:
                pass

    def update_session_stats(self):
        """Update session statistics display"""
        if self.session_id:
            try:
                # Calculate current session statistics
                sleep_minutes = calculate_sleep_minutes_for_session(self.session_id)
                idle_minutes = calculate_idle_minutes_simple(self.session_id)
                
                # Calculate work time (total - sleep - idle)
                work_minutes = 0
                if self.clock_in_time:
                    total_minutes = int((datetime.now() - self.clock_in_time).total_seconds() / 60)
                    work_minutes = max(0, total_minutes - sleep_minutes - idle_minutes)
                
                def format_minutes(minutes):
                    if minutes < 60:
                        return f"{minutes}m"
                    else:
                        hours = minutes // 60
                        mins = minutes % 60
                        return f"{hours}h {mins}m"
                
                self.work_time_label.setText(f"💼 Work Time: {format_minutes(work_minutes)}")
                self.sleep_time_label.setText(f"😴 Sleep Time: {format_minutes(sleep_minutes)}")
                self.idle_time_label.setText(f"💤 Idle Time: {format_minutes(idle_minutes)}")
                
                # Color coding based on values
                if work_minutes < 30:  # Less than 30 minutes work
                    self.work_time_label.setStyleSheet("font-size: 13px; color: #e74c3c; font-weight: normal;")
                else:
                    self.work_time_label.setStyleSheet("font-size: 13px; color: #27ae60; font-weight: normal;")
                
                if sleep_minutes > 30:  # More than 30 minutes sleep
                    self.sleep_time_label.setStyleSheet("font-size: 13px; color: #e74c3c; font-weight: normal;")
                else:
                    self.sleep_time_label.setStyleSheet("font-size: 13px; color: #f39c12; font-weight: normal;")
                
                if idle_minutes > 60:  # More than 1 hour idle
                    self.idle_time_label.setStyleSheet("font-size: 13px; color: #e74c3c; font-weight: bold;")
                elif idle_minutes > 30:  # More than 30 minutes idle
                    self.idle_time_label.setStyleSheet("font-size: 13px; color: #f39c12; font-weight: normal;")
                else:
                    self.idle_time_label.setStyleSheet("font-size: 13px; color: #27ae60; font-weight: normal;")
                
            except Exception:
                self.work_time_label.setText("💼 Work Time: Error")
                self.sleep_time_label.setText("😴 Sleep Time: Error")
                self.idle_time_label.setText("💤 Idle Time: Error")

    def show_feedback_dialog(self):
        """Show feedback dialog"""
        if not self.feedback_shown:
            self.feedback_shown = True
            try:
                from gui.feedback_dialog import FeedbackDialog
                
                def submit_callback(account_id, mood, comment, anonymous):
                    insert_feedback(account_id, mood, comment, anonymous)
                    self.feedback_given = True
                
                feedback_dialog = FeedbackDialog(self.account_id, submit_callback)
                feedback_dialog.exec_()
            except Exception:
                pass

    def closeEvent(self, event):
        """Handle window close with automatic clock out"""
        try:
            if not self.feedback_shown:
                self.show_feedback_dialog()

            self.timer.stop()
            self.idle_status_timer.stop()
            self.stats_timer.stop()

            if self.session_id:
                stop_idle_monitoring(self.account_id, self.session_id)

            if self.session_id:
                end_session(self.session_id, datetime.now())
            else:
                auto_clock_out_all_sessions(self.account_id)

            event.accept()
        except Exception:
            event.accept()

    def handle_logout(self):
        """Handle logout with automatic clock out"""
        try:
            if not self.feedback_shown:
                self.show_feedback_dialog()

            self.timer.stop()
            self.idle_status_timer.stop()
            self.stats_timer.stop()

            if self.session_id:
                stop_idle_monitoring(self.account_id, self.session_id)

            if self.session_id:
                end_session(self.session_id, datetime.now())
            else:
                auto_clock_out_all_sessions(self.account_id)

            from gui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Logout failed: {str(e)}")
            self.close()