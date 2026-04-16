# gui/tabs/exchanges_tab.py
# Контейнер для всех бирж (Binance, Bybit, OKX)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
import ccxt

from gui.tabs.single_exchange_tab import SingleExchangeTab

class ExchangesTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.inner_tabs = QTabWidget()

        # Создаём экземпляры вкладок для каждой биржи
        self.binance_tab = SingleExchangeTab("Binance", ccxt.binance())
        self.bybit_tab   = SingleExchangeTab("Bybit",   ccxt.bybit())
        self.okx_tab     = SingleExchangeTab("OKX",     ccxt.okx())

        # Добавляем их как подпапки
        self.inner_tabs.addTab(self.binance_tab, "Binance")
        self.inner_tabs.addTab(self.bybit_tab,   "Bybit")
        self.inner_tabs.addTab(self.okx_tab,     "OKX")

        layout.addWidget(self.inner_tabs)