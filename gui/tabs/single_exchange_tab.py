# gui/tabs/single_exchange_tab.py — Обновление в отдельном потоке

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
import ccxt

class ExchangeDataFetcher(QThread):
    data_ready = Signal(dict)

    def __init__(self, exchange, exchange_name):
        super().__init__()
        self.exchange = exchange
        self.exchange_name = exchange_name

    def run(self):
        try:
            spot_data = []
            futures_data = []

            tokens = ["BTC", "ETH"]

            for token in tokens:
                # Спот
                try:
                    ticker = f"{token}/USDT"
                    data = self.exchange.fetch_ticker(ticker)
                    price = data.get('last') or data.get('close') or 0
                    volume = data.get('quoteVolume') or 0
                    spot_data.append({
                        'token': token,
                        'price': price,
                        'volume': volume
                    })
                except:
                    pass

                # Фьючерсы
                try:
                    ticker = f"{token}/USDT:USDT"
                    ticker_data = self.exchange.fetch_ticker(ticker)
                    price = ticker_data.get('last') or ticker_data.get('close') or 0
                    volume = ticker_data.get('quoteVolume') or 0

                    funding = self.exchange.fetch_funding_rate(ticker)
                    rate = funding.get('fundingRate') or funding.get('predictedFundingRate') or 0
                    rate_pct = rate * 100

                    futures_data.append({
                        'token': token,
                        'price': price,
                        'funding': rate_pct,
                        'volume': volume
                    })
                except:
                    pass

            self.data_ready.emit({
                'spot': spot_data,
                'futures': futures_data,
                'exchange_name': self.exchange_name
            })
        except Exception as e:
            print(f"Ошибка в {self.exchange_name}:", e)

class SingleExchangeTab(QWidget):
    def __init__(self, exchange_name: str, exchange_instance):
        super().__init__()
        self.exchange_name = exchange_name
        self.exchange = exchange_instance

        layout = QVBoxLayout(self)
        title = QLabel(f"{exchange_name} — Спот и Фьючерсы")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.inner_tabs = QTabWidget()
        self.spot_widget = QWidget()
        self.futures_widget = QWidget()

        self.inner_tabs.addTab(self.spot_widget, "Спот")
        self.inner_tabs.addTab(self.futures_widget, "Фьючерсы")

        layout.addWidget(self.inner_tabs)

        self.setup_tables()

        self.fetcher = ExchangeDataFetcher(self.exchange, exchange_name)
        self.fetcher.data_ready.connect(self.update_tables)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_fetch)
        self.timer.start(15000)

        QTimer.singleShot(800, self.start_fetch)

    def setup_tables(self):
        # Spot
        self.spot_table = QTableWidget()
        self.spot_table.setColumnCount(5)
        self.spot_table.setHorizontalHeaderLabels(["Токен", "Цена", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт"])
        self.spot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.spot_table.setAlternatingRowColors(True)
        layout = QVBoxLayout(self.spot_widget)
        layout.addWidget(self.spot_table)

        # Futures
        self.futures_table = QTableWidget()
        self.futures_table.setColumnCount(8)
        self.futures_table.setHorizontalHeaderLabels(["Токен", "Цена", "Фандинг", "Таймер", "Период", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт"])
        self.futures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.futures_table.setAlternatingRowColors(True)
        layout = QVBoxLayout(self.futures_widget)
        layout.addWidget(self.futures_table)

    def start_fetch(self):
        if not self.fetcher.isRunning():
            self.fetcher.start()

    def update_tables(self, data):
        # Spot
        self.spot_table.setRowCount(0)
        for item in data['spot']:
            row = self.spot_table.rowCount()
            self.spot_table.insertRow(row)
            self.spot_table.setItem(row, 0, QTableWidgetItem(item['token']))
            self.spot_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.spot_table.setItem(row, 2, QTableWidgetItem(f"{item['volume']:,.0f}"))
            self.spot_table.setItem(row, 3, QTableWidgetItem("—"))
            self.spot_table.setItem(row, 4, QTableWidgetItem("SPOT"))

        # Futures
        self.futures_table.setRowCount(0)
        for item in data['futures']:
            row = self.futures_table.rowCount()
            self.futures_table.insertRow(row)
            self.futures_table.setItem(row, 0, QTableWidgetItem(item['token']))
            self.futures_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.futures_table.setItem(row, 2, QTableWidgetItem(f"{item['funding']:+.4f}%"))
            self.futures_table.setItem(row, 3, QTableWidgetItem("02:14:45"))
            self.futures_table.setItem(row, 4, QTableWidgetItem("8ч"))
            self.futures_table.setItem(row, 5, QTableWidgetItem(f"{item['volume']:,.0f}"))
            self.futures_table.setItem(row, 6, QTableWidgetItem("—"))
            self.futures_table.setItem(row, 7, QTableWidgetItem("PERP"))