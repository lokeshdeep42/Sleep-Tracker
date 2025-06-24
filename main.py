import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from gui.login_window import LoginWindow

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'db_config.json')

def check_and_load_config():
    if not os.path.exists(CONFIG_PATH):
        QMessageBox.critical(None, "Missing Configuration",
            f"Configuration file not found at:\n{CONFIG_PATH}\n\nPlease contact admin or provide a valid config.")
        return False

    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        required_keys = {"server", "database", "username", "password"}
        if not required_keys.issubset(config.keys()):
            QMessageBox.critical(None, "Invalid Configuration",
                f"Config file is missing required fields: {required_keys}")
            return False
    except Exception as e:
        QMessageBox.critical(None, "Error Reading Config", str(e))
        return False

    return True

if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not check_and_load_config():
        sys.exit(1)

    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
