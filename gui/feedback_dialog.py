#gui/feeback_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QCheckBox, QButtonGroup, QRadioButton, QMessageBox
)
from PyQt5.QtCore import Qt

class FeedbackDialog(QDialog):
    def __init__(self, account_id, submit_callback):
        super().__init__()
        self.account_id = account_id
        self.submit_callback = submit_callback
        self.setWindowTitle("Feedback")
        self.setFixedSize(400, 350)

        self.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)

        self.label = QLabel("How is your mood today?")

        self.button_group = QButtonGroup()
        moods = ["Terrible", "Poor", "Good", "Great", "Excellent"]
        mood_layout = QHBoxLayout()
        for mood in moods:
            btn = QRadioButton(mood)
            self.button_group.addButton(btn)
            mood_layout.addWidget(btn)

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Comments...")

        self.anonymous_checkbox = QCheckBox("Share anonymously")

        self.submit_button = QPushButton("Submit Feedback")
        self.submit_button.clicked.connect(self.submit_feedback)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(mood_layout)
        layout.addWidget(self.comment_edit)
        layout.addWidget(self.anonymous_checkbox)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_feedback(self):
        selected_button = self.button_group.checkedButton()
        mood = selected_button.text() if selected_button else None
        comment = self.comment_edit.toPlainText()
        anonymous = self.anonymous_checkbox.isChecked()
        
        if not mood:
            QMessageBox.warning(self, "Validation Error", "Please select your mood before submitting.")
            return

        self.submit_callback(self.account_id, mood, comment, anonymous)
        self.accept()