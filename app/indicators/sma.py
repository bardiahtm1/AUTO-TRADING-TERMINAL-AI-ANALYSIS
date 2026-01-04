from .base import IndicatorBase


class SMA(IndicatorBase):
    def calculate(self, candles):
        closes = [c["close"] for c in candles]
        values = []

        for i in range(len(closes)):
            if i + 1 < self.period:
                values.append(None)
            else:
                window = closes[i + 1 - self.period : i + 1]
                values.append(sum(window) / self.period)

        return values
