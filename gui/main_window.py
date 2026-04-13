# gui/main_window.py — Добавлен правый боковой бар (заглушки)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QGroupBox, QListWidget, QTextEdit, QStatusBar
)
from PySide6.QtCore import Qt
from gui.tabs.monitoring_tab import MonitoringTab
from gui.tabs.single_exchange_tab import SingleExchangeTab   # для бирж
import ccxt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbitra — Funding & Price Arbitrage Monitor")
        self.resize(1700, 920)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # === ЛЕВАЯ ЧАСТЬ — ВКЛАДКИ (80%) ===
        self.tabs = QTabWidget()
        self.tabs.addTab(MonitoringTab(), "Мониторинг")
        self.tabs.addTab(QWidget(), "Торговля")
        self.tabs.addTab(QWidget(), "Тестирование")

        # Вкладка Биржи
        exchanges_tab = QTabWidget()
        exchanges_tab.addTab(SingleExchangeTab("Binance", ccxt.binance()), "Binance")
        exchanges_tab.addTab(SingleExchangeTab("Bybit", ccxt.bybit()), "Bybit")
        exchanges_tab.addTab(SingleExchangeTab("OKX", ccxt.okx()), "OKX")
        self.tabs.addTab(exchanges_tab, "Биржи")

        main_layout.addWidget(self.tabs, 4)   # 80% ширины

        # === ПРАВЫЙ БОКОВОЙ БАР (20%) ===
        sidebar = QWidget()
        sidebar.setMaximumWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(12)

        # Верхняя часть — Статистика
        stat_group = QGroupBox("📊 Статистика")
        stat_layout = QVBoxLayout(stat_group)
        self.stats_list = QListWidget()
        stat_layout.addWidget(self.stats_list)
        sidebar_layout.addWidget(stat_group, 1)

        # Нижняя часть — Лог системы
        log_group = QGroupBox("📜 Лог системы")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        sidebar_layout.addWidget(log_group, 1)

        main_layout.addWidget(sidebar, 1)   # 20% ширины

        # Статус-бар внизу
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе • Последнее обновление: —")

        # Примеры для заглушки
        self.stats_list.addItem("Сегодня 15:18 — Bybit: 553 Spot + 421 Futures")
        self.stats_list.addItem("Сегодня 15:20 — Найдено 3 выгодных спреда")
        self.log_text.append("[15:18] ✅ Bybit успешно импортирован")
        self.log_text.append("[15:19] 📡 Соединение с Binance OK")