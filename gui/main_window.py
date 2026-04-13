# gui/main_window.py — Главное окно + статус-бар внизу

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QStatusBar
)
from PySide6.QtCore import Qt
from gui.tabs.monitoring_tab import MonitoringTab
from gui.tabs.exchanges_tab import ExchangesTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbitra — Funding & Price Arbitrage Monitor")
        self.resize(1350, 820)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Заголовок
        title = QLabel("Arbitra — Funding & Price Arbitrage Monitor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E90FF;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Основные вкладки
        self.tabs = QTabWidget()
        self.tabs.addTab(MonitoringTab(), "Мониторинг")
        self.tabs.addTab(QWidget(), "Торговля")
        self.tabs.addTab(ExchangesTab(), "Биржи")
        self.tabs.addTab(QWidget(), "Тестирование")

        main_layout.addWidget(title)
        main_layout.addWidget(self.tabs)

        # === СТАТУС-БАР ВНИЗУ ===
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.statusBar.showMessage("Готов к работе • Последнее обновление: —")