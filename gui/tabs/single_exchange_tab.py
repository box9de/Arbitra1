# gui/tabs/single_exchange_tab.py — Максимум фьючерсов Binance

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QHBoxLayout, QMessageBox,
    QProgressDialog
)
from PySide6.QtCore import QTimer, Qt
import ccxt
import json
import os
from datetime import datetime

class SingleExchangeTab(QWidget):
    def __init__(self, exchange_name: str, exchange_instance):
        super().__init__()
        self.exchange_name = exchange_name
        self.spot_exchange = exchange_instance
        self.data_file = f"data/exchanges/{exchange_name.lower()}.json"

        os.makedirs("data/exchanges", exist_ok=True)

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel(f"{exchange_name} — Спот и Фьючерсы")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self.import_btn = QPushButton("Импортировать все токены")
        self.import_btn.clicked.connect(self.import_tokens)
        header.addWidget(self.import_btn)

        layout.addLayout(header)

        self.inner_tabs = QTabWidget()
        self.spot_widget = QWidget()
        self.futures_widget = QWidget()
        self.inner_tabs.addTab(self.spot_widget, "Спот")
        self.inner_tabs.addTab(self.futures_widget, "Фьючерсы")
        layout.addWidget(self.inner_tabs)

        self.setup_tables()
        QTimer.singleShot(300, self.load_from_file)

    def setup_tables(self):
        self.spot_table = QTableWidget()
        self.spot_table.setColumnCount(6)
        self.spot_table.setHorizontalHeaderLabels(["Пара", "Цена", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт", "Мониторинг ВКЛ."])
        self.spot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.spot_table.setAlternatingRowColors(True)
        self.spot_table.setSortingEnabled(True)
        QVBoxLayout(self.spot_widget).addWidget(self.spot_table)

        self.futures_table = QTableWidget()
        self.futures_table.setColumnCount(9)
        self.futures_table.setHorizontalHeaderLabels(["Токен", "Цена", "Фандинг", "Таймер", "Период", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт", "Мониторинг ВКЛ."])
        self.futures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.futures_table.setAlternatingRowColors(True)
        self.futures_table.setSortingEnabled(True)
        QVBoxLayout(self.futures_widget).addWidget(self.futures_table)

    def import_tokens(self):
        reply = QMessageBox.question(self, "Подтверждение",
            f"Загрузить ВСЕ токены с {self.exchange_name}?\n\nМожет занять 20–50 секунд.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.import_btn.setEnabled(False)
        self.import_btn.setText("Загрузка...")

        progress = QProgressDialog("Загрузка токенов...", None, 0, 100, self)
        progress.setWindowTitle("Импорт")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            spot_data = []
            futures_data = []
            seen = set()

            if self.exchange_name == "Bybit":
                # Bybit — без изменений (работает идеально)
                from pybit.unified_trading import HTTP
                session = HTTP(testnet=False)
                # ... (тот же код Bybit, что был раньше — не трогаем)

                spot_instr = session.get_instruments_info(category="spot").get("result", {}).get("list", [])
                spot_tickers = session.get_tickers(category="spot").get("result", {}).get("list", [])
                for inst in spot_instr:
                    symbol = inst.get("symbol")
                    if symbol and (str(symbol).endswith("USDT") or str(symbol).endswith("USDC")):
                        ticker = next((t for t in spot_tickers if t.get("symbol") == symbol), None)
                        if ticker:
                            spot_data.append({
                                "pair": symbol,
                                "price": float(ticker.get("lastPrice") or 0),
                                "volume": float(ticker.get("volume24h") or 0)
                            })

                futures_instr = session.get_instruments_info(category="linear").get("result", {}).get("list", [])
                futures_tickers = session.get_tickers(category="linear").get("result", {}).get("list", [])
                for inst in futures_instr:
                    base = inst.get("baseCoin")
                    symbol = inst.get("symbol")
                    if base and base not in seen:
                        ticker = next((t for t in futures_tickers if t.get("symbol") == symbol), None)
                        if ticker:
                            rate = 0.0
                            try:
                                fr = session.get_funding_rate(symbol=symbol)
                                result = fr.get("result")
                                if isinstance(result, list) and result:
                                    rate = float(result[0].get("fundingRate", 0)) * 100
                                elif isinstance(result, dict):
                                    rate = float(result.get("fundingRate", 0)) * 100
                            except:
                                pass
                            futures_data.append({
                                "token": base,
                                "price": float(ticker.get("lastPrice") or 0),
                                "funding": rate,
                                "volume": float(ticker.get("volume24h") or 0)
                            })
                            seen.add(base)

            else:
                # Binance + OKX
                spot_ex = self.spot_exchange
                futures_ex = ccxt.binanceusdm() if self.exchange_name == "Binance" else ccxt.okx()

                spot_ex.load_markets()
                futures_ex.load_markets()

                tickers_spot = spot_ex.fetch_tickers()
                tickers_fut = futures_ex.fetch_tickers()

                # Spot — без изменений
                for symbol, market in spot_ex.markets.items():
                    if not market.get('active') or not market.get('spot'): continue
                    base = market.get('base')
                    if base in seen or not (symbol.endswith('/USDT') or symbol.endswith('/USDC')): continue
                    ticker = tickers_spot.get(symbol)
                    if ticker:
                        spot_data.append({
                            "pair": symbol,
                            "price": float(ticker.get('last') or ticker.get('close') or 0),
                            "volume": float(ticker.get('quoteVolume') or 0)
                        })
                        seen.add(base)

                # Futures — МАКСИМАЛЬНО ШИРОКИЙ ФИЛЬТР
                for symbol, market in futures_ex.markets.items():
                    if not market.get('active'): continue
                    base = market.get('base')
                    if base and base not in seen:
                        ticker = tickers_fut.get(symbol)
                        if ticker:
                            try:
                                fr = futures_ex.fetch_funding_rate(symbol)
                                rate = (fr.get('fundingRate') or fr.get('predictedFundingRate') or 0) * 100
                            except:
                                rate = 0.0
                            futures_data.append({
                                "token": base,
                                "price": float(ticker.get('last') or ticker.get('close') or 0),
                                "funding": rate,
                                "volume": float(ticker.get('quoteVolume') or 0)
                            })
                            seen.add(base)

            # Сохранение
            data_to_save = {
                'spot': spot_data,
                'futures': futures_data,
                'last_update': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.update_tables(data_to_save)

            QMessageBox.information(self, "Импорт завершён",
                f"Загружено токенов с {self.exchange_name}:\n"
                f"Спот: {len(spot_data)} шт.\n"
                f"Фьючерсы: {len(futures_data)} шт.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))
        finally:
            progress.close()
            self.import_btn.setEnabled(True)
            self.import_btn.setText("Импортировать все токены")

    def load_from_file(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.update_tables(data)
            except:
                pass

    def update_tables(self, data):
        self.spot_table.setRowCount(0)
        for item in data.get('spot', []):
            row = self.spot_table.rowCount()
            self.spot_table.insertRow(row)
            self.spot_table.setItem(row, 0, QTableWidgetItem(item['pair']))
            self.spot_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.spot_table.setItem(row, 2, QTableWidgetItem(f"{item['volume']:,.0f}"))
            self.spot_table.setItem(row, 3, QTableWidgetItem("—"))
            self.spot_table.setItem(row, 4, QTableWidgetItem("SPOT"))
            check = QTableWidgetItem(); check.setCheckState(Qt.CheckState.Unchecked)
            self.spot_table.setItem(row, 5, check)

        self.futures_table.setRowCount(0)
        for item in data.get('futures', []):
            row = self.futures_table.rowCount()
            self.futures_table.insertRow(row)
            self.futures_table.setItem(row, 0, QTableWidgetItem(item['token']))
            self.futures_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.futures_table.setItem(row, 2, QTableWidgetItem(f"{item['funding']:+.4f}%"))
            self.futures_table.setItem(row, 3, QTableWidgetItem("—"))
            self.futures_table.setItem(row, 4, QTableWidgetItem("8ч"))
            self.futures_table.setItem(row, 5, QTableWidgetItem(f"{item['volume']:,.0f}"))
            self.futures_table.setItem(row, 6, QTableWidgetItem("—"))
            self.futures_table.setItem(row, 7, QTableWidgetItem("PERP"))
            check = QTableWidgetItem(); check.setCheckState(Qt.CheckState.Unchecked)
            self.futures_table.setItem(row, 8, check)