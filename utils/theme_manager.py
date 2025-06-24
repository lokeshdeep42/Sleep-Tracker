# utils/theme_manager.py
import json
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QPalette

class ThemeManager:
    def __init__(self):
        self.settings = QSettings("EmployeeTracker", "Theme")
        self.current_theme = self.settings.value("theme", "system")
        
    def get_current_theme(self):
        """Get the currently selected theme"""
        return self.current_theme
    
    def set_theme(self, theme_name):
        """Set and save the current theme"""
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        
    def is_dark_mode(self):
        """Determine if we should use dark mode"""
        if self.current_theme == "dark":
            return True
        elif self.current_theme == "light":
            return False
        else:  # system
            return self.is_system_dark_mode()
    
    def is_system_dark_mode(self):
        """Detect if system is in dark mode"""
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                # Check if window background is darker than text
                window_color = palette.color(QPalette.Window)
                text_color = palette.color(QPalette.WindowText)
                
                # Calculate luminance
                window_luminance = (0.299 * window_color.red() + 
                                  0.587 * window_color.green() + 
                                  0.114 * window_color.blue())
                text_luminance = (0.299 * text_color.red() + 
                                0.587 * text_color.green() + 
                                0.114 * text_color.blue())
                
                return window_luminance < text_luminance
        except:
            pass
        return False
    
    def get_theme_styles(self):
        """Get CSS styles based on current theme"""
        if self.is_dark_mode():
            return self.get_dark_theme_styles()
        else:
            return self.get_light_theme_styles()
    
    def get_light_theme_styles(self):
        """Light theme CSS styles"""
        return {
            'main_widget': """
                QWidget { 
                    background-color: #f0f4f8; 
                    font-family: Arial; 
                    font-size: 14px;
                    color: #2c3e50;
                }
            """,
            'header_label': """
                QLabel { 
                    font-size: 18px; 
                    font-weight: bold; 
                    color: #2c3e50; 
                }
            """,
            'info_label': """
                QLabel { 
                    font-size: 12px; 
                    color: #666; 
                    font-weight: normal;
                }
            """,
            'button': """
                QPushButton {
                    background-color: #007bff; 
                    color: white; 
                    padding: 8px 16px; 
                    border-radius: 5px; 
                    font-weight: bold;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover { 
                    background-color: #0056b3; 
                }
                QPushButton:disabled { 
                    background-color: #cccccc; 
                    color: #555555; 
                }
            """,
            'input_field': """
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #bdc3c7;
                    border-radius: 6px;
                    font-size: 14px;
                    background-color: #ffffff;
                    color: #2c3e50;
                }
                QLineEdit:focus {
                    border: 2px solid #007bff;
                }
            """,
            'combo_box': """
                QComboBox {
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #ffffff;
                    color: #2c3e50;
                    min-width: 80px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #2c3e50;
                    selection-background-color: #007bff;
                    selection-color: white;
                }
            """,
            'date_edit': """
                QDateEdit {
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #ffffff;
                    color: #2c3e50;
                }
            """,
            'table': """
                QTableWidget { 
                    background-color: #ffffff; 
                    font-size: 13px;
                    gridline-color: #e0e0e0;
                    color: #2c3e50;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    padding: 8px;
                    border: 1px solid #e0e0e0;
                    font-weight: bold;
                }
            """,
            'group_box': """
                QGroupBox { 
                    background-color: #e9eff5; 
                    border-radius: 6px; 
                    padding: 8px; 
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    border: 1px solid #d0d7de;
                }
            """,
            'checkbox': """
                QCheckBox {
                    color: #2c3e50;
                    font-size: 13px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    background-color: #ffffff;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #007bff;
                    background-color: #007bff;
                    border-radius: 3px;
                }
            """
        }
    
    def get_dark_theme_styles(self):
        """Dark theme CSS styles"""
        return {
            'main_widget': """
                QWidget { 
                    background-color: #1e1e1e; 
                    font-family: Arial; 
                    font-size: 14px;
                    color: #e0e0e0;
                }
            """,
            'header_label': """
                QLabel { 
                    font-size: 18px; 
                    font-weight: bold; 
                    color: #ffffff; 
                }
            """,
            'info_label': """
                QLabel { 
                    font-size: 12px; 
                    color: #b0b0b0; 
                    font-weight: normal;
                }
            """,
            'button': """
                QPushButton {
                    background-color: #0d7377; 
                    color: #ffffff; 
                    padding: 8px 16px; 
                    border-radius: 5px; 
                    font-weight: bold;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover { 
                    background-color: #14a085; 
                }
                QPushButton:disabled { 
                    background-color: #555555; 
                    color: #888888; 
                }
            """,
            'input_field': """
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    font-size: 14px;
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                }
                QLineEdit:focus {
                    border: 2px solid #0d7377;
                }
            """,
            'combo_box': """
                QComboBox {
                    padding: 5px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    min-width: 80px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                    background-color: #2d2d2d;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    selection-background-color: #0d7377;
                    selection-color: white;
                    border: 1px solid #555555;
                }
            """,
            'date_edit': """
                QDateEdit {
                    padding: 5px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                }
            """,
            'table': """
                QTableWidget { 
                    background-color: #2d2d2d; 
                    font-size: 13px;
                    gridline-color: #555555;
                    color: #e0e0e0;
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 8px;
                    border: 1px solid #555555;
                    font-weight: bold;
                }
                QTableWidget::item:selected {
                    background-color: #0d7377;
                    color: white;
                }
            """,
            'group_box': """
                QGroupBox { 
                    background-color: #3d3d3d; 
                    border-radius: 6px; 
                    padding: 8px; 
                    font-size: 14px;
                    font-weight: bold;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
            """,
            'checkbox': """
                QCheckBox {
                    color: #e0e0e0;
                    font-size: 13px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #555555;
                    background-color: #2d2d2d;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #0d7377;
                    background-color: #0d7377;
                    border-radius: 3px;
                }
            """
        }
theme_manager = ThemeManager()