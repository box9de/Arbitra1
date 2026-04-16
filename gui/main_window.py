# gui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton, QStatusBar
)
from PySide6.QtCore import Qt, QTimer

from gui.tabs.monitoring_tab import MonitoringTab
from gui.tabs.exchanges_tab import ExchangesTab
from gui.tabs.global_registry_tab import GlobalRegistryTab   # если вкладка есть

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arbitra — Funding & Price Arbitrage Monitor")
        self.resize(1350, 820)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Заголовок
        title = QLabel("Arbitra — Funding & Price Arbitrage Monitor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E90FF;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.addTab(MonitoringTab(), "Мониторинг")
        self.tabs.addTab(QWidget(), "Торговля")
        self.tabs.addTab(ExchangesTab(), "Биржи")
        self.tabs.addTab(QWidget(), "Тестирование")
        self.tabs.addTab(GlobalRegistryTab(), "Глобальный реестр")

        main_layout.addWidget(self.tabs)

        # === ГЛОБАЛЬНОЕ АВТООБНОВЛЕНИЕ ===
        self.auto_btn = QPushButton("Автообновление: ВЫКЛ")
        self.auto_btn.setCheckable(True)
        self.auto_btn.clicked.connect(self.toggle_auto_update)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.auto_btn)
        main_layout.addLayout(btn_layout)

        # Таймер (обновляет все биржи одновременно)
        self.global_timer = QTimer()
        self.global_timer.timeout.connect(self.refresh_all_exchanges)
        self.global_timer.setInterval(3000)  # 3 секунды

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе • Автообновление выключено")

        # Автоматически включаем при старте, если данные уже есть
        QTimer.singleShot(800, self.auto_start_if_data_exists)

    def toggle_auto_update(self):
        if self.auto_btn.isChecked():
            self.start_auto_update()
        else:
            self.stop_auto_update()

    def start_auto_update(self):
        self.global_timer.start()
        self.auto_btn.setText("Автообновление: ВКЛ (3с)")
        self.auto_btn.setStyleSheet("background-color: #00aa00; color: white; font-weight: bold;")
        self.status_bar.showMessage("Автообновление включено • Каждые 3 секунды")

    def stop_auto_update(self):
        self.global_timer.stop()
        self.auto_btn.setText("Автообновление: ВЫКЛ")
        self.auto_btn.setStyleSheet("")
        self.status_bar.showMessage("Автообновление выключено")

    def auto_start_if_data_exists(self):
        """Если данные уже загружены — включаем автообновление автоматически"""
        try:
            if hasattr(self.tabs.widget(2), 'binance_tab'):   # вкладка Биржи
                self.start_auto_update()
        except:
            pass

    def refresh_all_exchanges(self):
        """Обновляет все три биржи одновременно"""
        try:
            exchanges_tab = self.tabs.widget(2)  # вкладка "Биржи"
            exchanges_tab.binance_tab.refresh_data()
            exchanges_tab.bybit_tab.refresh_data()
            exchanges_tab.okx_tab.refresh_data()
        except:
            pass  # если вкладки ещё не готовы

    def closeEvent(self, event):
        self.stop_auto_update()
        event.accept()