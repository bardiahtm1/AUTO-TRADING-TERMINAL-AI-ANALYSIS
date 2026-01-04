class SignalInterpreter:
    @staticmethod
    def extract_signal(text: str):
        t = text.lower()

        if "strong buy" in t or "buy" in t:
            return "BUY"
        if "strong sell" in t or "sell" in t:
            return "SELL"

        return "WAIT"
