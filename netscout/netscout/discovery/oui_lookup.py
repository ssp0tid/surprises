import csv
from pathlib import Path
from typing import Optional

from netscout.utils.errors import NetworkError


class OUILookup:
    OUI_URL = "https://standards-oui.ieee.org/oui.txt"
    CACHE_FILE = "oui_database.txt"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".netscout"
        self.cache_file = self.cache_dir / self.CACHE_FILE
        self._cache: dict[str, str] = {}

    def load(self) -> None:
        if not self.cache_file.exists():
            self.download()

        self._cache = {}
        with open(self.cache_file, "r", encoding="utf-8") as f:
            for line in f:
                if "(hex)" in line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        oui = parts[0].strip().replace("-", ":").upper()[:8]
                        vendor = parts[-1].strip()
                        self._cache[oui] = vendor

    def lookup(self, mac: str) -> Optional[str]:
        mac = mac.upper().replace("-", ":")
        prefix = mac[:8]
        return self._cache.get(prefix)

    def download(self) -> None:
        import urllib.request

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(self.OUI_URL, self.cache_file)
        except Exception as e:
            raise NetworkError(f"Failed to download OUI database: {e}")
