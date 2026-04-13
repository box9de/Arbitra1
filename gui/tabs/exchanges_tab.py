# gui/tabs/exchanges_tab.py — Контейнер для всех бирж

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt
import ccxt
from gui.tabs.single_exchange_tab import SingleExchangeTab

class ExchangesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QTabWidget()  # Главные вкладки по биржам
        layout.addWidget(title)

        # Binance
        binance = ccxt.binance()
        title.addTab(SingleExchangeTab("Binance", binance), "Binance")

        # Bybit
        bybit = ccxt.bybit()
        title.addTab(SingleExchangeTab("Bybit", bybit), "Bybit")

        # OKX
        okx = ccxt.okx()
        title.addTab(SingleExchangeTab("OKX", okx), "OKX")