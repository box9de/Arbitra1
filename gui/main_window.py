# gui/main_window.py — ИСПРАВЛЕНО (добавлен импорт ccxt)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QGroupBox, QListWidget, QTextEdit, QStatusBar,
    QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime
import ccxt   # ← ЭТО БЫЛО ЗАБЫТО

from gui.tabs.single_exchange_tab import SingleExchangeTab
from gui.tabs.monitoring_tab import MonitoringTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbitra — Funding & Price Arbitrage Monitor")
        self.resize(1450, 820)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Левая часть — вкладки
        left_layout = QVBoxLayout()
        title = QLabel("Arbitra — Funding & Price Arbitrage Monitor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E90FF;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(MonitoringTab(), "Мониторинг")
        self.tabs.addTab(QWidget(), "Торговля")
        self.tabs.addTab(self.create_exchanges_tab(), "Биржи")
        self.tabs.addTab(QWidget(), "Тестирование")
        left_layout.addWidget(self.tabs)

        main_layout.addLayout(left_layout, 4)

        # Правый сайдбар
        self.sidebar = QVBoxLayout()

        stat_group = QGroupBox("📊 Статистика")
        stat_layout = QVBoxLayout(stat_group)
        self.stat_list = QListWidget()
        stat_layout.addWidget(self.stat_list)
        self.sidebar.addWidget(stat_group)

        log_group = QGroupBox("📜 Лог системы")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        self.sidebar.addWidget(log_group)

        main_layout.addLayout(self.sidebar, 1)

        # Статус-бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе • Последнее обновление: —")

        # Примеры
        self.add_log("✅ Приложение запущено")
        self.add_stat("Bybit: 553 Spot + 421 Futures", "Сегодня 15:18")

    def create_exchanges_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        tabs = QTabWidget()

        tabs.addTab(SingleExchangeTab("Binance", ccxt.binance()), "Binance")
        tabs.addTab(SingleExchangeTab("Bybit", ccxt.bybit()), "Bybit")
        tabs.addTab(SingleExchangeTab("OKX", ccxt.okx()), "OKX")

        layout.addWidget(tabs)
        return tab

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def add_stat(self, text: str, time: str = None):
        if time is None:
            time = datetime.now().strftime("%H:%M")
        self.stat_list.addItem(f"{time} — {text}")