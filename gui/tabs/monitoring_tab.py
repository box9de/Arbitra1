# gui/tabs/monitoring_tab.py — Без подвисания + настоящие иконки

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QLabel, QHBoxLayout
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon
import ccxt
import time
import os
from token_map import TOKEN_MAP, get_ticker

class DataFetcher(QThread):
    data_ready = Signal(list)   # отправляем готовые строки

    def run(self):
        try:
            binance = ccxt.binance()
            okx = ccxt.okx()
            bybit = ccxt.bybit()

            exchanges = {"Binance": binance, "OKX": okx, "Bybit": bybit}
            rows = []

            icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")

            for token_key in TOKEN_MAP.keys():
                rates = {}
                prices = {}

                for name, ex in exchanges.items():
                    ticker = get_ticker(token_key, name)
                    if not ticker:
                        continue
                    try:
                        f = ex.fetch_funding_rate(ticker)
                        rate = f.get('fundingRate') or f.get('predictedFundingRate')
                        rates[name] = rate * 100 if rate is not None else 0

                        ticker_data = ex.fetch_ticker(ticker)
                        price = ticker_data.get('last') or ticker_data.get('close')
                        prices[name] = price if price else 0
                    except:
                        pass

                pairs = [("Binance", "Bybit"), ("Binance", "OKX")]

                for ex1, ex2 in pairs:
                    if ex1 not in rates or ex2 not in rates:
                        continue

                    rate1 = rates[ex1]
                    rate2 = rates[ex2]
                    price1 = prices.get(ex1, 0)
                    price2 = prices.get(ex2, 0)
                    funding_spread = rate1 - rate2

                    # Подготовка данных для строки
                    row_data = {
                        'token': token_key,
                        'ex1': ex1,
                        'ex2': ex2,
                        'rate1': rate1,
                        'rate2': rate2,
                        'price1': price1,
                        'price2': price2,
                        'funding_spread': funding_spread,
                        'icons_path': icons_path
                    }
                    rows.append(row_data)

            self.data_ready.emit(rows)

        except Exception as e:
            print("Ошибка в DataFetcher:", e)

class MonitoringTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("Мониторинг спредов")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Токен", "Связка", "Цена", "Фандинг", "Таймер", "Период",
            "Фандинг 24ч", "Годовая ставка", "Фандинг Спред",
            "Ценовой Спред", "Действие"
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

        # Запускаем обновление в отдельном потоке
        self.fetcher = DataFetcher()
        self.fetcher.data_ready.connect(self.update_table_ui)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_fetch)
        self.timer.start(12000)   # каждые 12 секунд

        QTimer.singleShot(500, self.start_fetch)

    def start_fetch(self):
        if not self.fetcher.isRunning():
            self.fetcher.start()

    def update_table_ui(self, rows):
        """Обновление таблицы в главном потоке (без подвисания)"""
        self.table.setRowCount(0)

        for data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(data['token']))

            # Связка с иконками
            link_widget = QWidget()
            link_layout = QHBoxLayout(link_widget)
            link_layout.setContentsMargins(8, 4, 8, 4)
            link_layout.setSpacing(8)

            icon_path1 = os.path.join(data['icons_path'], f"{data['ex1'].lower()}.png")
            icon_path2 = os.path.join(data['icons_path'], f"{data['ex2'].lower()}.png")

            lbl1 = QLabel()
            lbl1.setPixmap(QIcon(icon_path1).pixmap(24, 24))
            lbl1.setText(f" {data['ex1']} ↑")
            lbl1.setStyleSheet("color: #00FF88; font-weight: bold;")

            lbl2 = QLabel()
            lbl2.setPixmap(QIcon(icon_path2).pixmap(24, 24))
            lbl2.setText(f" {data['ex2']} ↓")
            lbl2.setStyleSheet("color: #FF5555; font-weight: bold;")

            link_layout.addWidget(lbl1)
            link_layout.addWidget(lbl2)
            link_layout.addStretch()

            self.table.setCellWidget(row, 1, link_widget)

            self.table.setItem(row, 2, QTableWidgetItem(f"{data['price1']:,.2f}\n{data['price2']:,.2f}"))

            funding_text = f"{data['rate1']:+.4f}%\n{data['rate2']:+.4f}%"
            funding_item = QTableWidgetItem(funding_text)
            funding_item.setForeground(QColor("#00FF88") if data['rate1'] > 0 else QColor("#FF5555"))
            self.table.setItem(row, 3, funding_item)

            self.table.setItem(row, 4, QTableWidgetItem("02:14:45\n02:14:45"))
            self.table.setItem(row, 5, QTableWidgetItem("8ч\n8ч"))
            self.table.setItem(row, 6, QTableWidgetItem("0.012%\n-0.019%"))
            self.table.setItem(row, 7, QTableWidgetItem("+11.2%\n-17.5%"))

            spread_item = QTableWidgetItem(f"{data['funding_spread']:+.3f}%")
            spread_item.setForeground(QColor("#00FF88") if data['funding_spread'] > 0 else QColor("#FF5555"))
            self.table.setItem(row, 8, spread_item)

            self.table.setItem(row, 9, QTableWidgetItem("+0.002%"))

            btn = QPushButton("Торговать")
            btn.clicked.connect(lambda checked=False, t=data['token'], e1=data['ex1'], e2=data['ex2']: 
                               self.trade_clicked(t, e1, e2))
            self.table.setCellWidget(row, 10, btn)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setColumnWidth(1, 240)

    def trade_clicked(self, token, ex1, ex2):
        print(f"✅ Торговать → {token} ({ex1} → {ex2})")