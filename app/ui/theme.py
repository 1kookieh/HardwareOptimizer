DARK_QSS = """
QWidget { background-color: #0B1120; color: #E5E7EB; font-family: 'Segoe UI', Inter, Arial; font-size: 14px; }
QFrame#Sidebar, QWidget#Sidebar { background-color: #111827; border-right: 1px solid #334155; }
QLabel#Title { font-size: 22px; font-weight: 700; color: #F8FAFC; }
QLabel#Subtitle { color: #9CA3AF; font-size: 13px; }
QPushButton {
    background-color: #1F2937; color: #E5E7EB; border: 1px solid #334155;
    border-radius: 8px; padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { background-color: #2C3A50; }
QPushButton:disabled { color: #64748B; }
QPushButton#Primary { background-color: #2563EB; color: #FFFFFF; border: none; }
QPushButton#Primary:hover { background-color: #1D4ED8; }
QPushButton#Danger { background-color: #EF4444; color: #FFFFFF; border: none; }
QPushButton#Success { background-color: #22C55E; color: #052E16; border: none; }
QListWidget, QTreeWidget, QTableWidget, QComboBox, QLineEdit, QTextEdit {
    background-color: #111827; border: 1px solid #334155; border-radius: 8px; padding: 4px;
    color: #E5E7EB;
    selection-background-color: #2563EB; selection-color: #FFFFFF;
}
QTableWidget { gridline-color: #334155; alternate-background-color: #1F2937; }
QTabWidget::pane { border: 1px solid #334155; border-radius: 8px; background-color: #111827; }
QTabBar::tab {
    background: #0B1120; color: #9CA3AF; padding: 8px 16px;
    border: 1px solid #334155; border-bottom: none;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #111827; color: #F8FAFC; }
QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 16px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #9CA3AF; }
QHeaderView::section { background-color: #1F2937; color: #E5E7EB; padding: 6px; border: none; }
QCheckBox { color: #E5E7EB; }
QStatusBar { background-color: #111827; color: #9CA3AF; }
"""

LIGHT_QSS = """
QWidget { background-color: #F8FAFC; color: #0F172A; font-family: 'Segoe UI', Inter, Arial; font-size: 14px; }
QFrame#Sidebar, QWidget#Sidebar { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
QLabel#Title { font-size: 22px; font-weight: 700; color: #0F172A; }
QLabel#Subtitle { color: #64748B; font-size: 13px; }
QPushButton {
    background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;
    border-radius: 8px; padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { background-color: #F1F5F9; }
QPushButton:disabled { color: #94A3B8; background-color: #F1F5F9; }
QPushButton#Primary { background-color: #2563EB; color: #FFFFFF; border: none; }
QPushButton#Primary:hover { background-color: #1D4ED8; }
QPushButton#Danger { background-color: #EF4444; color: #FFFFFF; border: none; }
QPushButton#Success { background-color: #16A34A; color: #FFFFFF; border: none; }
QListWidget, QTreeWidget, QTableWidget, QComboBox, QLineEdit, QTextEdit {
    background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 4px;
    color: #0F172A;
    selection-background-color: #2563EB; selection-color: #FFFFFF;
}
QTableWidget { gridline-color: #E2E8F0; alternate-background-color: #F8FAFC; }
QTabWidget::pane { border: 1px solid #CBD5E1; border-radius: 8px; background-color: #FFFFFF; }
QTabBar::tab {
    background: #F1F5F9; color: #64748B; padding: 8px 16px;
    border: 1px solid #CBD5E1; border-bottom: none;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; }
QGroupBox { border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 16px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #64748B; }
QHeaderView::section { background-color: #F1F5F9; color: #0F172A; padding: 6px; border: none; }
QCheckBox { color: #0F172A; }
QStatusBar { background-color: #FFFFFF; color: #64748B; }
"""

# Backward compat
QSS = DARK_QSS
