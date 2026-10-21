#!/usr/bin/env python3
"""Rapatrie dans le dépôt toutes les images encore hébergées chez Shopify.

À exécuter AVANT de fermer la boutique Shopify : ensuite, ces images disparaissent.
Le plus simple : onglet « Actions » du dépôt GitHub > « Rapatrier les images Shopify » > « Run workflow ».
En local :  python3 scripts/rapatrier_images.py

Pour chaque adresse cdn.shopify.com trouvée dans content/ :
  1. télécharge l'image (en pleine résolution si possible) dans images/articles/ ;
  2. remplace l'adresse par /images/articles/<fichier> dans le contenu.
Le script peut être relancé sans risque : il ne retélécharge pas une image déjà présente."""
import os, re, sys, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(HERE, "content")
DEST = os.path.join(HERE, "images", "articles")
URL_RE = re.compile(r"https://cdn\.shopify\.com/[^\s\"'<>)]+")
SIZE_RE = re.compile(r"_(\d+x\d*|\d*x\d+)(?=\.\w+$)")   # ex. photo_480x480.webp


def local_name(url):
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path)
    return SIZE_RE.sub("", name)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rapatriement Poil & Museau)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download(url, target):
    """Essaie d'abord la version pleine résolution, puis l'adresse exacte."""
    base = url.split("?")[0]
    candidates = []
    if SIZE_RE.search(os.path.basename(urllib.parse.urlparse(base).path)):
        candidates.append(SIZE_RE.sub("", base))
    candidates += [base, url]
    for c in candidates:
        try:
            data = fetch(c)
            if len(data) > 200:
                open(target, "wb").write(data)
                return True
        except Exception:
            continue
    return False


def main():
    os.makedirs(DEST, exist_ok=True)
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(CONTENT) for f in fs if f.endswith(".html")]
    done, failed, changed = {}, [], 0
    for path in sorted(files):
        txt = open(path, encoding="utf-8").read()
        urls = sorted(set(u.rstrip(".,;") for u in URL_RE.findall(txt)), key=len, reverse=True)
        if not urls:
            continue
        new = txt
        for u in urls:
            clean = u.replace("&amp;", "&")
            name = local_name(clean)
            # Les images de couverture servent de vignettes : on évite les doublons de nom
            target = os.path.join(DEST, name)
            if name not in done:
                ok = os.path.exists(target) or download(clean, target)
                done[name] = ok
                print(("✓ " if ok else "✗ ") + name)
            if done[name]:
                new = new.replace(u, "/images/articles/" + name)
            else:
                failed.append((os.path.relpath(path, HERE), u))
        if new != txt:
            open(path, "w", encoding="utf-8").write(new)
            changed += 1
    print(f"\n{sum(done.values())} image(s) rapatriée(s), {changed} fichier(s) de contenu mis à jour.")
    if failed:
        print(f"{len(failed)} image(s) introuvable(s) :")
        for f, u in failed:
            print("  ", f, u)
        sys.exit(1)


if __name__ == "__main__":
    main()
