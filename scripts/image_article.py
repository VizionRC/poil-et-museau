"""Prépare une photo d'article pour le site : WebP optimisé + tailles 480, 720 et 1080 px.

Usage :
    python3 scripts/image_article.py <photo source> <nom-de-fichier-descriptif>
Exemple :
    python3 scripts/image_article.py ~/Téléchargements/photo.png chat-griffoir-salon
Crée images/articles/<nom>.webp (1600 px de large au maximum) et les tailles réduites.
Le chemin à mettre dans l'article est affiché à la fin (champ « image » ou balise <img>).
"""
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, nom = sys.argv[1], sys.argv[2]
    nom = re.sub(r"[^a-z0-9-]+", "-", nom.lower()).strip("-")
    im = Image.open(src).convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    base = os.path.join(HERE, "images", "articles")
    im.save(os.path.join(base, nom + ".webp"), "WEBP", quality=82, method=6)
    for w in (480, 720, 1080):
        if w < im.width:
            d = os.path.join(base, str(w))
            os.makedirs(d, exist_ok=True)
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(os.path.join(d, nom + ".webp"), "WEBP", quality=80, method=6)
    print(f"/images/articles/{nom}.webp  ({im.width}×{im.height})")


if __name__ == "__main__":
    main()
