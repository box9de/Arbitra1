# gui/tabs/single_exchange_tab.py
# ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ — готова к глобальному автообновлению

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QHBoxLayout, QMessageBox,
    QProgressDialog, QApplication
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
import ccxt
import json
import os
from datetime import datetime, timedelta


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

        self.spot_table.cellClicked.connect(self._copy_contract)
        self.futures_table.cellClicked.connect(self._copy_contract)

    def setup_tables(self):
        # Спот
        self.spot_table = QTableWidget()
        self.spot_table.setColumnCount(6)
        self.spot_table.setHorizontalHeaderLabels(["Пара", "Цена", "Изм. 24ч", "Объём 24ч", "Адрес контракта", "Сеть"])
        self.spot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.spot_table.setAlternatingRowColors(True)
        self.spot_table.setSortingEnabled(True)
        QVBoxLayout(self.spot_widget).addWidget(self.spot_table)

        # Фьючерсы
        self.futures_table = QTableWidget()
        self.futures_table.setColumnCount(8)
        self.futures_table.setHorizontalHeaderLabels([
            "Токен", "Цена", "Фандинг", "След. фандинг", "Объём 24ч",
            "Открытый интерес", "Адрес контракта", "Сеть"
        ])
        self.futures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.futures_table.setAlternatingRowColors(True)
        self.futures_table.setSortingEnabled(True)
        QVBoxLayout(self.futures_widget).addWidget(self.futures_table)

    def _copy_contract(self, row: int, column: int):
        table = self.sender()
        if table is None or column != 6:
            return
        item = table.item(row, column)
        if item and item.text() != "—":
            QApplication.clipboard().setText(item.text())

    def _calculate_next_funding(self) -> str:
        now = datetime.utcnow()
        hour = now.hour
        if hour < 8:
            next_h = 8
        elif hour < 16:
            next_h = 16
        else:
            next_h = 0
        next_time = now.replace(hour=next_h, minute=0, second=0, microsecond=0)
        if next_h == 0:
            next_time += timedelta(days=1)
        delta = next_time - now
        h = delta.seconds // 3600
        m = (delta.seconds % 3600) // 60
        return f"через {h}ч {m}м"

    def import_tokens(self):
        reply = QMessageBox.question(self, "Подтверждение",
            f"Загрузить ВСЕ токены с {self.exchange_name}?\n\nМожет занять 30–90 секунд.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.import_btn.setEnabled(False)
        self.import_btn.setText("Загрузка...")

        progress = QProgressDialog("Загрузка токенов...", None, 0, 100, self)
        progress.setWindowTitle("Импорт")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        spot_data = []
        futures_data = []
        seen = set()

        next_funding_str = self._calculate_next_funding()

        try:
            if self.exchange_name == "Bybit":
                from pybit.unified_trading import HTTP
                session = HTTP(testnet=False)

                # Spot Bybit
                spot_instr = session.get_instruments_info(category="spot").get("result", {}).get("list", [])
                spot_tickers = session.get_tickers(category="spot").get("result", {}).get("list", [])
                for inst in spot_instr:
                    symbol = inst.get("symbol")
                    if symbol and (symbol.endswith("USDT") or symbol.endswith("USDC")):
                        ticker = next((t for t in spot_tickers if t.get("symbol") == symbol), {})
                        base = symbol.split("/")[0]
                        spot_data.append({
                            "pair": symbol,
                            "price": float(ticker.get("lastPrice") or 0),
                            "change24h": float(ticker.get("price24hPcnt") or 0) * 100,
                            "volume": float(ticker.get("volume24h") or 0),
                            "contract": "—",
                            "network": "—"
                        })

                # Futures Bybit
                futures_instr = session.get_instruments_info(category="linear").get("result", {}).get("list", [])
                futures_tickers = session.get_tickers(category="linear").get("result", {}).get("list", [])
                for inst in futures_instr:
                    base = inst.get("baseCoin")
                    if base and base not in seen:
                        ticker = next((t for t in futures_tickers if t.get("symbol") == inst.get("symbol")), {})
                        rate = 0.0
                        period = "8h"
                        try:
                            fr = session.get_funding_rate(symbol=inst.get("symbol"))
                            result = fr.get("result", {})
                            if isinstance(result, list) and result:
                                rate = float(result[0].get("fundingRate", 0)) * 100
                                period = result[0].get("fundingInterval", "8h").replace("h", "h")
                        except:
                            pass
                        futures_data.append({
                            "token": base,
                            "price": float(ticker.get("lastPrice") or 0),
                            "funding": rate,
                            "funding_period": period,
                            "next_funding": next_funding_str,
                            "volume": float(ticker.get("volume24h") or 0),
                            "open_interest": float(ticker.get("openInterest") or 0),
                            "contract": "PERP",
                            "network": "—"
                        })
                        seen.add(base)

            else:
                # OKX
                if self.exchange_name == "OKX":
                    spot_ex = ccxt.okx()
                    futures_ex = ccxt.okx({'options': {'defaultType': 'swap'}})
                    spot_ex.load_markets()
                    futures_ex.load_markets()
                    tickers_spot = spot_ex.fetch_tickers()
                    tickers_fut = futures_ex.fetch_tickers()

                    # Spot OKX
                    for symbol, market in spot_ex.markets.items():
                        if not market.get('active') or not market.get('spot'): continue
                        base = market.get('base')
                        if base and base not in seen and (symbol.endswith('/USDT') or symbol.endswith('/USDC')):
                            ticker = tickers_spot.get(symbol, {})
                            info = market.get('info', {})
                            contract = info.get('contractAddress') or "—"
                            network = info.get('chain') or "—"
                            spot_data.append({
                                "pair": symbol,
                                "price": float(ticker.get('last') or 0),
                                "change24h": float(ticker.get('percentage') or 0),
                                "volume": float(ticker.get('quoteVolume') or 0),
                                "contract": contract,
                                "network": network
                            })
                            seen.add(base)

                    # Futures OKX
                    for symbol, market in futures_ex.markets.items():
                        if not market.get('active'): continue
                        base = market.get('base')
                        if base and base not in seen:
                            ticker = tickers_fut.get(symbol, {})
                            rate = 0.0
                            try:
                                fr = futures_ex.fetch_funding_rate(symbol)
                                rate = float(fr.get('fundingRate') or 0) * 100
                            except:
                                pass
                            futures_data.append({
                                "token": base,
                                "price": float(ticker.get('last') or 0),
                                "funding": rate,
                                "funding_period": "8h",
                                "next_funding": next_funding_str,
                                "volume": float(ticker.get('quoteVolume') or 0),
                                "open_interest": float(ticker.get('info', {}).get('openInterest', 0) or 0),
                                "contract": "PERP",
                                "network": "—"
                            })
                            seen.add(base)

                # Binance
                else:
                    spot_ex = self.exchange
                    futures_ex = ccxt.binanceusdm()
                    spot_ex.load_markets()
                    futures_ex.load_markets()
                    tickers_spot = spot_ex.fetch_tickers()
                    tickers_fut = futures_ex.fetch_tickers()

                    for symbol, market in spot_ex.markets.items():
                        if not market.get('active') or not market.get('spot'): continue
                        base = market.get('base')
                        if base in seen or not (symbol.endswith('/USDT') or symbol.endswith('/USDC')): continue
                        ticker = tickers_spot.get(symbol, {})
                        info = market.get('info', {})
                        contract = info.get('contractAddress') or "—"
                        network = info.get('networks', {}).get('ETH', {}).get('network', 'ETH')
                        spot_data.append({
                            "pair": symbol,
                            "price": float(ticker.get('last') or 0),
                            "change24h": float(ticker.get('percentage') or 0),
                            "volume": float(ticker.get('quoteVolume') or 0),
                            "contract": contract,
                            "network": network
                        })
                        seen.add(base)

                    for symbol, market in futures_ex.markets.items():
                        if not market.get('active'): continue
                        base = market.get('base')
                        if base and base not in seen:
                            ticker = tickers_fut.get(symbol, {})
                            rate = 0.0
                            try:
                                fr = futures_ex.fetch_funding_rate(symbol)
                                rate = float(fr.get('fundingRate') or 0) * 100
                            except:
                                pass
                            futures_data.append({
                                "token": base,
                                "price": float(ticker.get('last') or 0),
                                "funding": rate,
                                "funding_period": "8h",
                                "next_funding": next_funding_str,
                                "volume": float(ticker.get('quoteVolume') or 0),
                                "open_interest": float(ticker.get('info', {}).get('openInterest', 0) or 0),
                                "contract": "PERP",
                                "network": "—"
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

    def update_tables(self, data):
        # Спот
        self.spot_table.setRowCount(0)
        for item in data.get('spot', []):
            row = self.spot_table.rowCount()
            self.spot_table.insertRow(row)
            self.spot_table.setItem(row, 0, QTableWidgetItem(item.get('pair', '')))
            self.spot_table.setItem(row, 1, QTableWidgetItem(f"{item.get('price', 0):,.4f}"))
            change = item.get('change24h', 0)
            change_item = QTableWidgetItem(f"{change:+.2f}%")
            change_item.setForeground(QColor("#00ff00") if change >= 0 else QColor("#ff0000"))
            self.spot_table.setItem(row, 2, change_item)
            self.spot_table.setItem(row, 3, QTableWidgetItem(f"{item.get('volume', 0):,.0f}"))
            self.spot_table.setItem(row, 4, QTableWidgetItem(item.get('contract', '—')))
            self.spot_table.setItem(row, 5, QTableWidgetItem(item.get('network', '—')))

        # Фьючерсы
        self.futures_table.setRowCount(0)
        for item in data.get('futures', []):
            row = self.futures_table.rowCount()
            self.futures_table.insertRow(row)
            self.futures_table.setItem(row, 0, QTableWidgetItem(item.get('token', '')))
            self.futures_table.setItem(row, 1, QTableWidgetItem(f"{item.get('price', 0):,.4f}"))
            
            rate = item.get('funding', 0)
            period = item.get('funding_period', '8h')
            funding_text = f"{rate:+.4f}% ({period})"
            funding_item = QTableWidgetItem(funding_text)
            funding_item.setForeground(QColor("#00ff00") if rate >= 0 else QColor("#ff0000"))
            self.futures_table.setItem(row, 2, funding_item)
            
            self.futures_table.setItem(row, 3, QTableWidgetItem(item.get('next_funding', '—')))
            
            self.futures_table.setItem(row, 4, QTableWidgetItem(f"{item.get('volume', 0):,.0f}"))
            self.futures_table.setItem(row, 5, QTableWidgetItem(f"{item.get('open_interest', 0):,.0f}"))
            self.futures_table.setItem(row, 6, QTableWidgetItem(item.get('contract', '—')))
            self.futures_table.setItem(row, 7, QTableWidgetItem(item.get('network', '—')))

    def load_from_file(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.update_tables(data)
            except:
                pass

    # Метод для глобального автообновления
    def refresh_data(self):
        """Лёгкое обновление только значений (вызывается из MainWindow)"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.update_tables(data)
            except:
                pass