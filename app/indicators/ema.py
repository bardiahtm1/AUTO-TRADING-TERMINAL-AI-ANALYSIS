from .base import IndicatorBase


class EMA(IndicatorBase):
    def calculate(self, candles):
        closes = [c["close"] for c in candles]
        values = []

        k = 2 / (self.period + 1)

        for i, price in enumerate(closes):
            if i == 0:
                values.append(price)
            else:
                values.append(price * k + values[-1] * (1 - k))

        return values
