# gui/tabs/global_registry_tab.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PySide6.QtCore import Qt
import json
import os

class GlobalRegistryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Глобальный реестр токенов и контрактов")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Токен", "Биржа", "Режим", "Сеть", "Адрес контракта", "Ресурс"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        path = "data/token_registry.json"
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        row = 0
        for ticker, info in data.get("tokens", {}).items():
            for exchange, modes in info.get("exchanges", {}).items():
                for mode, networks in modes.items():
                    for network, contract in networks.items():
                        if not contract or contract == "—":
                            continue
                        self.table.insertRow(row)
                        self.table.setItem(row, 0, QTableWidgetItem(ticker))
                        self.table.setItem(row, 1, QTableWidgetItem(exchange))
                        self.table.setItem(row, 2, QTableWidgetItem(mode.capitalize()))
                        self.table.setItem(row, 3, QTableWidgetItem(network))
                        self.table.setItem(row, 4, QTableWidgetItem(contract))
                        self.table.setItem(row, 5, QTableWidgetItem("API биржи"))
                        row += 1