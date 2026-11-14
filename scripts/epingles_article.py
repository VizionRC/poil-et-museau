"""Crée les 3 épingles Pinterest (1000 × 1500, encadré terracotta) d'un nouvel article.

Usage :
    python3 scripts/epingles_article.py <slug-de-l-article> "Titre 1" "Titre 2" "Titre 3" [--photos p1.webp p2.webp p3.webp] [--ia]
- Les titres (3 lignes au plus à l'affichage) doivent proposer 3 angles différents.
- Sans --photos, la photo principale de l'article est utilisée pour les 3 épingles (recadrages différents).
- --ia ajoute la mention « Image générée par IA » (à utiliser si la photo a été générée).
Écrit images/pins/<slug>-1.jpg, -2.jpg, -3.jpg. Nécessite Playwright (déjà installé dans les sessions Claude).
"""
import html as H
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "images", "pins")

TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:F;src:url(file://{root}/static/fonts/fraunces-latin-soft-normal.woff2)}}
@font-face{{font-family:J;src:url(file://{root}/static/fonts/plus-jakarta-sans-latin-wght-normal.woff2)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:#A65815;font-family:J,sans-serif;position:relative;overflow:hidden}}
.card{{position:absolute;inset:34px;background:#FBF5EC;border-radius:34px;overflow:hidden}}
.ph{{position:absolute;inset:0 0 auto 0;height:880px;background:url('file://{img}') {pos}/cover}}
.tag{{position:absolute;top:34px;left:34px;background:#FBF5EC;border-radius:999px;padding:12px 26px;font-weight:800;font-size:26px;letter-spacing:.06em;text-transform:uppercase;color:#7A3A12}}
.ia{{position:absolute;top:34px;right:34px;background:rgba(43,30,20,.72);color:#FBF5EC;border-radius:999px;padding:10px 20px;font-weight:700;font-size:20px}}
.box{{position:absolute;left:56px;right:56px;top:930px}}
h1{{font-family:F,serif;font-weight:800;font-size:{fs}px;line-height:1.06;letter-spacing:-.02em;color:#2B1E14;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-variation-settings:"SOFT" 100}}
.brand{{position:absolute;left:56px;right:56px;bottom:44px;display:flex;align-items:center;justify-content:space-between;font-weight:800;font-size:30px;color:#A65815}}
.brand b{{font-family:F,serif;font-size:42px;color:#6B3410}} .brand b i{{color:#D08C3C}}
</style></head><body><div class="card"><div class="ph"></div><div class="tag">{tag}</div>{ia}
<div class="box"><h1>{title}</h1></div>
<div class="brand"><b>Poil <i>&amp;</i> Museau</b><span>poiletmuseau.com</span></div></div></body></html>"""


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
    tag = {"chien": "Conseils chien", "chat": "Conseils chat"}.get(m.get("animal"), "Chiens & chats")
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for n, (titre, img, pos) in enumerate(zip(titres, photos * 3, ["center", "30% center", "70% center"]), 1):
            fs = 82 if len(titre) < 40 else 72 if len(titre) < 60 else 62
            html = TPL.format(root=HERE, img=img, pos=pos, tag=H.escape(tag), title=H.escape(titre), fs=fs,
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
