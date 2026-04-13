# token_map.py — Сопоставление токенов для Arbitra

TOKEN_MAP = {
    "BTC": {
        "tickers": {
            "Binance": "BTC/USDT:USDT",
            "OKX": "BTC/USDT:USDT",
            "Bybit": "BTC/USDT:USDT"
        }
    },
    "ETH": {
        "tickers": {
            "Binance": "ETH/USDT:USDT",
            "OKX": "ETH/USDT:USDT",
            "Bybit": "ETH/USDT:USDT"
        }
    }
}

def get_ticker(token_name: str, exchange: str) -> str:
    """Возвращает правильный тикер для токена на указанной бирже"""
    if token_name in TOKEN_MAP:
        return TOKEN_MAP[token_name]["tickers"].get(exchange)
    return None

def get_all_tokens():
    return list(TOKEN_MAP.keys())

# Тест при запуске файла
if __name__ == "__main__":
    print("=== Token Map загружен ===")
    print("Токены:", get_all_tokens())