"""Génère une image verticale Pinterest (1000 × 1500) pour chaque article, FR et EN.

À lancer après l'ajout ou la modification d'un article :
    python3 build.py --local && python3 scripts/epingles.py
Nécessite Playwright (pip install playwright ; python -m playwright install chromium).
Les images sont écrites dans images/pins/ et utilisées par build.py (bouton « Épingler »).
"""
import os
import re
import sys
import html as H

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "images", "pins")
os.makedirs(OUT, exist_ok=True)


def lire(path):
    s = open(path, encoding="utf-8").read()
    m = re.match(r"\s*<!--(.*?)-->", s, re.S)
    meta = {}
    for ln in (m.group(1) if m else "").splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def articles():
    fr = {}
    for f in sorted(os.listdir(os.path.join(HERE, "content", "articles"))):
        if f.endswith(".html"):
            m = lire(os.path.join(HERE, "content", "articles", f))
            if m.get("brouillon") == "oui":
                continue
            fr[f[:-5]] = m
    out = [("fr", h, m["titre"], m.get("resume", ""), m["image"], m.get("animal", "")) for h, m in fr.items()]
    d = os.path.join(HERE, "content", "en", "articles")
    for f in sorted(os.listdir(d)):
        if f.endswith(".html"):
            m = lire(os.path.join(d, f))
            src = fr.get(m.get("traduction_de", ""))
            if src:
                out.append(("en", f[:-5], m["titre"], m.get("resume", ""), src["image"], src.get("animal", "")))
    return out


TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:F;src:url(file://{root}/static/fonts/fraunces-latin-soft-normal.woff2)}}
@font-face{{font-family:J;src:url(file://{root}/static/fonts/plus-jakarta-sans-latin-wght-normal.woff2)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1000px;height:1500px;background:#FBF5EC;font-family:J,sans-serif;color:#2B1E14;position:relative;overflow:hidden}}
.ph{{position:absolute;inset:0 0 auto 0;height:930px;background:url('file://{img}') center/cover}}
.ph::after{{content:"";position:absolute;inset:auto 0 0 0;height:160px;background:linear-gradient(transparent,#FBF5EC)}}
.tag{{position:absolute;top:44px;left:44px;background:#FBF5EC;border-radius:999px;padding:14px 28px;font-weight:800;font-size:28px;letter-spacing:.06em;text-transform:uppercase;color:#7A3A12}}
.box{{position:absolute;left:60px;right:60px;bottom:150px}}
h1{{font-family:F,serif;font-weight:800;font-size:{fs}px;line-height:1.05;letter-spacing:-.02em;font-variation-settings:"SOFT" 100}}
p{{margin-top:26px;font-size:34px;line-height:1.35;color:#5E5044;font-weight:500}}
.brand{{position:absolute;left:60px;right:60px;bottom:52px;display:flex;align-items:center;justify-content:space-between;font-weight:800;font-size:32px}}
.brand b{{font-family:F,serif;font-size:42px;color:#6B3410}} .brand b i{{color:#D08C3C}}
.brand span{{color:#A65815}}
</style></head><body><div class="ph"></div><div class="tag">{tag}</div>
<div class="box"><h1>{title}</h1><p>{resume}</p></div>
<div class="brand"><b>Poil <i>&amp;</i> Museau</b><span>poiletmuseau.com</span></div></body></html>"""


def main():
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM") or None
    todo = articles()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for lang, h, title, resume, image, animal in todo:
            dest = os.path.join(OUT, ("en-" if lang == "en" else "") + h + ".jpg")
            img = os.path.join(HERE, image.lstrip("/"))
            if not os.path.exists(img):
                print("photo absente :", img); continue
            tag = {"fr": {"chien": "Conseils chien", "chat": "Conseils chat"}, "en": {"chien": "Dog tips", "chat": "Cat tips"}}[lang].get(animal, "Chiens & chats" if lang == "fr" else "Dogs & cats")
            fs = 84 if len(title) < 45 else 72 if len(title) < 70 else 62
            page = TPL.format(root=HERE, img=img, tag=H.escape(tag), title=H.escape(title), resume=H.escape(resume), fs=fs)
            tmp = os.path.join(OUT, "_tmp.html")
            open(tmp, "w", encoding="utf-8").write(page)
            pg.goto("file://" + tmp)
            pg.wait_for_timeout(250)
            pg.screenshot(path=dest, type="jpeg", quality=84)
        os.remove(os.path.join(OUT, "_tmp.html"))
        b.close()
    print(len(os.listdir(OUT)), "épingles dans images/pins/")


if __name__ == "__main__":
    main()
