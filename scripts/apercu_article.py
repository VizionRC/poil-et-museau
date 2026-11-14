"""Crée un aperçu HTML autonome (un seul fichier) d'un article tel qu'il sera publié.

Usage :
    python3 build.py --apercu
    python3 scripts/apercu_article.py <slug-francais> [--en] [sortie.html]

- Lit la page générée dans dist/ (articles programmés et brouillons inclus avec --apercu).
- Intègre polices, images (taille 1080 si elle existe) et script du site dans le fichier,
  pour qu'on puisse l'ouvrir ou l'envoyer tel quel et voir exactement le rendu.
- --en : aperçu de la version anglaise (trouvée grâce à traduction_de).
Sortie par défaut : apercu-<slug>.html (ou apercu-<slug-anglais>.html) dans le dossier courant.
"""
import base64
import mimetypes
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(HERE, "dist")


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or ("font/woff2" if path.endswith(".woff2") else "application/octet-stream")
    if path.endswith(".webp"):
        mime = "image/webp"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def resolve(page_dir, ref):
    ref = ref.split("?")[0].split("#")[0]
    if ref.startswith("https://poiletmuseau.com/"):
        ref = ref[len("https://poiletmuseau.com/"):]
        p = os.path.join(DIST, ref)
    elif ref.startswith("/"):
        p = os.path.join(DIST, ref.lstrip("/"))
    else:
        p = os.path.normpath(os.path.join(page_dir, ref))
    return p if os.path.isfile(p) else None


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    en = "--en" in args
    args = [a for a in args if a != "--en"]
    slug = args[0]
    if en:
        en_dir = os.path.join(HERE, "content", "en", "articles")
        found = [f[:-5] for f in os.listdir(en_dir)
                 if re.search(rf"^traduction_de:\s*{re.escape(slug)}\s*$", open(os.path.join(en_dir, f), encoding="utf-8").read(), re.M)]
        if not found:
            sys.exit(f"Aucune version anglaise trouvée pour {slug}")
        page = os.path.join(DIST, "en", "articles", found[0] + ".html")
        name = found[0]
    else:
        page = os.path.join(DIST, "articles", slug + ".html")
        name = slug
    if not os.path.isfile(page):
        sys.exit(f"Page introuvable : {page} (lancez d'abord python3 build.py --apercu)")
    out = args[1] if len(args) > 1 else f"apercu-{name}.html"
    page_dir = os.path.dirname(page)
    s = open(page, encoding="utf-8").read()

    # Pas de statistiques dans un aperçu
    s = re.sub(r'<script[^>]*googletagmanager[^>]*></script>', "", s)
    s = re.sub(r"<script>(?:(?!</script>).)*gtag\((?:(?!</script>).)*</script>", "", s, flags=re.S)

    # Script du site intégré
    def js(m):
        p = resolve(page_dir, m.group(1))
        return f"<script>{open(p, encoding='utf-8').read()}</script>" if p else ""
    s = re.sub(r'<script[^>]*\bsrc="([^"]+)"[^>]*></script>', js, s)

    # Polices et images de fond dans le CSS
    def css_url(m):
        p = resolve(page_dir, m.group(2))
        return f"url({data_uri(p)})" if p else m.group(0)
    s = re.sub(r"""url\((['"]?)(?!data:)([^)'"]+)\1\)""", css_url, s)

    # Images : version 1080 si disponible, sans srcset ni chargement différé
    s = re.sub(r'\s(srcset|sizes)="[^"]*"', "", s)
    s = s.replace(' loading="lazy"', "")

    def img(m):
        ref = m.group(1)
        p = resolve(page_dir, ref)
        big = resolve(page_dir, re.sub(r"images/articles/(?:480/|720/)?", "images/articles/1080/", ref)) if "images/articles/" in ref else None
        p = big or p
        return f'src="{data_uri(p)}"' if p else m.group(0)
    s = re.sub(r'src="([^"]+\.(?:webp|png|jpe?g|svg|gif))"', img, s)

    # Préchargements et liens vers des fichiers locaux devenus inutiles
    s = re.sub(r'<link rel="preload"[^>]*>', "", s)
    s = re.sub(r'<link rel="(?:icon|apple-touch-icon)"[^>]*>', "", s)

    # Statistiques désactivées dans l'aperçu (aucun envoi à Google Analytics)
    s = s.replace("https://www.googletagmanager.com/gtag/js", "about:blank")

    open(out, "w", encoding="utf-8").write(s)
    print(f"{out}  ({os.path.getsize(out) // 1024} Ko)")


if __name__ == "__main__":
    main()
