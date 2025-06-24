# gui/admin_dashboard.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox,
    QGroupBox, QDateEdit, QLineEdit, QComboBox, QDialog,
    QTextEdit, QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtCore import QTimer, QDate, Qt
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, date, timedelta
import threading
from gui.manage_users import ManageUsers
from database.queries import (
    fetch_all_sessions_with_idle, fetch_sessions_by_date_range_with_idle, 
    fetch_filtered_feedback, insert_feedback, fetch_all_users, start_session, 
    end_session, get_active_session, auto_clock_out_all_sessions,
    get_active_sessions_with_status
)

from utils.activity_monitor import start_activity_monitor
from utils.session_timeout import start_timeout_monitor
from utils.mac_address import get_mac_address
from utils.idle_monitor import start_idle_monitoring, stop_idle_monitoring, get_idle_status

class CommentViewDialog(QDialog):
    """Dialog to view full comment text"""
    def __init__(self, comment, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full Comment")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        label = QLabel("Full Comment:")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(comment or "No comment provided")
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

class AdminDashboard(QWidget):
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id
        self.current_session_id = None
        self.clock_in_time = None
        self.manage_window = None
        self.feedback_given = False
        self.feedback_shown = False

        self.setWindowTitle("Admin Dashboard - Live Employee Monitoring")
        self.resize(1600, 1000)
        self.setStyleSheet("""
            QWidget { 
                background-color: #f0f4f8; 
                font-family: Arial; 
                font-size: 14px; 
            }
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50; 
            }
            QPushButton {
                background-color: #007bff; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 5px; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #0056b3; 
            }
            QPushButton:disabled { 
                background-color: #cccccc; 
                color: #555555; 
            }
            QTableWidget { 
                background-color: #ffffff; 
                font-size: 13px; 
            }
            QGroupBox { 
                background-color: #e9eff5; 
                border-radius: 6px; 
                padding: 8px; 
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox, QLineEdit, QDateEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
            }
        """)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_live_status)

        self.check_and_handle_existing_session()

        self.create_header_elements()
        self.create_live_status_section()
        self.create_control_buttons()
        self.create_session_filter_box()
        self.create_feedback_filter_box()
        self.create_tables()
        self.create_layout()

        self.update_ui_for_active_session()
        
        self.load_sessions()
        self.load_feedback()
        
        self.status_update_timer.start(10000)

    def create_header_elements(self):
        """Create header labels and status display"""
        self.header = QLabel("📊 Admin Dashboard - Real-Time Employee Monitoring")
        self.status_label = QLabel("Status: Auto-Tracking Active")
        self.timer_label = QLabel("")
        
        current_mac = get_mac_address()
        self.mac_label = QLabel(f"🖥️ Admin Device MAC: {current_mac}")
        self.mac_label.setStyleSheet("font-size: 12px; color: #666; font-weight: normal;")

    def create_live_status_section(self):
        """Create live status monitoring section"""
        self.live_status_box = QGroupBox("🔴 LIVE STATUS - Active Employee Sessions")
        live_status_layout = QVBoxLayout()
        
        self.live_summary_label = QLabel("Loading live status...")
        self.live_summary_label.setStyleSheet("font-size: 16px; color: #2c3e50; font-weight: bold;")
        live_status_layout.addWidget(self.live_summary_label)
        
        self.live_status_table = QTableWidget()
        self.live_status_table.setColumnCount(8)
        self.live_status_table.setHorizontalHeaderLabels([
            "Employee", "MAC Address", "Clock In", "Total Time", 
            "Work Time", "Sleep Time", "Idle Time", "Current Status"
        ])
        self.live_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.live_status_table.setMaximumHeight(200)
        
        live_status_layout.addWidget(self.live_status_table)
        self.live_status_box.setLayout(live_status_layout)

    def create_control_buttons(self):
        """Create main control buttons"""
        self.refresh_button = QPushButton("🔄 Refresh All")
        self.manage_users_button = QPushButton("👥 Manage Users")
        self.logout_button = QPushButton("🚪 Logout")

        self.refresh_button.clicked.connect(self.refresh_all)
        self.manage_users_button.clicked.connect(self.open_manage_users)
        self.logout_button.clicked.connect(self.handle_logout)

    def create_session_filter_box(self):
        """Create session filtering controls"""
        self.session_filter_box = QGroupBox("🗓️ Filter Sessions")
        session_filter_layout = QHBoxLayout()

        session_filter_layout.addWidget(QLabel("Employee:"))
        self.employee_search = QLineEdit()
        self.employee_search.setPlaceholderText("Search employee name...")
        session_filter_layout.addWidget(self.employee_search)

        session_filter_layout.addWidget(QLabel("MAC:"))
        self.mac_search = QLineEdit()
        self.mac_search.setPlaceholderText("Search MAC address...")
        session_filter_layout.addWidget(self.mac_search)

        self.day_combo = QComboBox()
        self.day_combo.addItem("Day")
        for day in range(1, 32):
            self.day_combo.addItem(str(day))

        self.month_combo = QComboBox()
        months = ["Month", "January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        self.month_combo.addItems(months)

        self.year_combo = QComboBox()
        current_year = datetime.now().year
        self.year_combo.addItem("Year")
        for year in range(current_year - 5, current_year + 2):
            self.year_combo.addItem(str(year))

        self.apply_session_filter_btn = QPushButton("Apply Filter")
        self.apply_session_filter_btn.clicked.connect(self.filter_sessions_by_dropdowns)

        self.clear_session_filter_btn = QPushButton("Clear Filter")
        self.clear_session_filter_btn.clicked.connect(self.clear_session_filters)

        session_filter_layout.addWidget(QLabel("Day:"))
        session_filter_layout.addWidget(self.day_combo)
        session_filter_layout.addWidget(QLabel("Month:"))
        session_filter_layout.addWidget(self.month_combo)
        session_filter_layout.addWidget(QLabel("Year:"))
        session_filter_layout.addWidget(self.year_combo)
        session_filter_layout.addWidget(self.apply_session_filter_btn)
        session_filter_layout.addWidget(self.clear_session_filter_btn)
        session_filter_layout.addStretch()

        self.session_filter_box.setLayout(session_filter_layout)
        self.session_filter_box.setMaximumHeight(70)

    def create_feedback_filter_box(self):
        """Create feedback filtering controls"""
        self.feedback_filter_box = QGroupBox("🗣️ Filter Feedback")
        feedback_filter_layout = QHBoxLayout()

        feedback_filter_layout.addWidget(QLabel("From:"))
        self.feedback_from_date = QDateEdit(calendarPopup=True)
        self.feedback_from_date.setDate(QDate.currentDate().addMonths(-1))
        feedback_filter_layout.addWidget(self.feedback_from_date)

        feedback_filter_layout.addWidget(QLabel("To:"))
        self.feedback_to_date = QDateEdit(calendarPopup=True)
        self.feedback_to_date.setDate(QDate.currentDate())
        feedback_filter_layout.addWidget(self.feedback_to_date)

        feedback_filter_layout.addWidget(QLabel("Mood:"))
        self.mood_filter = QComboBox()
        self.mood_filter.addItems(["All", "Terrible", "Poor", "Good", "Great", "Excellent"])
        feedback_filter_layout.addWidget(self.mood_filter)

        feedback_filter_layout.addWidget(QLabel("Keyword:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Search...")
        feedback_filter_layout.addWidget(self.keyword_input)

        self.filter_feedback_button = QPushButton("Apply Filter")
        self.filter_feedback_button.clicked.connect(self.load_feedback_filtered)
        feedback_filter_layout.addWidget(self.filter_feedback_button)

        self.clear_feedback_filter_btn = QPushButton("Clear Filter")
        self.clear_feedback_filter_btn.clicked.connect(self.clear_feedback_filters)
        feedback_filter_layout.addWidget(self.clear_feedback_filter_btn)

        self.feedback_filter_box.setLayout(feedback_filter_layout)
        self.feedback_filter_box.setMaximumHeight(70)

    def create_tables(self):
        """Create data tables with proper sleep and idle columns"""
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "MAC Address", "Employee Name", "Clock In", "Clock Out", 
            "Date", "Work Time (min)", "Sleep Time (min)", "Idle Time (min)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(5)
        self.feedback_table.setHorizontalHeaderLabels([
            "Employee Name", "Mood", "Comment", "Anonymous", "Submitted At"
        ])
        self.feedback_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.feedback_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.feedback_table.cellDoubleClicked.connect(self.show_full_comment)

    def create_layout(self):
        """Create and set the main layout"""
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.manage_users_button)
        top_layout.addWidget(self.logout_button)
        top_layout.addStretch()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.header)
        layout.addWidget(self.status_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.mac_label)
        layout.addLayout(top_layout)

        layout.addWidget(self.live_status_box)

        layout.addWidget(self.session_filter_box)
        layout.addWidget(QLabel("📅 All Sessions: Complete time tracking with Sleep and Idle monitoring"))
        layout.addWidget(self.table)

        layout.addWidget(self.feedback_filter_box)
        layout.addWidget(QLabel("🗣️ User Feedback: (Double-click row to view full comment)"))
        layout.addWidget(self.feedback_table)

        self.setLayout(layout)

    def check_and_handle_existing_session(self):
        """Check for existing active session and handle auto clock-in"""
        try:
            session_id, clock_in_time = get_active_session(self.account_id)
            if session_id:
                self.current_session_id = session_id
                self.clock_in_time = clock_in_time
            else:
                self.auto_clock_in()
        except Exception:
            self.auto_clock_in()

    def auto_clock_in(self):
        """Automatically clock in when user logs in"""
        try:
            self.clock_in_time = datetime.now()
            self.current_session_id = start_session(self.account_id, self.clock_in_time)
        except Exception:
            pass

    def update_ui_for_active_session(self):
        """Update UI elements when session is active"""
        if self.current_session_id and self.clock_in_time:
            self.status_label.setText(f"Admin auto-tracking since {self.clock_in_time.strftime('%H:%M:%S')}")
            self.timer.start(1000)
            
            try:
                start_timeout_monitor(self.account_id, self.current_session_id, self.clock_in_time)
                threading.Thread(
                    target=start_activity_monitor,
                    args=(self.account_id, self.current_session_id),
                    daemon=True
                ).start()
                
                start_idle_monitoring(self.account_id, self.current_session_id, 60)
                    
            except Exception:
                pass

    def update_live_status(self):
        """Update live status of all active sessions"""
        try:
            active_sessions = get_active_sessions_with_status()
            
            total_active = len(active_sessions)
            idle_count = sum(1 for session in active_sessions if session['is_idle'])
            active_count = total_active - idle_count
            
            summary_text = f"📊 Active Sessions: {total_active} | Working: {active_count} | Idle: {idle_count}"
            if idle_count > 0:
                idle_users = [session['username'] for session in active_sessions if session['is_idle']]
                summary_text += f" | Idle Users: {', '.join(idle_users[:3])}{'...' if len(idle_users) > 3 else ''}"
            
            self.live_summary_label.setText(summary_text)
            
            self.populate_live_status_table(active_sessions)
            
            self.load_sessions()
            
        except Exception:
            self.live_summary_label.setText("❌ Error loading live status")

    def populate_live_status_table(self, active_sessions):
        """Populate the live status table with real-time data"""
        try:
            self.live_status_table.setRowCount(len(active_sessions))
            
            for row_idx, session in enumerate(active_sessions):
                name_item = QTableWidgetItem(session['username'])
                if session['is_idle']:
                    name_item.setBackground(QColor(255, 200, 200))
                    name_item.setFont(QFont("Arial", 10, QFont.Bold))
                else:
                    name_item.setBackground(QColor(200, 255, 200))
                
                self.live_status_table.setItem(row_idx, 0, name_item)
                
                self.live_status_table.setItem(row_idx, 1, QTableWidgetItem(session['mac_address']))
                
                clock_in_str = session['clock_in'].strftime('%H:%M:%S') if session['clock_in'] else 'Unknown'
                self.live_status_table.setItem(row_idx, 2, QTableWidgetItem(clock_in_str))
                
                total_hours = session['total_minutes'] // 60
                total_mins = session['total_minutes'] % 60
                self.live_status_table.setItem(row_idx, 3, QTableWidgetItem(f"{total_hours}h {total_mins}m"))
                
                work_hours = session['work_minutes'] // 60
                work_mins = session['work_minutes'] % 60
                self.live_status_table.setItem(row_idx, 4, QTableWidgetItem(f"{work_hours}h {work_mins}m"))
                
                sleep_item = QTableWidgetItem(f"{session['sleep_minutes']}m")
                if session['sleep_minutes'] > 30:
                    sleep_item.setBackground(QColor(255, 255, 200))
                self.live_status_table.setItem(row_idx, 5, sleep_item)
                
                idle_item = QTableWidgetItem(f"{session['idle_minutes']}m")
                if session['idle_minutes'] > 60:
                    idle_item.setBackground(QColor(255, 200, 200))
                elif session['idle_minutes'] > 30:
                    idle_item.setBackground(QColor(255, 255, 200))
                self.live_status_table.setItem(row_idx, 6, idle_item)
                
                if session['is_idle']:
                    idle_duration = session['current_idle_duration']
                    status_text = f"💤 Idle ({idle_duration}m)"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setBackground(QColor(255, 200, 200))
                    status_item.setFont(QFont("Arial", 10, QFont.Bold))
                else:
                    status_item = QTableWidgetItem("💻 Active")
                    status_item.setBackground(QColor(200, 255, 200))
                
                self.live_status_table.setItem(row_idx, 7, status_item)
                
        except Exception:
            pass

    def filter_sessions_by_dropdowns(self):
        """Filter sessions based on dropdown selections and text inputs"""
        day = self.day_combo.currentText()
        month = self.month_combo.currentText()
        year = self.year_combo.currentText()
        employee_search = self.employee_search.text().strip().lower()
        mac_search = self.mac_search.text().strip().lower()
        
        start_date = None
        end_date = None

        try:
            if year != "Year":
                year_int = int(year)
                
                if month != "Month":
                    month_int = self.month_combo.currentIndex()
                    
                    if day != "Day":
                        day_int = int(day)
                        start_date = date(year_int, month_int, day_int)
                        end_date = start_date
                    else:
                        start_date = date(year_int, month_int, 1)
                        
                        if month_int == 12:
                            end_date = date(year_int + 1, 1, 1) - timedelta(days=1)
                        else:
                            end_date = date(year_int, month_int + 1, 1) - timedelta(days=1)
                else:
                    start_date = date(year_int, 1, 1)
                    end_date = date(year_int, 12, 31)

            if start_date and end_date:
                sessions = fetch_sessions_by_date_range_with_idle(start_date, end_date)
            else:
                sessions = fetch_all_sessions_with_idle()
            
            if employee_search or mac_search:
                filtered_sessions = []
                for session in sessions:
                    mac_address, username = session[0], session[1]
                    
                    employee_match = not employee_search or employee_search in username.lower()
                    mac_match = not mac_search or mac_search in mac_address.lower()
                    
                    if employee_match and mac_match:
                        filtered_sessions.append(session)
                sessions = filtered_sessions
                
            self.populate_sessions_table(sessions)
        
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid Date", "Please select a valid date combination.")
            self.load_sessions()

    def clear_session_filters(self):
        """Clear all session filters"""
        self.employee_search.clear()
        self.mac_search.clear()
        self.day_combo.setCurrentIndex(0)
        self.month_combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)
        self.load_sessions()

    def clear_feedback_filters(self):
        """Clear all feedback filters"""
        self.feedback_from_date.setDate(QDate.currentDate().addMonths(-1))
        self.feedback_to_date.setDate(QDate.currentDate())
        self.mood_filter.setCurrentIndex(0)
        self.keyword_input.clear()
        self.load_feedback()

    def show_full_comment(self, row, column):
        """Show full comment in dialog when user double-clicks"""
        if column == 2:
            comment_item = self.feedback_table.item(row, 2)
            if comment_item:
                comment = comment_item.text()
                dialog = CommentViewDialog(comment, self)
                dialog.exec_()

    def update_timer(self):
        """Update the elapsed time timer"""
        if self.clock_in_time:
            elapsed = datetime.now() - self.clock_in_time
            minutes, seconds = divmod(elapsed.seconds, 60)
            hours, minutes = divmod(minutes, 60)
            self.timer_label.setText(f"⏱ Admin Session Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def load_sessions(self):
        """Load all sessions from database with complete idle and sleep information"""
        try:
            sessions = fetch_all_sessions_with_idle()
            self.populate_sessions_table(sessions)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sessions: {str(e)}")

    def populate_sessions_table(self, sessions):
        """Populate table with sessions data including complete sleep and idle time"""
        try:
            self.table.setRowCount(len(sessions))
            for row_idx, session in enumerate(sessions):
                if len(session) >= 9:
                    mac_address, username, clock_in, clock_out, session_date, work_minutes, sleep_minutes, idle_minutes, session_id = session[:9]
                    account_id = session[9] if len(session) > 9 else None
                else:
                    mac_address, username, clock_in, clock_out, session_date, work_minutes, sleep_minutes = session
                    idle_minutes = 0
                    session_id = None
                    account_id = None
                
                work_minutes = work_minutes if work_minutes is not None else 0
                sleep_minutes = sleep_minutes if sleep_minutes is not None else 0
                idle_minutes = idle_minutes if idle_minutes is not None else 0
                
                work_item = QTableWidgetItem(str(work_minutes))
                
                sleep_item = QTableWidgetItem(str(sleep_minutes))
                if sleep_minutes > 30:
                    sleep_item.setBackground(QColor(255, 255, 200))
                
                idle_item = QTableWidgetItem(str(idle_minutes))
                if idle_minutes > 60:
                    idle_item.setBackground(QColor(255, 200, 200))
                elif idle_minutes > 30:
                    idle_item.setBackground(QColor(255, 255, 200))
                
                # Set all table items
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(mac_address)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(username)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(clock_in)))
                
                # Show current status for active sessions
                clock_out_text = str(clock_out if clock_out else "🔴 Active")
                if not clock_out and session_id and account_id:
                    # Check if currently idle
                    idle_status = get_idle_status(account_id, session_id)
                    if idle_status and idle_status.get('is_idle'):
                        clock_out_text = "🔴 Active (💤 Idle)"
                
                self.table.setItem(row_idx, 3, QTableWidgetItem(clock_out_text))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(session_date)))
                self.table.setItem(row_idx, 5, work_item)
                self.table.setItem(row_idx, 6, sleep_item)
                self.table.setItem(row_idx, 7, idle_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate sessions table: {str(e)}")

    def load_feedback(self):
        """Load all feedback from database"""
        try:
            feedbacks = fetch_filtered_feedback()
            self.populate_feedback_table(feedbacks)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load feedback: {str(e)}")

    def load_feedback_filtered(self):
        """Load filtered feedback based on user selections"""
        try:
            start_date = self.feedback_from_date.date().toPyDate()
            end_date = self.feedback_to_date.date().toPyDate()
            mood = self.mood_filter.currentText()
            keyword = self.keyword_input.text()
            
            feedbacks = fetch_filtered_feedback(start_date, end_date, mood, keyword)
            self.populate_feedback_table(feedbacks)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter feedback: {str(e)}")

    def populate_feedback_table(self, feedbacks):
        """Populate feedback table with data"""
        try:
            self.feedback_table.setRowCount(len(feedbacks))
            for row_idx, feedback in enumerate(feedbacks):
                feedback_id, username, mood, comment, anonymous, submitted_at = feedback
                display_name = username if username else "Anonymous"
                self.feedback_table.setItem(row_idx, 0, QTableWidgetItem(display_name))
                self.feedback_table.setItem(row_idx, 1, QTableWidgetItem(mood))
                
                truncated_comment = ""
                if comment:
                    truncated_comment = comment[:50] + "..." if len(comment) > 50 else comment
                
                self.feedback_table.setItem(row_idx, 2, QTableWidgetItem(truncated_comment))
                self.feedback_table.setItem(row_idx, 3, QTableWidgetItem(anonymous))
                self.feedback_table.setItem(row_idx, 4, QTableWidgetItem(submitted_at.strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate feedback table: {str(e)}")

    def refresh_all(self):
        """Refresh all data and live status"""
        self.update_live_status()
        self.load_feedback()

    def open_manage_users(self):
        """Open manage users window"""
        try:
            if self.manage_window is None or not self.manage_window.isVisible():
                self.manage_window = ManageUsers()
                self.manage_window.show()
            else:
                self.manage_window.raise_()
                self.manage_window.activateWindow()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open manage users: {str(e)}")

    def handle_logout(self):
        """Handle logout with automatic clock out"""
        try:
            if not self.feedback_shown:
                self.show_feedback_dialog()
            
            if self.current_session_id:
                stop_idle_monitoring(self.account_id, self.current_session_id)
            
            if self.current_session_id:
                end_session(self.current_session_id, datetime.now())
            else:
                auto_clock_out_all_sessions(self.account_id)
                
            from gui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            
            self.hide()
            
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.close)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Logout failed: {str(e)}")

    def closeEvent(self, event):
        """Handle window close with automatic logout"""
        try:
            self.handle_logout_logic()
            event.accept()
        except Exception:
            event.accept()
    
    def handle_logout_logic(self):
        """Common logout logic for both logout button and close button"""
        try:
            if not self.feedback_shown:
                self.show_feedback_dialog()
            
            if self.manage_window and self.manage_window.isVisible():
                self.manage_window.close()

            if self.current_session_id:
                stop_idle_monitoring(self.account_id, self.current_session_id)

            if self.current_session_id:
                end_session(self.current_session_id, datetime.now())
            else:
                auto_clock_out_all_sessions(self.account_id)

        except Exception:
            pass
    
    def show_feedback_dialog(self):
        """Show feedback dialog on logout/close"""
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