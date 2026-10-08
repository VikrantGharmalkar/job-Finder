"""Polite HTTP fetcher: robots.txt, rate limit, retries, identifiable User-Agent."""
import time, requests, urllib.robotparser as rp
from urllib.parse import urlparse

UA = "GradGuideJobsBot/1.0 (student hiring-assignment project)"

class Fetcher:
    def __init__(self, delay=2.0, retries=3):
        self.delay, self.retries, self._last = delay, retries, 0.0
        self.s = requests.Session(); self.s.headers.update({"User-Agent": UA, "Accept-Language": "en"})
        self._robots = {}

    def allowed(self, url):
        p = urlparse(url); base = f"{p.scheme}://{p.netloc}"
        if base not in self._robots:
            r = rp.RobotFileParser(base + "/robots.txt")
            try: r.read()
            except Exception: r = None          # robots unreachable -> treat as allowed
            self._robots[base] = r
        r = self._robots[base]
        return True if r is None else r.can_fetch(UA, url)

    def get(self, url):
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        for attempt in range(self.retries):
            wait = self.delay - (time.time() - self._last)
            if wait > 0: time.sleep(wait)
            self._last = time.time()
            try:
                r = self.s.get(url, timeout=20); r.raise_for_status(); return r.text
            except requests.RequestException:
                if attempt == self.retries - 1: raise
                time.sleep(2 ** attempt)
