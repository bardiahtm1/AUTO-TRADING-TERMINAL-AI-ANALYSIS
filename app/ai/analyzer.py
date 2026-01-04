import os
import requests
from dotenv import load_dotenv

load_dotenv()


class AIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not found in .env file"
            )

        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-4o-mini"

    # ===============================
    # INDICATORS
    # ===============================

    def sma(self, values, period):
        if len(values) < period:
            return None
        return sum(values[-period:]) / period

    def ema(self, values, period):
        if len(values) < period:
            return None

        k = 2 / (period + 1)
        ema_val = values[0]

        for price in values[1:]:
            ema_val = price * k + ema_val * (1 - k)

        return ema_val

    # ===============================
    # AI ANALYSIS
    # ===============================

    def analyze(self, symbol: str, timeframe: str, candles: list) -> str:
        if not candles:
            return "AI Analyzer: No candle data available."

        closes = [c["close"] for c in candles]

        sma_20 = self.sma(closes, 20)
        ema_20 = self.ema(closes[-50:], 20)

        last_price = closes[-1]

        indicator_text = "Indicators:\n"
        indicator_text += f"Last Price: {last_price:.2f}\n"

        if sma_20:
            indicator_text += f"SMA(20): {sma_20:.2f}\n"
        else:
            indicator_text += "SMA(20): Not enough data\n"

        if ema_20:
            indicator_text += f"EMA(20): {ema_20:.2f}\n"
        else:
            indicator_text += "EMA(20): Not enough data\n"

        recent = candles[-40:]

        candle_text = "\n".join(
            f"O:{c['open']} H:{c['high']} L:{c['low']} C:{c['close']}"
            for c in recent
        )

        prompt = (
            "You are a professional technical trading analyst.\n\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {timeframe}\n\n"
            f"{indicator_text}\n"
            "Recent candles:\n"
            f"{candle_text}\n\n"
            "Analyze trend, momentum, and bias.\n"
            "State if price is above or below SMA/EMA.\n"
            "Give a short professional analysis.\n"
            "No disclaimers. No emojis."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Bardia Terminal"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.25
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=15
            )

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            return (
                "AI Analyzer Error\n"
                "----------------------\n"
                f"{str(e)}"
            )
