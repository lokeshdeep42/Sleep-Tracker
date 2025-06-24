# gui/login_window.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from database.queries import authenticate_user, auto_clock_out_all_sessions
from gui.admin_dashboard import AdminDashboard
from gui.employee_dashboard import EmployeeDashboard
from utils.mac_address import get_mac_address

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(450, 380)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel#header {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #2c3e50;
            }
            QLabel#mac_info {
                font-size: 12px;
                color: #666;
                font-weight: normal;
                margin-bottom: 10px;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                height: 38px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 15px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #555555;
            }
            QCheckBox {
                color: #2c3e50;
                font-size: 13px;
            }
        """)

        self.header = QLabel("🔐 Employee Login")
        self.header.setObjectName("header")
        self.header.setAlignment(Qt.AlignCenter)

        current_mac = get_mac_address()
        self.mac_info = QLabel(f"🖥️ Device MAC: {current_mac}")
        self.mac_info.setObjectName("mac_info")
        self.mac_info.setAlignment(Qt.AlignCenter)
        self.mac_info.setWordWrap(True)

        self.auto_info = QLabel("ℹ️ Auto clock-in/out enabled")
        self.auto_info.setObjectName("mac_info")
        self.auto_info.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.returnPressed.connect(self.handle_login)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.handle_login)

        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)

        self.login_button = QPushButton("🔓 Login")
        self.login_button.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)
        layout.addWidget(self.header)
        layout.addWidget(self.mac_info)
        layout.addWidget(self.auto_info)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_password_checkbox)
        layout.addSpacing(5)
        layout.addWidget(self.login_button)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

    def toggle_password_visibility(self, state):
        self.password_input.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return

        current_mac = get_mac_address()
        print(f"Login attempt from MAC: {current_mac}")

        account_id, role = authenticate_user(username, password)

        if account_id is None:
            QMessageBox.warning(self, "Login Failed", "User is not enabled or invalid credentials.")
        elif role == 'admin':
            try:
                self.admin = AdminDashboard(account_id)
                self.admin.show()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open admin dashboard: {str(e)}")
        elif role == 'employee':
            try:
                self.emp = EmployeeDashboard(account_id)
                self.emp.show()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open employee dashboard: {str(e)}")
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def closeEvent(self, event):
        """Handle application close"""
        event.accept()