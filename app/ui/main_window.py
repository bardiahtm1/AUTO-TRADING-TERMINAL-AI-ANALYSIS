from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QComboBox, QLabel,
    QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, QTimer

from app.chart.chart_view import ChartView
from app.ai.analyzer import AIAnalyzer
from app.data.mt5_connector import MT5Connector


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bardia Terminal")
        self.resize(1200, 820)

        # ================= STATE =================
        self.auto_trade_enabled = False

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ================= TOP BAR =================
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 6, 10, 6)

        symbol_label = QLabel("Symbol:")
        self.symbol_box = QComboBox()
        self.symbol_box.addItems([
            "XAUUSD.",
            "EURUSD.",
            "GBPUSD.",
            "USDJPY."
        ])

        tf_label = QLabel("Timeframe:")
        self.tf_box = QComboBox()
        self.tf_box.addItems([
            "M1",
            "M5",
            "M15",
            "H1"
        ])

        self.auto_btn = QPushButton("Auto Scroll ON")
        self.auto_btn.setCheckable(True)
        self.auto_btn.setChecked(True)

        top_bar.addWidget(symbol_label)
        top_bar.addWidget(self.symbol_box)
        top_bar.addSpacing(20)
        top_bar.addWidget(tf_label)
        top_bar.addWidget(self.tf_box)
        top_bar.addSpacing(20)
        top_bar.addWidget(self.auto_btn)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # ================= CHART =================
        self.chart = ChartView()
        layout.addWidget(self.chart, stretch=1)

        # ================= TRADE PANEL =================
        trade_bar = QHBoxLayout()
        trade_bar.setContentsMargins(10, 8, 10, 8)
        trade_bar.setSpacing(12)

        self.sell_btn = QPushButton("SELL")
        self.buy_btn = QPushButton("BUY")

        self.run_auto_btn = QPushButton("AUTO TRADE OFF")
        self.run_auto_btn.setCheckable(True)
        self.run_auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                font-weight: bold;
                padding: 10px 26px;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #2E7D32;
            }
        """)

        trade_bar.addStretch()
        trade_bar.addWidget(self.sell_btn)
        trade_bar.addWidget(self.buy_btn)
        trade_bar.addSpacing(20)
        trade_bar.addWidget(self.run_auto_btn)
        trade_bar.addStretch()

        layout.addLayout(trade_bar)

        # ================= AI PANEL =================
        self.ai_panel = QTextEdit()
        self.ai_panel.setReadOnly(True)
        self.ai_panel.setFixedHeight(160)
        self.ai_panel.setPlaceholderText(
            "AI Market Analysis will appear here..."
        )

        self.ai_panel.setStyleSheet("""
            QTextEdit {
                background-color: #0E1621;
                color: #D1D4DC;
                border: none;
                padding: 10px;
                font-family: Segoe UI;
                font-size: 12px;
            }
        """)

        layout.addWidget(self.ai_panel)

        # ================= BOTTOM BAR =================
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(10, 6, 10, 6)
        bottom_bar.setSpacing(20)

        self.account_label = QLabel("Account: --")
        self.balance_label = QLabel("Balance: --")
        self.equity_label = QLabel("Equity: --")
        self.margin_label = QLabel("Margin: --")

        for lbl in (
            self.account_label,
            self.balance_label,
            self.equity_label,
            self.margin_label
        ):
            lbl.setStyleSheet("""
                color: #D1D4DC;
                font-size: 11px;
                font-family: Segoe UI;
            """)

        bottom_bar.addWidget(self.account_label)
        bottom_bar.addWidget(self.balance_label)
        bottom_bar.addWidget(self.equity_label)
        bottom_bar.addWidget(self.margin_label)
        bottom_bar.addStretch()

        layout.addLayout(bottom_bar)

        # ================= MT5 =================
        self.mt5 = MT5Connector(
            self.symbol_box.currentText(),
            self.tf_box.currentText(),
            1
        )

        # ================= AI =================
        self.ai = AIAnalyzer()

        self.ai_timer = QTimer()
        self.ai_timer.setSingleShot(True)
        self.ai_timer.timeout.connect(self.run_ai_analysis)

        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        self.account_timer.start(2000)

        # ================= AUTO TRADE TIMER =================
        self.trade_timer = QTimer()
        self.trade_timer.timeout.connect(self.auto_trade_tick)
        self.trade_timer.start(200)  # every tick interval

        # ================= SIGNALS =================
        self.symbol_box.currentTextChanged.connect(self.on_market_change)
        self.tf_box.currentTextChanged.connect(self.on_market_change)
        self.auto_btn.toggled.connect(self.toggle_auto)
        self.buy_btn.clicked.connect(lambda: self.send_order("BUY"))
        self.sell_btn.clicked.connect(lambda: self.send_order("SELL"))
        self.run_auto_btn.toggled.connect(self.toggle_auto_trade)

        self.ai_timer.start(800)

    # ==================================================

    def toggle_auto(self, checked):
        self.auto_btn.setText(
            "Auto Scroll ON" if checked else "Auto Scroll OFF"
        )
        self.chart.set_auto_scroll(checked)

    def toggle_auto_trade(self, checked):
        self.auto_trade_enabled = checked
        self.run_auto_btn.setText(
            "AUTO TRADE ON" if checked else "AUTO TRADE OFF"
        )
        self.ai_panel.append(
            "Auto trading ENABLED" if checked else "Auto trading DISABLED"
        )

    # ==================================================

    def on_market_change(self):
        self.chart.set_symbol(self.symbol_box.currentText())
        self.chart.set_timeframe(self.tf_box.currentText())
        self.ai_panel.setText("Analyzing market...")
        self.ai_timer.start(800)

    # ==================================================

    def auto_trade_tick(self):
        if not self.auto_trade_enabled:
            return

        if not hasattr(self.chart, "candles") or not self.chart.candles:
            return

        if self.mt5.has_open_position(self.symbol_box.currentText()):
            return

        ema_values = self.chart.calculate_ema(self.chart.EMA_PERIOD)
        ema = ema_values[-1]
        last_close = self.chart.candles[-1]["close"]

        tick = self.mt5.get_tick()
        if not tick:
            return

        bid = tick.bid
        ask = tick.ask
        symbol = self.symbol_box.currentText()
        lot = 0.10
        delta = 5

        # CASE 1: EMA ABOVE PRICE → BUY
        if ema > last_close and ask >= ema:
            self.mt5.buy_with_sl_tp(
                symbol, lot,
                ask,
                ask + delta,
                ask - delta
            )
            self.ai_panel.append("AUTO BUY executed")
            return

        # CASE 2: EMA BELOW PRICE → SELL
        if ema < last_close and bid <= ema:
            self.mt5.sell_with_sl_tp(
                symbol, lot,
                bid,
                bid - delta,
                bid + delta
            )
            self.ai_panel.append("AUTO SELL executed")
            return

    # ==================================================

    def run_ai_analysis(self):
        candles = getattr(self.chart, "candles", [])

        if not candles:
            self.ai_panel.setText("No candle data available for AI analysis.")
            return

        try:
            text = self.ai.analyze(
                self.symbol_box.currentText(),
                self.tf_box.currentText(),
                candles
            )
            self.ai_panel.setText(text)
        except Exception as e:
            self.ai_panel.setText(f"AI Error: {e}")

    # ==================================================

    def update_account_info(self):
        info = self.mt5.get_account_info()
        if not info:
            return

        self.account_label.setText(f"Account: {info.login}")
        self.balance_label.setText(f"Balance: {info.balance:.2f}")
        self.equity_label.setText(f"Equity: {info.equity:.2f}")
        self.margin_label.setText(f"Margin: {info.margin:.2f}")

    # ==================================================

    def send_order(self, side):
        lot = 0.10
        symbol = self.symbol_box.currentText()

        try:
            if side == "BUY":
                result = self.mt5.buy(symbol, lot)
            else:
                result = self.mt5.sell(symbol, lot)

            if result:
                self.ai_panel.append(f"{side} order executed.")
            else:
                self.ai_panel.append(f"{side} order failed.")

        except Exception as e:
            self.ai_panel.append(f"Trade error: {e}")
