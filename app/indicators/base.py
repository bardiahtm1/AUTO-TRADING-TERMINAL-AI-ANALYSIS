class IndicatorBase:
    def __init__(self, period):
        self.period = period

    def calculate(self, candles):
        """
        candles: list of candle dicts
        must return list same length as candles
        """
        raise NotImplementedError
