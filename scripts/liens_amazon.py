"""Résout les liens courts Amazon (amzn.to, link.amazon) des articles et note le produit (ASIN) de chacun.

Lancé par .github/workflows/liens-amazon.yml. Écrit data/liens-amazon.json :
    {"https://amzn.to/xxxx": {"asin": "B0...", "final": "https://www.amazon.ca/dp/B0...?..."}, ...}
build.py s'en sert pour réécrire chaque lien vers https://www.amazon.ca/dp/<ASIN>?tag=<AMAZON_TAG>.
Les liens déjà résolus sont conservés ; seuls les nouveaux sont interrogés.
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "liens-amazon.json")
SHORT = re.compile(r'https://(?:amzn\.to|link\.amazon)/[A-Za-z0-9]+')
ASIN = re.compile(r'/(?:dp|gp/product|gp/aw/d|product)/([A-Z0-9]{10})(?:[/?]|$)')
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


opener = urllib.request.build_opener(NoRedirect)


def suivre(url, n=6):
    """Suit les redirections une à une (sans charger la page Amazon finale)."""
    for _ in range(n):
        if "amazon." in url and ASIN.search(url):
            return url
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
        try:
            r = opener.open(req, timeout=20)
            body = r.read(200000).decode("utf-8", "ignore")
            m = re.search(r'(https://www\.amazon\.[a-z.]+/[^"\'<>\s]*?/(?:dp|gp/product)/[A-Z0-9]{10}[^"\'<>\s]*)', body)
            return m.group(1) if m else url
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location")
            if e.code in (301, 302, 303, 307, 308) and loc:
                url = urllib.parse.urljoin(url, loc)
                continue
            return url
    return url


def main():
    liens = set()
    for root, _, files in os.walk(os.path.join(HERE, "content")):
        for f in files:
            if f.endswith(".html"):
                liens |= set(SHORT.findall(open(os.path.join(root, f), encoding="utf-8").read()))
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    ok = ko = 0
    for u in sorted(liens):
        if data.get(u, {}).get("asin"):
            ok += 1
            continue
        final = suivre(u)
        m = ASIN.search(final)
        data[u] = {"asin": m.group(1) if m else None, "final": final}
        if m:
            ok += 1
        else:
            ko += 1
            print("Non résolu :", u, "->", final)
        time.sleep(1.5)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(dict(sorted(data.items())), open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"{ok} liens résolus, {ko} non résolus, sur {len(liens)} liens courts.")


if __name__ == "__main__":
    main()
