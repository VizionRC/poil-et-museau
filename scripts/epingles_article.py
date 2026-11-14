"""Crée les 3 épingles Pinterest (1000 × 1500) d'un nouvel article, dans le style du compte Pinterest Poil & Museau :
bandeau crème en haut avec le titre en majuscules (vert olive, un mot clé en terracotta), photo au centre,
trait de pinceau crème, bandeau vert olive en bas avec un sous-titre et poiletmuseau.com.

Usage :
    python3 scripts/epingles_article.py <slug-de-l-article> "Titre 1|Sous-titre 1" "Titre 2|Sous-titre 2" "Titre 3|Sous-titre 3" [--ia] [--photos p1 p2 p3]
- Mettez le mot à faire ressortir en terracotta entre astérisques : "Votre chien reconnaît-il certains *mots*?"
- Titre : 3 lignes au plus. Sous-titre : court (une ou deux lignes), facultatif.
- Les 3 épingles doivent proposer 3 angles différents.
- Sans --photos, la photo principale de l'article est utilisée pour les 3 épingles.
- --ia ajoute une petite mention « Image générée par IA » sur la photo. --photos doit venir en dernier.
Écrit images/pins/<slug>-1.jpg, -2.jpg, -3.jpg. Nécessite Playwright (déjà installé dans les sessions Claude).
Polices : scripts/polices/ (League Spartan pour le titre, Poppins pour le sous-titre).
"""
import html as H
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "images", "pins")
FONTS = os.path.join(HERE, "scripts", "polices")

TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:T;src:url(file://{fonts}/league-spartan-latin-800-normal.woff2)}}
@font-face{{font-family:P;src:url(file://{fonts}/poppins-latin-400-normal.woff2)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:#F7F2EE;position:relative;overflow:hidden}}
.top{{position:absolute;inset:0 0 auto 0;height:386px;display:flex;align-items:center;justify-content:center;padding:30px 70px 22px}}
h1{{font-family:T,sans-serif;font-weight:800;font-size:{fs}px;line-height:1.1;text-transform:uppercase;text-align:center;color:#47491B;letter-spacing:-.01em}}
h1 em{{font-style:normal;color:#B5622F}}
.ph{{position:absolute;left:0;right:0;top:386px;height:760px;background:url('file://{img}') {pos}/cover}}
.ia{{position:absolute;top:404px;right:20px;background:rgba(43,30,20,.6);color:#F7F2EE;border-radius:999px;padding:7px 16px;font-family:P,sans-serif;font-size:18px}}
.edge{{position:absolute;left:0;top:1112px;width:1000px;height:52px}}
.bot{{position:absolute;left:0;right:0;top:1146px;bottom:0;background:#6B6A27}}
.sub{{position:absolute;left:50px;right:50px;top:1166px;height:200px;display:flex;align-items:center;justify-content:center;text-align:center;font-family:P,sans-serif;font-size:46px;line-height:1.3;color:#FBF8F1}}
.url{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font-family:P,sans-serif;font-size:24px;color:#E4E2C8;opacity:.9}}
</style></head><body>
<div class="top"><h1>{title}</h1></div>
<div class="ph"></div>{ia}
<div class="bot"></div>
<svg class="edge" viewBox="0 0 1000 52" preserveAspectRatio="none"><path d="M0 34 C120 22 260 30 380 24 C520 17 650 26 780 18 C860 13 940 16 1000 10 L1000 30 C930 33 860 31 780 36 C660 41 520 34 380 40 C250 45 120 40 0 46 Z" fill="#F8F3EE"/><path d="M0 46 C140 40 300 44 460 38 C620 33 800 37 1000 30 L1000 34 C820 41 640 38 460 43 C300 48 140 45 0 49 Z" fill="#F8F3EE" opacity=".55"/></svg>
<div class="sub">{sub}</div>
<div class="url">poiletmuseau.com</div>
</body></html>"""


def fmt_titre(t):
    t = H.escape(t)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)


def meta(slug):
    p = os.path.join(HERE, "content", "articles", slug + ".html")
    s = open(p, encoding="utf-8").read()
    return dict(re.findall(r"^(\w+):\s*(.+)$", s.split("-->")[0], re.M))


def main():
    args = sys.argv[1:]
    if len(args) < 4:
        sys.exit(__doc__)
    ia = "--ia" in args
    args = [a for a in args if a != "--ia"]
    photos = []
    if "--photos" in args:
        i = args.index("--photos")
        photos, args = args[i + 1:], args[:i]
    slug, titres = args[0], args[1:4]
    m = meta(slug)
    main_img = os.path.join(HERE, m["image"].lstrip("/"))
    photos = [os.path.abspath(p) for p in photos] or [main_img] * 3
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for n, (arg, img, pos) in enumerate(zip(titres, photos * 3, ["center", "45% center", "55% center"]), 1):
            titre, _, sous = arg.partition("|")
            nu = len(titre.replace("*", ""))
            fs = 78 if nu < 32 else 70 if nu < 52 else 62
            html = TPL.format(fonts=FONTS, img=img, pos=pos, title=fmt_titre(titre.strip()), sub=H.escape(sous.strip()), fs=fs,
                              ia='<div class="ia">Image générée par IA</div>' if ia else "")
            tmp = os.path.join(OUT, "_tmp.html")
            open(tmp, "w", encoding="utf-8").write(html)
            pg.goto("file://" + tmp)
            pg.wait_for_timeout(300)
            dest = os.path.join(OUT, f"{slug}-{n}.jpg")
            pg.screenshot(path=dest, type="jpeg", quality=86)
            print(dest)
        os.remove(os.path.join(OUT, "_tmp.html"))
        b.close()


if __name__ == "__main__":
    main()
