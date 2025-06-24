import pyodbc
import json
import os

def load_db_config():
    config_path = os.path.join(os.path.dirname(__file__), "../config/db_config.json")
    with open(config_path, "r") as file:
        return json.load(file)

def get_connection():
    config = load_db_config()
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
    )
    return conn