# token_registry.py
import json
import os
from datetime import datetime

class TokenRegistry:
    def __init__(self):
        self.file = "data/token_registry.json"
        os.makedirs("data", exist_ok=True)
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"tokens": {}, "last_updated": None}

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_or_update(self, ticker: str, exchange: str, mode: str, network: str, contract: str):
        ticker = ticker.upper()
        if ticker not in self.data["tokens"]:
            self.data["tokens"][ticker] = {"exchanges": {}}

        if exchange not in self.data["tokens"][ticker]["exchanges"]:
            self.data["tokens"][ticker]["exchanges"][exchange] = {"spot": {}, "futures": {}}

        target = self.data["tokens"][ticker]["exchanges"][exchange][mode]
        if network not in target:
            target[network] = contract
        elif contract and contract != "—":
            target[network] = contract  # обновляем, если пришёл реальный адрес

        self.save()