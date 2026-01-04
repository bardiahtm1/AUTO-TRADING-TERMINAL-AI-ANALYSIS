from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsPathItem
)
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPoint, QTimer
from datetime import datetime

from app.data.mt5_connector import MT5Connector
from app.core import config


class ChartView(QGraphicsView):
    VIEW_HEIGHT = 600
    PRICE_SCALE_WIDTH = 90
    TIME_SCALE_HEIGHT = 24
    PAD_TOP = 20
    PAD_BOTTOM = 20
    PRICE_STEPS = 10

    EMA_PERIOD = 20
    SMA_PERIOD = 50

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("#131722"))

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

        self.dragging = False
        self.last_mouse = QPoint()
        self.candle_shift = 0
        self.auto_scroll = True

        self.symbol = "XAUUSD."
        self.timeframe = "M1"
        self.bars = 120

        self.mt5 = MT5Connector(self.symbol, self.timeframe, self.bars)

        self.crosshair_pos = None
        self.live_price = None

        # ===== ADDED (SAFE) =====
        self.bid_price = None
        self.ask_price = None
        # ========================

        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_chart)
        self.chart_timer.start(600)

        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.update_tick)
        self.tick_timer.start(200)

        self.update_chart()

    # =====================================================
    # PUBLIC API

    def set_symbol(self, symbol):
        self.symbol = symbol
        self.mt5 = MT5Connector(self.symbol, self.timeframe, self.bars)
        self.candle_shift = 0
        self.auto_scroll = True
        self.update_chart()

    def set_timeframe(self, timeframe):
        self.timeframe = timeframe
        self.mt5 = MT5Connector(self.symbol, self.timeframe, self.bars)
        self.candle_shift = 0
        self.auto_scroll = True
        self.update_chart()

    def set_auto_scroll(self, enabled):
        self.auto_scroll = enabled

    # =====================================================
    # DATA

    def update_chart(self):
        if self.auto_scroll:
            self.candle_shift = 0

        self.candles = self.mt5.get_live_candles(self.candle_shift)
        if not self.candles:
            return

        prices = []
        for c in self.candles:
            prices.extend([c["high"], c["low"]])

        if self.live_price:
            prices.append(self.live_price)

        self.max_p = max(prices)
        self.min_p = min(prices)

        rng = max(self.max_p - self.min_p, 0.00001)
        usable = self.VIEW_HEIGHT - self.PAD_TOP - self.PAD_BOTTOM
        self.scale_y = usable / rng

        self.draw()

    def update_tick(self):
        tick = self.mt5.get_tick()
        if tick:
            self.live_price = tick.bid
            self.bid_price = tick.bid
            self.ask_price = tick.ask
            self.draw()

    # =====================================================
    # COORDS

    def price_to_y(self, price):
        return self.PAD_TOP + (self.max_p - price) * self.scale_y

    def y_to_price(self, y):
        return self.max_p - (y - self.PAD_TOP) / self.scale_y

    # =====================================================
    # INDICATORS

    def calculate_sma(self, period):
        closes = [c["close"] for c in self.candles]
        sma = []
        for i in range(len(closes)):
            if i + 1 < period:
                sma.append(None)
            else:
                sma.append(sum(closes[i + 1 - period:i + 1]) / period)
        return sma

    def calculate_ema(self, period):
        closes = [c["close"] for c in self.candles]
        ema = []
        k = 2 / (period + 1)

        for i, price in enumerate(closes):
            if i == 0:
                ema.append(price)
            else:
                ema.append(price * k + ema[-1] * (1 - k))
        return ema

    # =====================================================
    # DRAW

    def draw(self):
        self.scene.clear()

        x = 0
        step = config.CANDLE_WIDTH + config.CANDLE_GAP

        for c in self.candles:
            o, h, l, cl = c["open"], c["high"], c["low"], c["close"]

            oy = self.price_to_y(o)
            cy = self.price_to_y(cl)
            hy = self.price_to_y(h)
            ly = self.price_to_y(l)

            color = QColor("#26A69A") if cl >= o else QColor("#EF5350")

            self.scene.addLine(
                x + config.CANDLE_WIDTH / 2, hy,
                x + config.CANDLE_WIDTH / 2, ly,
                QPen(QColor("#B0BEC5"))
            )

            self.scene.addRect(
                QRectF(
                    x,
                    min(oy, cy),
                    config.CANDLE_WIDTH,
                    max(abs(oy - cy), 1)
                ),
                Qt.NoPen,
                QBrush(color)
            )

            x += step

        self.draw_indicators()

        # ===== ADDED =====
        if self.bid_price is not None and self.ask_price is not None:
            self.draw_bid_ask_lines(x)
        # =================

        self.draw_price_axis(x)
        self.draw_time_axis(x)

        if self.live_price:
            self.draw_live_price_marker(x)

        if self.crosshair_pos:
            self.draw_crosshair(x)

        self.scene.setSceneRect(
            0, 0,
            x + self.PRICE_SCALE_WIDTH,
            self.VIEW_HEIGHT + self.TIME_SCALE_HEIGHT
        )

    # =====================================================
    # INDICATOR DRAWING

    def draw_indicators(self):
        ema = self.calculate_ema(self.EMA_PERIOD)
        sma = self.calculate_sma(self.SMA_PERIOD)

        self.draw_line_indicator(ema, QColor("#FFD54F"))
        self.draw_line_indicator(sma, QColor("#42A5F5"))

    def draw_line_indicator(self, values, color):
        path = QPainterPath()
        step = config.CANDLE_WIDTH + config.CANDLE_GAP

        started = False
        for i, val in enumerate(values):
            if val is None:
                continue

            x = i * step + config.CANDLE_WIDTH / 2
            y = self.price_to_y(val)

            if not started:
                path.moveTo(x, y)
                started = True
            else:
                path.lineTo(x, y)

        item = QGraphicsPathItem(path)
        pen = QPen(color, 1.6)
        pen.setCosmetic(True)
        item.setPen(pen)
        self.scene.addItem(item)

    # =====================================================
    # BID / ASK (ADDED)

    def draw_bid_ask_lines(self, chart_width):
        bid_y = self.price_to_y(self.bid_price)
        ask_y = self.price_to_y(self.ask_price)

        self.scene.addLine(
            0, bid_y, chart_width, bid_y,
            QPen(QColor("#42A5F5"), 1)
        )
        self.scene.addLine(
            0, ask_y, chart_width, ask_y,
            QPen(QColor("#EF5350"), 1)
        )

    # =====================================================
    # AXES / LIVE / CROSSHAIR

    def draw_price_axis(self, chart_width):
        panel = QGraphicsRectItem(
            QRectF(chart_width, 0, self.PRICE_SCALE_WIDTH, self.VIEW_HEIGHT)
        )
        panel.setBrush(QBrush(QColor("#0E1621")))
        panel.setPen(Qt.NoPen)
        self.scene.addItem(panel)

        step = (self.max_p - self.min_p) / self.PRICE_STEPS

        for i in range(self.PRICE_STEPS + 1):
            price = self.min_p + i * step
            y = self.price_to_y(price)

            txt = QGraphicsTextItem(f"{price:.2f}")
            txt.setFont(QFont("Segoe UI", 8))
            txt.setDefaultTextColor(QColor("#D1D4DC"))
            txt.setPos(
                chart_width + self.PRICE_SCALE_WIDTH - txt.boundingRect().width() - 6,
                y - 8
            )
            self.scene.addItem(txt)

    def draw_time_axis(self, chart_width):
        base = QGraphicsRectItem(
            QRectF(0, self.VIEW_HEIGHT, chart_width, self.TIME_SCALE_HEIGHT)
        )
        base.setBrush(QBrush(QColor("#0E1621")))
        base.setPen(Qt.NoPen)
        self.scene.addItem(base)

        count = len(self.candles)
        if count == 0:
            return

        step = max(1, count // 6)

        for i in range(0, count, step):
            ts = self.candles[i]["time"]
            t = datetime.fromtimestamp(ts).strftime("%H:%M")

            x = i * (config.CANDLE_WIDTH + config.CANDLE_GAP)

            txt = QGraphicsTextItem(t)
            txt.setFont(QFont("Segoe UI", 8))
            txt.setDefaultTextColor(QColor("#D1D4DC"))
            txt.setPos(x - 18, self.VIEW_HEIGHT + 4)
            self.scene.addItem(txt)

    def draw_live_price_marker(self, chart_width):
        y = self.price_to_y(self.live_price)

        rect = QGraphicsRectItem(
            QRectF(chart_width, y - 11, self.PRICE_SCALE_WIDTH, 22)
        )
        rect.setBrush(QBrush(QColor("#E53935")))
        rect.setPen(Qt.NoPen)
        self.scene.addItem(rect)

        txt = QGraphicsTextItem(f"{self.live_price:.2f}")
        txt.setFont(QFont("Segoe UI", 9, QFont.Bold))
        txt.setDefaultTextColor(Qt.white)
        txt.setPos(
            chart_width + self.PRICE_SCALE_WIDTH - txt.boundingRect().width() - 6,
            y - 9
        )
        self.scene.addItem(txt)

    def draw_crosshair(self, chart_width):
        pen = QPen(QColor("#787B86"))
        pen.setStyle(Qt.DashLine)

        x = self.crosshair_pos.x()
        y = self.crosshair_pos.y()

        self.scene.addLine(x, 0, x, self.VIEW_HEIGHT, pen)
        self.scene.addLine(0, y, chart_width, y, pen)

    # =====================================================
    # MOUSE

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.auto_scroll = False
            self.last_mouse = e.pos()

    def mouseMoveEvent(self, e):
        if self.dragging:
            dx = e.pos().x() - self.last_mouse.x()
            self.last_mouse = e.pos()

            bars = dx // (config.CANDLE_WIDTH + config.CANDLE_GAP)
            if bars:
                self.candle_shift = max(0, self.candle_shift - bars)
                self.update_chart()
        else:
            self.crosshair_pos = e.pos()
            self.draw()

    def mouseReleaseEvent(self, e):
        self.dragging = False
