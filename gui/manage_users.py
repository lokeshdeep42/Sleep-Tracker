# gui/manage_users.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QComboBox, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from database.queries import fetch_all_users, create_user, toggle_user_status, delete_user

class ManageUsers(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Management")
        self.resize(1100, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        header = QLabel("👥 Manage Users")
        header.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 12px;")
        self.layout.addWidget(header, alignment=Qt.AlignLeft)

        form_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(150)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(150)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["employee", "admin"])
        self.role_combo.setFixedWidth(120)

        self.add_user_btn = QPushButton("➕ Create User")
        self.add_user_btn.clicked.connect(self.create_user)
        self.add_user_btn.setStyleSheet(self.button_style("#0078D7"))

        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.role_combo)
        form_layout.addWidget(self.add_user_btn)
        form_layout.setSpacing(15)

        self.layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "MAC Address", "Status", "Toggle", "Delete"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 110)
        
        self.table.setStyleSheet("""
            QTableWidget { 
                font-size: 14px; 
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.layout.addWidget(self.table)

        self.load_users()

    def button_style(self, color="#0078D7"):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
                min-width: 60px;
                max-width: 100px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            QPushButton:pressed {{
                background-color: {color};
                opacity: 0.6;
            }}
        """

    def load_users(self):
        users = fetch_all_users()
        self.table.setRowCount(len(users))

        for row, user_data in enumerate(users):            
            if len(user_data) == 4:
                user_id, username, role, status = user_data
                mac_address = "N/A"
            elif len(user_data) == 5:
                user_id, username, role, status, mac_address = user_data
            elif len(user_data) == 6:
                user_id, username, role, mac_address, status, _ = user_data
            else:
                print(f"Warning: Unexpected user data length: {len(user_data)} for row {row}")
                print(f"Data: {user_data}")
                user_id = user_data[0] if len(user_data) > 0 else "Unknown"
                username = user_data[1] if len(user_data) > 1 else "Unknown"
                role = user_data[2] if len(user_data) > 2 else "employee"
                status = user_data[3] if len(user_data) > 3 else "Active"
                mac_address = user_data[4] if len(user_data) > 4 else "N/A"

            self.table.setItem(row, 0, QTableWidgetItem(str(user_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(username)))
            self.table.setItem(row, 2, QTableWidgetItem(str(role)))
            self.table.setItem(row, 3, QTableWidgetItem(str(mac_address)))

            status_item = QTableWidgetItem(str(status))
            status_color = QColor("green") if status == "Active" else QColor("red")
            status_item.setForeground(status_color)
            self.table.setItem(row, 4, status_item)

            toggle_btn = QPushButton("Disable" if status == "Active" else "Enable")
            toggle_btn.setStyleSheet(self.button_style("#F7630C" if status == "Active" else "#107C10"))
            toggle_btn.setMaximumSize(100, 26)
            toggle_btn.clicked.connect(
                lambda checked, uid=user_id, stat=status: self.toggle_user(uid, stat)
            )
            
            toggle_container = QWidget()
            toggle_layout = QHBoxLayout(toggle_container)
            toggle_layout.addWidget(toggle_btn)
            toggle_layout.setContentsMargins(5, 2, 5, 2)
            toggle_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 5, toggle_container)

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(self.button_style("#D13438"))
            delete_btn.setMaximumSize(100, 26)
            delete_btn.clicked.connect(
                lambda checked, uid=user_id, uname=username: self.delete_user(uid, uname)
            )
            
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.addWidget(delete_btn)
            delete_layout.setContentsMargins(5, 2, 5, 2)
            delete_layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 6, delete_container)

            self.table.setRowHeight(row, 40)

    def create_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required.")
            return

        try:
            create_user(username, password, role)
            QMessageBox.information(self, "Success", "User created successfully.")
            self.username_input.clear()
            self.password_input.clear()
            self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create user: {e}")

    def toggle_user(self, user_id, current_status):
        new_status = "Disabled" if current_status == "Active" else "Active"
        try:
            toggle_user_status(user_id, 'inactive' if new_status == "Disabled" else 'active')
            self.load_users()
            QMessageBox.information(self, "Success", f"User status updated to {new_status}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update user status: {e}")

    def delete_user(self, user_id, username):
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete user '{username}'?\n\n"
            "⚠️ This action cannot be undone and will remove:\n"
            "• The user account\n"
            "• All associated sessions\n"
            "• All related data\n\n"
            "Continue with deletion?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                delete_user(user_id)
                QMessageBox.information(self, "Success", f"User '{username}' deleted successfully.")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")