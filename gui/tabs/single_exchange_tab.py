# gui/tabs/single_exchange_tab.py — Bybit pybit SDK + сортировка + пары в Spot

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
        self.exchange = exchange_instance
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
        # Spot
        self.spot_table = QTableWidget()
        self.spot_table.setColumnCount(6)
        self.spot_table.setHorizontalHeaderLabels(["Пара", "Цена", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт", "Мониторинг ВКЛ."])
        self.spot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.spot_table.setAlternatingRowColors(True)
        self.spot_table.setSortingEnabled(True)          # ← ВКЛЮЧЕНА СОРТИРОВКА
        QVBoxLayout(self.spot_widget).addWidget(self.spot_table)

        # Futures
        self.futures_table = QTableWidget()
        self.futures_table.setColumnCount(9)
        self.futures_table.setHorizontalHeaderLabels(["Токен", "Цена", "Фандинг", "Таймер", "Период", "Объём 24ч (USDT)", "Открытые позиции (USDT)", "Контракт", "Мониторинг ВКЛ."])
        self.futures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.futures_table.setAlternatingRowColors(True)
        self.futures_table.setSortingEnabled(True)       # ← ВКЛЮЧЕНА СОРТИРОВКА
        QVBoxLayout(self.futures_widget).addWidget(self.futures_table)

    def import_tokens(self):
        reply = QMessageBox.question(self, "Подтверждение",
            f"Загрузить ВСЕ токены с {self.exchange_name}?\n\nЭто может занять 10–40 секунд.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.import_btn.setEnabled(False)
        self.import_btn.setText("Загрузка...")

        progress = QProgressDialog("Загрузка токенов...", "Отмена", 0, 100, self)
        progress.setWindowTitle("Импорт")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            if self.exchange_name == "Bybit":
                from pybit.unified_trading import HTTP
                session = HTTP(testnet=False)

                spot_resp = session.get_instruments_info(category="spot")
                spot_instr = spot_resp.get("result", {}).get("list", [])

                spot_tickers_resp = session.get_tickers(category="spot")
                spot_tickers = spot_tickers_resp.get("result", {}).get("list", [])

                futures_resp = session.get_instruments_info(category="linear")
                futures_instr = futures_resp.get("result", {}).get("list", [])

                futures_tickers_resp = session.get_tickers(category="linear")
                futures_tickers = futures_tickers_resp.get("result", {}).get("list", [])

                spot_data = []
                futures_data = []
                seen_futures = set()

                # Spot — показываем полную пару (ETH/USDT, ETH/USDC и т.д.)
                for inst in spot_instr:
                    if not isinstance(inst, dict):
                        continue
                    symbol = inst.get("symbol")
                    base = inst.get("baseCoin")
                    if not base or not symbol:
                        continue
                    if not (str(symbol).endswith("USDT") or str(symbol).endswith("USDC")):
                        continue

                    ticker = next((t for t in spot_tickers if isinstance(t, dict) and t.get("symbol") == symbol), None)
                    if ticker:
                        price = float(ticker.get("lastPrice") or 0)
                        volume = float(ticker.get("volume24h") or 0)
                        spot_data.append({"pair": symbol, "price": price, "volume": volume})

                # Futures
                for inst in futures_instr:
                    if not isinstance(inst, dict):
                        continue
                    symbol = inst.get("symbol")
                    base = inst.get("baseCoin")
                    if not base or base in seen_futures:
                        continue
                    ticker = next((t for t in futures_tickers if isinstance(t, dict) and t.get("symbol") == symbol), None)
                    if ticker:
                        price = float(ticker.get("lastPrice") or 0)
                        volume = float(ticker.get("volume24h") or 0)

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
                            "price": price,
                            "funding": rate,
                            "volume": volume
                        })
                        seen_futures.add(base)

            else:
                # Binance / OKX (ccxt)
                self.exchange.load_markets()
                markets = self.exchange.markets
                tickers = self.exchange.fetch_tickers()

                spot_data = []
                futures_data = []
                seen = set()

                for symbol, market in markets.items():
                    if not market.get('active'):
                        continue
                    base = market.get('base')
                    if not base or base in seen:
                        continue

                    if ':' in symbol and symbol.endswith(':USDT'):
                        ticker = tickers.get(symbol)
                        if ticker:
                            price = ticker.get('last') or ticker.get('close') or 0
                            volume = ticker.get('quoteVolume') or 0
                            try:
                                fr = self.exchange.fetch_funding_rate(symbol)
                                rate = (fr.get('fundingRate') or fr.get('predictedFundingRate') or 0) * 100
                            except:
                                rate = 0
                            futures_data.append({"token": base, "price": price, "funding": rate, "volume": volume})
                            seen.add(base)
                    elif '/USDT' in symbol and ':' not in symbol:
                        ticker = tickers.get(symbol)
                        if ticker:
                            price = ticker.get('last') or ticker.get('close') or 0
                            volume = ticker.get('quoteVolume') or 0
                            spot_data.append({"pair": symbol, "price": price, "volume": volume})
                            seen.add(base)

            data_to_save = {
                'spot': spot_data,
                'futures': futures_data,
                'last_update': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.update_tables(data_to_save)

            QMessageBox.information(
                self, "Импорт завершён",
                f"Загружено токенов с {self.exchange_name}:\n"
                f"Спот: {len(spot_data)} шт.\n"
                f"Фьючерсы: {len(futures_data)} шт."
            )

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
        # Spot — теперь показываем полную пару
        self.spot_table.setRowCount(0)
        for item in data.get('spot', []):
            row = self.spot_table.rowCount()
            self.spot_table.insertRow(row)
            self.spot_table.setItem(row, 0, QTableWidgetItem(item.get('pair', item.get('token', ''))))
            self.spot_table.setItem(row, 1, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.spot_table.setItem(row, 2, QTableWidgetItem(f"{item['volume']:,.0f}"))
            self.spot_table.setItem(row, 3, QTableWidgetItem("—"))
            self.spot_table.setItem(row, 4, QTableWidgetItem("SPOT"))
            check = QTableWidgetItem()
            check.setCheckState(Qt.CheckState.Unchecked)
            self.spot_table.setItem(row, 5, check)

        # Futures
        self.futures_table.setRowCount(0)
        for item in data.get('futures', []):
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
            check = QTableWidgetItem()
            check.setCheckState(Qt.CheckState.Unchecked)
            self.futures_table.setItem(row, 8, check)