# gui/main_window.py  (фрагмент с импортами и вкладками)

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

# Импорты вкладок
from gui.tabs.monitoring_tab import MonitoringTab
from gui.tabs.exchanges_tab import ExchangesTab          # ← должен быть
from gui.tabs.global_registry_tab import GlobalRegistryTab   # ← НОВАЯ вкладка

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
        main_layout.addWidget(title)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.addTab(MonitoringTab(), "Мониторинг")
        self.tabs.addTab(QWidget(), "Торговля")
        self.tabs.addTab(ExchangesTab(), "Биржи")
        self.tabs.addTab(QWidget(), "Тестирование")
        self.tabs.addTab(GlobalRegistryTab(), "Глобальный реестр")   # ← добавлено

        main_layout.addWidget(self.tabs)

        # Статус-бар
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Готов к работе • Последнее обновление: —")