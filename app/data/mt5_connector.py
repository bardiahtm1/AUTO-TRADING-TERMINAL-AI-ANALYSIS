import MetaTrader5 as mt5
from datetime import datetime
import time


class MT5Connector:
    def __init__(self, symbol, timeframe, bars):
        if not mt5.initialize():
            raise RuntimeError("MT5 initialize failed")

        self.symbol = symbol
        self.timeframe = timeframe
        self.bars = bars

        mt5.symbol_select(self.symbol, True)

    # ================= DATA =================

    def get_live_candles(self, shift=0):
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1
        }

        rates = mt5.copy_rates_from_pos(
            self.symbol,
            tf_map[self.timeframe],
            shift,
            self.bars
        )

        if rates is None:
            return []

        candles = []
        for r in rates:
            candles.append({
                "time": r["time"],
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"]
            })

        return candles

    def get_tick(self):
        return mt5.symbol_info_tick(self.symbol)

    # ================= ACCOUNT =================

    def get_account_info(self):
        return mt5.account_info()

    # ================= POSITIONS =================

    def has_open_position(self, symbol):
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return False
        return len(positions) > 0

    # ================= TRADING =================

    def buy(self, symbol, lot):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False
        return self._send_order(
            symbol, lot,
            mt5.ORDER_TYPE_BUY,
            tick.ask
        )

    def sell(self, symbol, lot):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False
        return self._send_order(
            symbol, lot,
            mt5.ORDER_TYPE_SELL,
            tick.bid
        )

    def buy_with_sl_tp(self, symbol, lot, price, tp, sl):
        return self._send_order(
            symbol, lot,
            mt5.ORDER_TYPE_BUY,
            price,
            tp=tp,
            sl=sl
        )

    def sell_with_sl_tp(self, symbol, lot, price, tp, sl):
        return self._send_order(
            symbol, lot,
            mt5.ORDER_TYPE_SELL,
            price,
            tp=tp,
            sl=sl
        )

    # ================= CORE SEND =================

    def _send_order(self, symbol, lot, order_type, price, tp=None, sl=None):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 26001,
            "comment": "BardiaTerminal",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if tp is not None:
            request["tp"] = tp
        if sl is not None:
            request["sl"] = sl

        result = mt5.order_send(request)

        if result is None:
            print("MT5 returned None")
            return False

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("Order failed:", result)
            return False

        return True
