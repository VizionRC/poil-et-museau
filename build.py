#!/usr/bin/env python3
"""Génère le site bilingue Poil & Museau à partir du dossier content/.

Utilisation :  python3 build.py            (produit le site dans dist/)
               python3 build.py autre_dossier

Français (à la racine) :  content/articles/<adresse>.html     →  /articles/<adresse>
Anglais (sous /en/)     :  content/en/articles/<slug>.html     →  /en/articles/<slug>

Chaque fichier commence par un en-tête <!-- clé: valeur --> suivi du texte en HTML.
Un article anglais indique l'article français qu'il traduit avec « traduction_de: ».
Voir README.md pour ajouter un article."""
import json, re, sys, html, os, datetime, shutil, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
LOCAL = "--local" in sys.argv          # aperçu hors ligne : liens en .html
OUT = os.path.abspath(ARGS[0]) if ARGS else os.path.join(HERE, "dist")
CONTENT = os.path.join(HERE, "content")
SITE = "https://poiletmuseau.com"
e = html.escape

# ---------------------------------------------------------------- langue courante
LANG = "fr"
ROOT = ""          # chemin relatif vers la racine du site depuis la page en cours

def t(fr, en):
    return fr if LANG == "fr" else en

SLUGS = {  # clé: (fichier français, fichier anglais)
    "home": ("index.html", "index.html"), "chiens": ("chiens.html", "dogs.html"), "chats": ("chats.html", "cats.html"),
    "conseils": ("conseils.html", "advice.html"), "aliments": ("aliments-dangereux.html", "dangerous-foods.html"),
    "reco": ("recommandations.html", "recommendations.html"), "apropos": ("a-propos.html", "about.html"),
    "contact": ("contact.html", "contact.html"), "divulgation": ("divulgation.html", "affiliate-disclosure.html"),
    "confidentialite": ("politique-de-confidentialite.html", "privacy-policy.html"),
    "conditions": ("conditions-utilisation.html", "terms-of-use.html"),
}

def path_of(key, lang=None):
    lang = lang or LANG
    s = SLUGS[key][0 if lang == "fr" else 1]
    return s if lang == "fr" else "en/" + s

def u(key, frag=""):
    """Lien vers une page du site, dans la langue courante."""
    return ROOT + path_of(key) + frag

def begin(path):
    global ROOT
    ROOT = "../" * path.count("/")
    return path

def canon(path):
    p = re.sub(r"(^|/)index\.html$", r"\1", path)
    return SITE + "/" + re.sub(r"\.html$", "", p)

# ---------------------------------------------------------------- contenu
REQUIRED_FR = ("titre", "date", "animal", "categorie", "image", "image_alt", "resume")
REQUIRED_EN = ("titre", "traduction_de", "image_alt", "resume")

def read_doc(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"\s*<!--\s*\n(.*?)\n\s*-->\s*\n?(.*)", txt, re.S)
    if not m:
        sys.exit(f"En-tête manquant dans {os.path.relpath(path, HERE)}")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, m.group(2).strip()

def html_files(folder):
    if not os.path.isdir(folder):
        return []
    return [f for f in sorted(os.listdir(folder)) if f.endswith(".html") and not f.startswith("_")]

def load_fr():
    out = []
    folder = os.path.join(CONTENT, "articles")
    for f in html_files(folder):
        meta, body = read_doc(os.path.join(folder, f))
        if meta.get("brouillon", "non").lower() in ("oui", "yes", "true"):
            continue
        missing = [k for k in REQUIRED_FR if not meta.get(k)]
        if missing:
            sys.exit(f"{f} : champ(s) manquant(s) dans l'en-tête : {', '.join(missing)}")
        if meta["animal"] not in ("chien", "chat", "both"):
            sys.exit(f"{f} : animal doit être chien, chat ou both (reçu : {meta['animal']})")
        if meta["categorie"] not in ("sante", "alimentation", "comportement", "produits", "toilettage"):
            sys.exit(f"{f} : categorie invalide ({meta['categorie']})")
        out.append(dict(h=f[:-5], fr=f[:-5], t=meta["titre"], d=meta["date"], sp=meta["animal"], cat=meta["categorie"],
                        img=meta["image"], alt=meta["image_alt"], s=meta["resume"], lang="fr", desc=meta.get("description") or meta["resume"],
                        tags=[x.strip() for x in meta.get("mots_cles", "").split(",") if x.strip()], body=body))
    return sorted(out, key=lambda a: a["d"], reverse=True)

def load_en(by_fr):
    out = []
    folder = os.path.join(CONTENT, "en", "articles")
    for f in html_files(folder):
        meta, body = read_doc(os.path.join(folder, f))
        if meta.get("brouillon", "no").lower() in ("oui", "yes", "true"):
            continue
        missing = [k for k in REQUIRED_EN if not meta.get(k)]
        if missing:
            sys.exit(f"en/{f} : champ(s) manquant(s) dans l'en-tête : {', '.join(missing)}")
        src = by_fr.get(meta["traduction_de"])
        if not src:
            sys.exit(f"en/{f} : traduction_de « {meta['traduction_de']} » ne correspond à aucun article français")
        out.append(dict(h=f[:-5], fr=src["h"], t=meta["titre"], d=meta.get("date", src["d"]), sp=src["sp"], cat=src["cat"],
                        img=meta.get("image", src["img"]), alt=meta["image_alt"], s=meta["resume"], lang="en", desc=meta.get("description") or meta["resume"],
                        tags=[x.strip() for x in meta.get("mots_cles", "").split(",") if x.strip()], body=body))
    return sorted(out, key=lambda a: a["d"], reverse=True)

A_FR = load_fr()
BY_FR = {a["h"]: a for a in A_FR}
A_EN = load_en(BY_FR)
FR2EN = {a["fr"]: a for a in A_EN}

def arts():
    return A_FR if LANG == "fr" else A_EN

def art(fr_handle):
    """Article dans la langue courante (repli sur le français s'il n'est pas encore traduit)."""
    if LANG == "en" and fr_handle in FR2EN:
        return FR2EN[fr_handle]
    return BY_FR[fr_handle]

def art_path(a):
    return ("" if a["lang"] == "fr" else "en/") + "articles/" + a["h"] + ".html"

def art_url(a):
    return ROOT + art_path(a)

# ---------------------------------------------------------------- libellés
CATS = {"sante": ("Santé", "Health"), "alimentation": ("Alimentation", "Nutrition"), "comportement": ("Comportement", "Behaviour"),
        "produits": ("Produits", "Products"), "toilettage": ("Toilettage", "Grooming")}
SPL = {"chien": ("Chien", "Dog"), "chat": ("Chat", "Cat"), "both": ("Chien et chat", "Dog & cat")}
def cat(k): return t(*CATS[k])
def spl(k): return t(*SPL[k])

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
def fmt(d):
    y, m, j = map(int, d.split("-"))
    return f"{j} {MOIS[m-1]} {y}" if LANG == "fr" else f"{MONTHS[m-1]} {j}, {y}"

def img(a, w=720):
    """Petites tailles : vignette 720 px (images/articles/720/) si elle existe, sinon l'image complète."""
    u_ = a["img"]
    if u_.startswith("http"):
        return u_ + ("&" if "?" in u_ else "?") + f"width={w}"
    rel = u_.lstrip("/")
    if w <= 800:
        d, f = os.path.split(rel)
        thumb = os.path.join(d, "720", os.path.splitext(f)[0] + ".webp")
        if os.path.exists(os.path.join(HERE, thumb)):
            return ROOT + thumb
    return ROOT + rel

def abs_img(a, w=1200):
    u_ = a["img"]
    if u_.startswith("http"):
        return u_ + ("&" if "?" in u_ else "?") + f"width={w}"
    return SITE + "/" + u_.lstrip("/")

ARROW = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
PAWBG = '<svg class="paw-bg" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><ellipse cx="6" cy="9" rx="2.2" ry="2.8"/><ellipse cx="10.2" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="14.8" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="19" cy="9" rx="2.2" ry="2.8"/><path d="M12.5 11c-3.2 0-6.2 3.6-6.2 6.4 0 2 1.6 3 3.4 3 1.2 0 2-.6 2.8-.6s1.6.6 2.8.6c1.8 0 3.4-1 3.4-3 0-2.8-3-6.4-6.2-6.4z"/></svg>'

def NAV():
    return [("home", t("Accueil", "Home")), ("chiens", t("Chiens", "Dogs")), ("chats", t("Chats", "Cats")),
            ("conseils", t("Conseils", "Advice")), ("aliments", t("Aliments à éviter", "Foods to avoid")),
            ("reco", t("Recommandations", "Recommendations")), ("apropos", t("À propos", "About"))]

# ---------------------------------------------------------------- gabarit commun
def logo():
    return (f'<a href="{u("home")}" class="logo" aria-label="{t("Poil &amp; Museau, accueil", "Poil &amp; Museau, home")}">'
            f'<img src="{ROOT}images/logo-illustration.webp" alt="" width="72" height="46">'
            '<span class="wm"><span class="w1">Poil</span><span class="amp">&amp;</span><span class="w2">Museau</span></span></a>')

def header(active, alt_href):
    cur = lambda k: ' aria-current="page"' if k == active else ""
    links = "".join(f'<a href="{u(k)}"{cur(k)}>{l}</a>' for k, l in NAV())
    mob = links + f'<a href="{u("contact")}"{cur("contact")}>{t("Nous joindre", "Contact us")}</a>'
    other, other_lang, other_name = ("EN", "en", "English") if LANG == "fr" else ("FR", "fr", "Français")
    return f'''<a class="skip" href="#contenu">{t("Aller au contenu", "Skip to content")}</a>
<div id="progress" aria-hidden="true"></div>
<header class="site">
  <div class="wrap nav">
    {logo()}
    <nav class="links" aria-label="{t("Navigation principale", "Main navigation")}">{links}</nav>
    <div class="nav-right">
      <a class="lang-btn" href="{alt_href}" hreflang="{other_lang}" lang="{other_lang}" title="{other_name}" aria-label="{other_name}">{other}</a>
      <button class="icon-btn" id="theme" type="button" aria-label="{t("Changer le thème clair ou sombre", "Switch light or dark theme")}"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
      <button class="icon-btn burger" id="burger" type="button" aria-label="{t("Ouvrir le menu", "Open menu")}" aria-expanded="false" aria-controls="mm"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg></button>
    </div>
  </div>
  <nav class="mobile-menu" id="mm" hidden aria-label="{t("Menu mobile", "Mobile menu")}">{mob}</nav>
</header>'''

def footer():
    return f'''<footer class="site">
  <div class="wrap">
    <div class="fgrid">
      <div>
        <a href="{u("home")}" aria-label="Poil &amp; Museau"><img class="flogo" src="{ROOT}images/logo.webp" alt="{t("Poil &amp; Museau, complice de vos animaux", "Poil &amp; Museau logo")}" width="240" height="183" loading="lazy"></a>
        <p class="meta" style="margin-top:12px;max-width:320px">{t("Conseils et produits choisis pour le bien-être des chiens et des chats. Fait au Québec.", "Advice and carefully chosen products for the well-being of dogs and cats. Made in Québec.")}</p>
        <p style="margin-top:16px;font-weight:700">info@poiletmuseau.com</p>
      </div>
      <div><h2>{t("Chiens", "Dogs")}</h2><ul>
        <li><a href="{u("chiens", "#sante")}">{cat("sante")}</a></li><li><a href="{u("chiens", "#alimentation")}">{cat("alimentation")}</a></li>
        <li><a href="{u("chiens", "#comportement")}">{cat("comportement")}</a></li><li><a href="{u("chiens", "#toilettage")}">{cat("toilettage")}</a></li>
        <li><a href="{u("chiens", "#produits")}">{cat("produits")}</a></li></ul></div>
      <div><h2>{t("Chats", "Cats")}</h2><ul>
        <li><a href="{u("chats", "#sante")}">{cat("sante")}</a></li><li><a href="{u("chats", "#comportement")}">{cat("comportement")}</a></li>
        <li><a href="{u("chats", "#produits")}">{cat("produits")}</a></li><li><a href="{u("aliments")}">{t("Aliments à éviter", "Foods to avoid")}</a></li></ul></div>
      <div><h2>{t("Infos", "Info")}</h2><ul>
        <li><a href="{u("apropos")}">{t("À propos", "About")}</a></li><li><a href="{u("contact")}">{t("Nous joindre", "Contact us")}</a></li>
        <li><a href="{u("divulgation")}">{t("Divulgation d'affiliation", "Affiliate disclosure")}</a></li>
        <li><a href="{u("confidentialite")}">{t("Politique de confidentialité", "Privacy policy")}</a></li>
        <li><a href="{u("conditions")}">{t("Conditions d'utilisation", "Terms of use")}</a></li></ul></div>
    </div>
    <div class="bottom"><span>© <span id="yr">2026</span> Poil &amp; Museau. {t("Tous droits réservés.", "All rights reserved.")}</span><span>{t("Nos conseils ne remplacent pas l'avis d'un vétérinaire.", "Our advice does not replace a veterinarian's opinion.")}</span></div>
  </div>
</footer>
<button class="icon-btn" id="top" type="button" aria-label="{t("Retour en haut", "Back to top")}"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg></button>'''

PAGES = []
TODAY = datetime.date.today().isoformat()

def page(path, title, desc, body, active="", image=None, jsonld=None, alt=None, img_alt=None, published=None, modified=None):
    """alt : chemin (depuis la racine) de la même page dans l'autre langue."""
    other = "en" if LANG == "fr" else "fr"
    alt = alt or path_of("home", other)
    fr_path, en_path = (path, alt) if LANG == "fr" else (alt, path)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    full_title = title if title.startswith("Poil & Museau") else f"{title} | Poil & Museau"
    og_img = image or abs_img(arts()[0] if arts() else A_FR[0])
    doc = f'''<!doctype html>
<html lang="{t("fr-CA", "en-CA")}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon(path)}">
<link rel="alternate" hreflang="fr-CA" href="{canon(fr_path)}">
<link rel="alternate" hreflang="en-CA" href="{canon(en_path)}">
<link rel="alternate" hreflang="x-default" href="{canon(fr_path)}">
<meta property="og:type" content="{"article" if "articles/" in path else "website"}">
<meta property="og:locale" content="{t("fr_CA", "en_CA")}">
<meta property="og:locale:alternate" content="{t("en_CA", "fr_CA")}">
<meta property="og:site_name" content="Poil &amp; Museau">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon(path)}">
<meta property="og:image" content="{e(og_img)}">
<meta property="og:image:alt" content="{e(img_alt or title)}">
{f'<meta property="article:published_time" content="{published}">' if published else ""}{f'<meta property="article:modified_time" content="{modified or published}">' if published else ""}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(og_img)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="alternate" type="application/rss+xml" title="{t("Poil &amp; Museau : derniers articles", "Poil &amp; Museau: latest articles")}" href="{ROOT}{t("feed.xml", "en/feed.xml")}">
<link rel="icon" type="image/png" href="{ROOT}images/favicon.png">
<link rel="apple-touch-icon" href="{ROOT}images/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,400..800,50..100&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{ROOT}assets/style.css">
<script src="{ROOT}assets/site.js"></script>
{ld}
</head>
<body data-copied="{t("Copié ✓", "Copied ✓")}">
{header(active, ROOT + alt)}
<main id="contenu">
{body}
</main>
{footer()}
</body>
</html>
'''
    if not LOCAL:
        doc = pretty_links(doc)
    dest = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(doc)
    PAGES.append(dict(loc=canon(path), fr=canon(fr_path), en=canon(en_path), lastmod=modified or published or TODAY))

def pretty_links(doc):
    """Liens internes sans « .html » (adresses canoniques servies par Cloudflare)."""
    def fix(m):
        attr, url, frag = m.group(1), m.group(2), m.group(3) or ""
        if re.match(r"^(https?:|mailto:|tel:|#|data:)", url) or not url.endswith(".html"):
            return m.group(0)
        if url.split("/")[-1] == "index.html":
            url = url[:-len("index.html")] or "./"
        else:
            url = url[:-5]
        return f'{attr}="{url}{frag}"'
    return re.sub(r'(href)="([^"#?]+)(#[^"]*)?"', fix, doc)

def card(a):
    return f'''<a class="card" href="{art_url(a)}" data-sp="{a["sp"]}" data-cat="{a["cat"]}">
  <div class="thumb"><img loading="lazy" src="{img(a)}" alt="{e(a["alt"])}" width="720" height="495"><span class="tag t-{a["sp"]}">{spl(a["sp"])}</span></div>
  <div class="cb"><span class="cat-l">{cat(a["cat"])}</span><h3>{e(a["t"])}</h3><p>{e(a["s"])}</p>
  <div class="foot"><span>{fmt(a["d"])}</span><span class="read">{t("Lire →", "Read →")}</span></div></div></a>'''

def crumbs(items):
    out = [f'<a href="{u("home")}">{t("Accueil", "Home")}</a>']
    for href, label in items:
        out.append('<span aria-hidden="true">/</span>')
        out.append(f'<a href="{ROOT}{href}">{e(label)}</a>' if href else f'<span aria-current="page">{e(label)}</span>')
    return f'<nav class="crumbs" aria-label="{t("Fil d&#x27;Ariane", "Breadcrumb")}">' + "".join(out) + "</nav>"

def crumbs_ld(items):
    lst = [{"@type": "ListItem", "position": 1, "name": t("Accueil", "Home"), "item": canon(path_of("home"))}]
    for i, (href, label) in enumerate(items, 2):
        it = {"@type": "ListItem", "position": i, "name": label}
        if href: it["item"] = canon(href)
        lst.append(it)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lst}

def list_tools(articles, show_species):
    counts = {k: sum(1 for a in articles if a["cat"] == k) for k in CATS}
    chips = f'<button class="chip on" type="button" data-cat="all" aria-pressed="true">{t("Tout", "All")}<span class="n">{len(articles)}</span></button>'
    chips += "".join(f'<button class="chip" type="button" data-cat="{k}" aria-pressed="false">{cat(k)}<span class="n">{counts[k]}</span></button>' for k in CATS if counts[k])
    seg = (f'<div class="seg" id="seg" role="group" aria-label="{t("Filtrer par animal", "Filter by animal")}"><span class="pill" aria-hidden="true"></span>'
           f'<button type="button" data-sp="all" class="on" aria-pressed="true">{t("Tous", "All")}</button><button type="button" data-sp="chien" aria-pressed="false">🐶 {t("Chiens", "Dogs")}</button>'
           f'<button type="button" data-sp="chat" aria-pressed="false">🐱 {t("Chats", "Cats")}</button></div>') if show_species else ""
    return f'''<div class="toolbar">
  <div class="left">{seg}<div class="chips" id="chips" role="group" aria-label="{t("Filtrer par sujet", "Filter by topic")}">{chips}</div></div>
  <label class="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="q" type="search" placeholder="{t("Rechercher : harnais, litière, vomit…", "Search: harness, litter, vomiting…")}" aria-label="{t("Rechercher un article", "Search articles")}"></label>
</div>
<p class="count-line" id="count" aria-live="polite">{len(articles)} articles</p>'''

def empty_msg():
    return f'<div class="empty" id="empty" hidden><div style="font-size:3rem" aria-hidden="true">🐾</div><p>{t("Aucun article ne correspond. Essayez un autre mot.", "No article matches. Try another word.")}</p></div>'

def newsletter():
    return f'''<section class="block" style="padding-top:0"><div class="wrap"><div class="news reveal">
  <div><span class="kicker">{t("Infolettre gratuite", "Free newsletter")}</span><h2 class="sec">{t("Un conseil utile,<br><em>chaque lundi.</em>", "One useful tip,<br><em>every Monday.</em>")}</h2>
  <div class="perks"><span>✅ {t("Le nouvel article de la semaine", "The new article of the week")}</span><span>✅ {t("Le tableau comparatif des fontaines à eau offert", "Free cat water fountain comparison chart")}</span><span>✅ {t("Zéro pourriel, désabonnement en un clic", "No spam, unsubscribe in one click")}</span></div></div>
  <form data-demo novalidate>
    <input id="nl-prenom" type="text" placeholder="{t("Votre prénom", "Your first name")}" aria-label="{t("Prénom", "First name")}" autocomplete="given-name">
    <input id="nl-courriel" type="email" required placeholder="{t("votre@courriel.com", "you@email.com")}" aria-label="{t("Courriel", "Email")}" autocomplete="email">
    <button class="btn" type="submit">{t("Je m'inscris", "Sign me up")} 🐾</button>
    <p class="ok-msg" data-ok hidden>{t("Merci! Surveillez votre boîte de réception.", "Thank you! Keep an eye on your inbox.")} 💛</p>
    <small>{t("Vos renseignements sont traités selon notre", "Your information is handled according to our")} <a href="{u("confidentialite")}" style="text-decoration:underline">{t("politique de confidentialité", "privacy policy")}</a> {t("(Loi 25).", "(Québec Law 25).")}</small>
  </form></div></div></section>'''

# ---------------------------------------------------------------- outil aliments
FOODS = [  # emoji, niveau, (nom FR, explication FR), (nom EN, explication EN)
 ("🍫", "bad", ("Chocolat", "Contient de la théobromine, toxique pour les chiens et les chats. Plus il est foncé, plus il est dangereux."),
  ("Chocolate", "Contains theobromine, which is toxic to dogs and cats. The darker it is, the more dangerous it is.")),
 ("🍇", "bad", ("Raisins et raisins secs", "Ils peuvent causer une atteinte rénale chez le chien, même en petite quantité."),
  ("Grapes and raisins", "They can cause kidney damage in dogs, even in small amounts.")),
 ("🧅", "bad", ("Oignon et ail", "Crus, cuits ou en poudre, ils peuvent endommager les globules rouges. Les chats y sont particulièrement sensibles."),
  ("Onion and garlic", "Raw, cooked or powdered, they can damage red blood cells. Cats are especially sensitive.")),
 ("🍬", "bad", ("Xylitol", "Cet édulcorant (gommes, certains beurres d'arachide « sans sucre ») peut provoquer une chute brutale de la glycémie chez le chien."),
  ("Xylitol", "This sweetener (gum, some “sugar-free” peanut butters) can cause a sudden drop in blood sugar in dogs.")),
 ("☕", "bad", ("Café et caféine", "La caféine stimule le cœur et le système nerveux. Gardez tasses, capsules et grains hors de portée."),
  ("Coffee and caffeine", "Caffeine stimulates the heart and nervous system. Keep mugs, pods and beans out of reach.")),
 ("🍷", "bad", ("Alcool", "Même une petite quantité peut causer une intoxication. Attention aux verres laissés sur une table basse."),
  ("Alcohol", "Even a small amount can cause poisoning. Watch out for glasses left on a coffee table.")),
 ("🌰", "bad", ("Noix de macadamia", "Elles peuvent causer faiblesse, tremblements et fièvre chez le chien."),
  ("Macadamia nuts", "They can cause weakness, tremors and fever in dogs.")),
 ("🍞", "bad", ("Pâte crue à la levure", "Elle gonfle dans l'estomac et produit de l'alcool en fermentant."),
  ("Raw yeast dough", "It expands in the stomach and produces alcohol as it ferments.")),
 ("🥑", "care", ("Avocat", "La chair est riche en gras et le noyau peut causer une obstruction. Mieux vaut s'abstenir."),
  ("Avocado", "The flesh is high in fat and the pit can cause a blockage. Best avoided.")),
 ("🥛", "care", ("Lait", "Beaucoup de chiens et de chats digèrent mal le lactose. Un peu peut causer diarrhée et inconfort."),
  ("Milk", "Many dogs and cats don't digest lactose well. A little can cause diarrhea and discomfort.")),
 ("🧀", "care", ("Fromage", "Gras et souvent salé. Un tout petit morceau comme récompense, pas plus."),
  ("Cheese", "Fatty and often salty. A tiny piece as a reward, no more.")),
 ("🦴", "care", ("Os cuits", "Les os cuits peuvent se briser en éclats coupants. Ne les donnez pas."),
  ("Cooked bones", "Cooked bones can splinter into sharp pieces. Don't give them.")),
 ("🥕", "ok", ("Carotte", "Crue ou cuite, nature et coupée en morceaux : une gâterie croquante et faible en calories."),
  ("Carrot", "Raw or cooked, plain and cut into pieces: a crunchy, low-calorie treat.")),
 ("🍎", "ok", ("Pomme", "Sans le cœur ni les pépins, en petits morceaux."),
  ("Apple", "Without the core or seeds, in small pieces.")),
 ("🍗", "ok", ("Poulet cuit nature", "Sans assaisonnement, sans peau grasse et surtout sans os."),
  ("Plain cooked chicken", "Unseasoned, without fatty skin and above all without bones.")),
 ("🍚", "ok", ("Riz cuit", "Nature, il se digère facilement."),
  ("Cooked rice", "Plain, it's easy to digest.")),
 ("🎃", "ok", ("Citrouille nature", "En purée nature, pas la garniture à tarte sucrée et épicée."),
  ("Plain pumpkin", "Plain purée, not sweetened and spiced pie filling.")),
 ("🫐", "ok", ("Bleuets", "Riches en antioxydants, en petite quantité. Une gâterie bien d'ici!"),
  ("Blueberries", "Rich in antioxidants, in small amounts. A truly Canadian treat!")),
]
LVL_COLOR = {"bad": "#B5651D", "care": "#EBB54F", "ok": "#A9BA82"}
def verdict(l): return {"bad": t("À éviter", "Avoid"), "care": t("Prudence", "Caution"), "ok": t("Sécuritaire", "Safe")}[l]
def food(f): return f[2] if LANG == "fr" else f[3]

def foods_tool(heading_tag="h2", extra_cta=""):
    btns = "".join(f'<button class="food" type="button" data-i="{i}" aria-pressed="false"><span class="lvl" style="background:{LVL_COLOR[f[1]]}" aria-hidden="true"></span><span aria-hidden="true">{f[0]}</span>{e(food(f)[0])}</button>' for i, f in enumerate(FOODS))
    data = json.dumps([dict(e=f[0], n=food(f)[0], l=f[1], v=verdict(f[1]), d=food(f)[1]) for f in FOODS], ensure_ascii=False)
    txt = json.dumps({"bad": t("Votre animal en a mangé? Appelez rapidement votre vétérinaire ou une clinique d’urgence.", "Did your pet eat some? Call your veterinarian or an emergency clinic right away."),
                      "badLink": art_url(art("que-faire-si-mon-chien-ou-mon-chat-mange-un-aliment-dangereux")), "badCta": t("Que faire →", "What to do →"),
                      "ok": t("Toujours en petite quantité et en complément de son alimentation habituelle.", "Always in small amounts, on top of their usual diet."),
                      "okLink": art_url(art("aliments-dangereux-chien-chat")), "okCta": t("Voir les 10 aliments à éviter →", "See the 10 foods to avoid →")}, ensure_ascii=False)
    cls = "display" if heading_tag == "h1" else "sec"
    dot = lambda c: f'<i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{c}"></i>'
    return f'''<div class="checker reveal">
  {PAWBG}
  <div class="checker-grid">
    <div><span class="kicker">{t("Outil rapide", "Quick tool")}</span><{heading_tag} class="{cls}">{t("Mon animal peut-il <em>manger ça?</em>", "Can my pet <em>eat this?</em>")}</{heading_tag}>
      <p style="opacity:.85;margin-top:14px;max-width:440px">{t("Touchez un aliment pour savoir s'il est sécuritaire pour votre chien ou votre chat.", "Tap a food to find out if it's safe for your dog or cat.")}</p>
      <div class="foods" id="foods">{btns}</div>
      <div class="legend"><span>{dot("#B5651D")}{verdict("bad")}</span><span>{dot("#EBB54F")}{verdict("care")}</span><span>{dot("#A9BA82")}{verdict("ok")}</span></div>
      {extra_cta}
    </div>
    <div class="verdict" id="verdict" aria-live="polite"><div class="big" aria-hidden="true">🍫</div><span class="badge bad">⛔ {verdict("bad")}</span><h3>{food(FOODS[0])[0]}</h3><p>{food(FOODS[0])[1]}</p><small>{t("Touchez un autre aliment pour voir son verdict.", "Tap another food to see its verdict.")}</small></div>
  </div>
</div>
<script>window.PM_FOODS={data};window.PM_TXT={txt};</script>'''

# ---------------------------------------------------------------- accueil
FACTS = [("🍟", "pattes-chien-sentent-chips",
          ("Pourquoi les pattes de mon chien sentent-elles les chips?", "Des bactéries et levures naturellement présentes sur les coussinets produisent cette odeur. C'est normal, sauf si elle devient forte ou s'accompagne de rougeurs."),
          ("Why do my dog's paws smell like chips?", "Bacteria and yeasts that naturally live on the paw pads produce this smell. It's normal, unless it gets strong or comes with redness.")),
         ("🧶", "pourquoi-chat-fait-des-pattes",
          ("Pourquoi mon chat pétrit-il ma couverture?", "Ce geste remonte à l'allaitement. À l'âge adulte, il est souvent associé au confort et à la détente."),
          ("Why does my cat knead my blanket?", "This behaviour goes back to nursing. In adult cats, it's often linked to comfort and relaxation.")),
         ("🐕", "pourquoi-chien-penche-tete",
          ("Pourquoi mon chien penche-t-il la tête?", "Les recherches suggèrent un lien avec l'attention portée aux mots qu'il reconnaît, et avec l'audition et la vision."),
          ("Why does my dog tilt its head?", "Research suggests a link with attention to words it recognizes, as well as hearing and vision."))]

ORG_LD = {"@context": "https://schema.org", "@type": "Organization", "@id": SITE + "/#organization", "name": "Poil & Museau",
          "alternateName": "Poil et Museau", "url": SITE + "/", "email": "info@poiletmuseau.com",
          "logo": {"@type": "ImageObject", "url": SITE + "/images/logo.png", "width": 900, "height": 686},
          "slogan": "Complice de vos animaux", "areaServed": {"@type": "AdministrativeArea", "name": "Québec, Canada"},
          "knowsLanguage": ["fr-CA", "en-CA"], "knowsAbout": ["Santé des chiens", "Santé des chats", "Alimentation animale",
          "Comportement canin", "Comportement félin", "Toilettage", "Dog health", "Cat health", "Pet nutrition"]}

def build_home():
    path = begin(path_of("home"))
    A = arts()
    f = A[0]
    latest = "".join(card(a) for a in A[1:7])
    facts_html = ""
    for em, h, fr, en in FACTS:
        q, ans = fr if LANG == "fr" else en
        facts_html += (f'<div class="flip reveal" tabindex="0" role="button" aria-label="{t("Retourner la carte", "Flip the card")} : {e(q)}"><div class="in"><div class="face front"><span class="e" aria-hidden="true">{em}</span>'
                       f'<span class="q">{e(q)}</span><small>{t("Touchez pour retourner ↻", "Tap to flip ↻")}</small></div><div class="face back"><p>{e(ans)}</p>'
                       f'<a href="{art_url(art(h))}">{t("Lire l&#x27;article complet →", "Read the full article →")}</a></div></div></div>')
    p1, p2, p3 = art("pourquoi-chien-penche-tete"), art("pourquoi-chat-fait-des-pattes"), art("choisir-nourriture-chien")
    dog_img, cat_img = art("comment-choisir-le-bon-lit-pour-votre-chien"), art("chat-boit-il-assez-deau")
    nd = sum(1 for a in A if a["sp"] in ("chien", "both")); nc = sum(1 for a in A if a["sp"] in ("chat", "both"))
    words = t("chien,chat,museau,poil", "dog,cat,pup,kitty")
    hero_title = t(f'Des conseils qui ont du <span class="swap" id="swap" data-words="{words}"><span>chien</span></span><br>pour des compagnons <span class="underline">bien dans leur poil.',
                   f'Trusted advice for every <span class="swap" id="swap" data-words="{words}"><span>dog</span></span><br>and companions who <span class="underline">feel great in their fur.')
    topics = t("Santé ✦ Alimentation ✦ Comportement ✦ Toilettage ✦ Guides d'achat ✦ Bien-être ✦", "Health ✦ Nutrition ✦ Behaviour ✦ Grooming ✦ Buying guides ✦ Well-being ✦")
    body = f'''
<section class="hero" data-paws>
  <div class="blob b1" aria-hidden="true"></div><div class="blob b2" aria-hidden="true"></div><div class="blob b3" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div>
      <span class="eyebrow"><span class="dot" aria-hidden="true"></span> {t("Nouvel article chaque lundi", "New article every Monday")}</span>
      <h1 class="display">{hero_title}<svg viewBox="0 0 300 16" preserveAspectRatio="none" aria-hidden="true"><path d="M3 11 C 70 3, 150 3, 297 9"/></svg></span></h1>
      <p class="lead">{t("Santé, alimentation, comportement, toilettage : des guides clairs, vérifiés et sans jargon pour mieux comprendre votre chien ou votre chat, et choisir les bons produits sans vous perdre dans le marketing.",
                         "Health, nutrition, behaviour, grooming: clear, well-researched, jargon-free guides to help you understand your dog or cat and choose the right products without getting lost in the marketing.")}</p>
      <div class="cta-row">
        <a href="{u("conseils")}" class="btn btn-primary">{t("Explorer les conseils", "Explore the advice")} {ARROW}</a>
        <a href="{u("aliments")}" class="btn btn-ghost">{t("Mon animal peut-il manger ça?", "Can my pet eat this?")}</a>
      </div>
      <div class="stats">
        <div class="stat"><b data-count="{len(A)}">{len(A)}</b><small>{t("guides et articles", "guides and articles")}</small></div>
        <div class="stat"><b data-count="{nd}">{nd}</b><small>{t("conseils pour chiens", "dog articles")}</small></div>
        <div class="stat"><b data-count="{nc}">{nc}</b><small>{t("conseils pour chats", "cat articles")}</small></div>
      </div>
    </div>
    <div class="collage" aria-hidden="true">
      <div class="polaroid p1"><div class="imgbox"><img src="{img(p1, 700)}" alt=""></div><div class="cap">{t("Pourquoi penche-t-il la tête?", "Why the head tilt?")}</div></div>
      <div class="polaroid p2"><div class="imgbox"><img src="{img(p2, 700)}" alt=""></div><div class="cap">{t("Le mystère du pétrissage", "The kneading mystery")}</div></div>
      <div class="polaroid p3"><div class="imgbox"><img src="{img(p3, 700)}" alt=""></div><div class="cap">{t("Bien lire l'étiquette", "Reading the label")}</div></div>
      <div class="sticker"><span>{t("Vérifié.<br>Expliqué.<br>Choisi 🐾", "Checked.<br>Explained.<br>Chosen 🐾")}</span></div>
    </div>
  </div>
</section>
<div class="marquee" aria-hidden="true"><div class="track"><span>{topics}</span><span>{topics}</span></div></div>

<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Par où commencer?", "Where to start?")}</span><h2 class="sec">{t("Votre compagnon,<br><em>votre parcours.</em>", "Your companion,<br><em>your path.</em>")}</h2></div>
  <p class="lead">{t("Choisissez votre animal pour voir les conseils qui le concernent.", "Choose your animal to see the advice that applies to it.")}</p></div>
  <div class="species">
    <a class="sp dog reveal" href="{u("chiens")}"><div><h3>{t("Chiens", "Dogs")}</h3><p>{t("Promenades, gâteries, bains, harnais et petits comportements attachants.", "Walks, treats, baths, harnesses and endearing little habits.")}</p></div>
      <div class="pills"><span>{cat("sante")}</span><span>{cat("alimentation")}</span><span>{cat("comportement")}</span><span>{cat("toilettage")}</span></div>
      <div class="arrow">{ARROW}</div><img src="{img(dog_img, 600)}" alt="{e(dog_img["alt"])}" loading="lazy"></a>
    <a class="sp cat reveal" href="{u("chats")}"><div><h3>{t("Chats", "Cats")}</h3><p>{t("Hydratation, litière, soins dentaires et langage félin enfin décodé.", "Hydration, litter, dental care and feline body language, finally decoded.")}</p></div>
      <div class="pills"><span>{cat("sante")}</span><span>{cat("produits")}</span><span>{cat("comportement")}</span></div>
      <div class="arrow">{ARROW}</div><img src="{img(cat_img, 600)}" alt="{e(cat_img["alt"])}" loading="lazy"></a>
  </div>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Tout frais", "Just published")}</span><h2 class="sec">{t("Le dernier <em>article</em>", "The latest <em>article</em>")}</h2></div></div>
  <a class="featured reveal" href="{art_url(f)}">
    <div class="img"><img src="{img(f, 1200)}" alt="{e(f["alt"])}"></div>
    <div class="body"><span class="tag t-{f["sp"]}" style="align-self:flex-start">{spl(f["sp"])} · {cat(f["cat"])}</span>
      <h3>{e(f["t"])}</h3><p class="lead" style="font-size:1.02rem">{e(f["s"])}</p>
      <span class="meta">{fmt(f["d"])}</span><span class="btn btn-primary" style="align-self:flex-start">{t("Lire l'article", "Read the article")} {ARROW}</span></div>
  </a>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Récemment publiés", "Recently published")}</span><h2 class="sec">{t("Nos derniers <em>conseils</em>", "Our latest <em>advice</em>")}</h2></div>
  <a class="link-arrow" href="{u("conseils")}">{t(f"Voir les {len(A)} articles →", f"See all {len(A)} articles →")}</a></div>
  <div class="grid">{latest}</div>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  {foods_tool(extra_cta=f'<p style="margin-top:22px"><a class="link-arrow" style="color:var(--butter)" href="{u("aliments")}">{t("Voir la liste complète →", "See the full list →")}</a></p>')}
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Le saviez-vous?", "Did you know?")}</span><h2 class="sec">{t("Petites questions, <em>grandes réponses</em>", "Small questions, <em>big answers</em>")}</h2></div><p class="meta">{t("Touchez une carte pour la retourner", "Tap a card to flip it")}</p></div>
  <div class="facts">{facts_html}</div>
</div></section>
{newsletter()}'''
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "@id": canon(path) + "#website", "name": "Poil & Museau", "url": canon(path),
           "inLanguage": t("fr-CA", "en-CA"), "publisher": {"@id": SITE + "/#organization"},
           "description": t("Conseils, guides d'achat et produits choisis avec soin pour le bien-être des chiens et des chats.", "Advice, buying guides and carefully chosen products for the well-being of dogs and cats."),
           "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": canon(path_of("conseils")) + "?q={search_term_string}"},
                               "query-input": "required name=search_term_string"}},
          ORG_LD]
    page(path, t("Poil & Museau : conseils pour chiens et chats", "Poil & Museau: dog and cat care advice"),
         t("Conseils, guides d'achat et produits choisis avec soin pour le bien-être des chiens et des chats. Santé, alimentation, comportement et toilettage, en français d'ici.",
           "Advice, buying guides and carefully chosen products for the well-being of dogs and cats. Health, nutrition, behaviour and grooming, from Québec."),
         body, "home", jsonld=ld, alt=path_of("home", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- chiens / chats
def build_species(sp):
    dog = sp == "chien"
    key = "chiens" if dog else "chats"
    path = begin(path_of(key))
    A = arts()
    lst = [a for a in A if a["sp"] in (sp, "both")]
    label = t("Chiens", "Dogs") if dog else t("Chats", "Cats")
    hero_a = art("toiletter-chien-maison" if dog else "regard-chat-signification-selon-situation")
    intro = (t("Promenades, gâteries, bains, harnais, petits comportements attachants : tout ce qu'il faut pour mieux comprendre votre chien et en prendre soin au quotidien.",
               "Walks, treats, baths, harnesses, endearing little habits: everything you need to understand your dog and care for it every day.") if dog else
             t("Hydratation, litière, soins dentaires, pétrissage et regards insistants : des réponses claires pour mieux comprendre votre chat.",
               "Hydration, litter, dental care, kneading and long stares: clear answers to help you understand your cat."))
    animal = t("chien", "dog") if dog else t("chat", "cat")
    guides = [a for a in lst if a["cat"] == "produits"][:3]
    guides_html = "".join(f'<a class="rc reveal" href="{art_url(a)}"><span class="ic" style="background:{"#FBE7B5" if dog else "#DDE5C8"}" aria-hidden="true">{"🦮" if dog else "🐈"}</span><h3>{e(a["t"])}</h3><p>{e(a["s"])}</p><span class="go">{t("Voir le guide →", "See the guide →")}</span></a>' for a in guides)
    body = f'''
<section class="page-hero {"dog" if dog else "cat"}"><div class="wrap split">
  <div>{crumbs([(None, label)])}
    <h1 class="display">{t("Tout pour votre", "Everything for your")} <em>{animal}</em></h1>
    <p class="lead">{intro}</p>
    <div class="cta-row"><a class="btn btn-ghost" style="border-color:#2B1E14;color:#2B1E14" href="#liste">{t(f"{len(lst)} conseils à lire ↓", f"{len(lst)} articles to read ↓")}</a></div>
  </div>
  <div class="hero-photo"><img src="{img(hero_a, 900)}" alt="{e(hero_a["alt"])}"></div>
</div></section>
<section class="block" id="liste"><div class="wrap">
  {list_tools(lst, False)}
  <div class="grid" data-list>{"".join(card(a) for a in lst)}</div>
  {empty_msg()}
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Guides d'achat", "Buying guides")}</span><h2 class="sec">{t("Bien choisir pour votre", "Choosing well for your")} <em>{animal}</em></h2></div>
  <a class="link-arrow" href="{u("reco")}">{t("Toutes nos recommandations →", "All our recommendations →")}</a></div>
  <div class="reco" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))">{guides_html}</div>
</div></section>
{newsletter()}'''
    desc = (t(f"Conseils pour chiens : santé, alimentation, comportement, toilettage et guides d'achat. {len(lst)} articles clairs et vérifiés.",
              f"Dog care advice: health, nutrition, behaviour, grooming and buying guides. {len(lst)} clear, well-researched articles.") if dog else
            t(f"Conseils pour chats : santé, hydratation, comportement et guides d'achat. {len(lst)} articles clairs et vérifiés.",
              f"Cat care advice: health, hydration, behaviour and buying guides. {len(lst)} clear, well-researched articles."))
    page(path, t(f"Conseils pour {'chiens' if dog else 'chats'}", f"{'Dog' if dog else 'Cat'} care advice"), desc, body, key,
         image=abs_img(hero_a), jsonld=[crumbs_ld([(None, label)])], alt=path_of(key, "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- conseils
def build_conseils():
    path = begin(path_of("conseils"))
    A = arts()
    label = t("Conseils", "Advice")
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--butter);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs([(None, label)])}
  <span class="kicker">{t("La bibliothèque", "The library")}</span><h1 class="display">{t("Tous nos <em>conseils</em>", "All our <em>advice</em>")}</h1>
  <p class="lead">{t(f"{len(A)} articles pour chiens et chats. Filtrez par animal ou par sujet, ou cherchez un mot.", f"{len(A)} articles for dogs and cats. Filter by animal or topic, or search for a word.")}</p></div></div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  {list_tools(A, True)}
  <div class="grid" data-list>{"".join(card(a) for a in A)}</div>
  {empty_msg()}
</div></section>
{newsletter()}'''
    page(path, t("Tous nos conseils", "All our advice"),
         t(f"Les {len(A)} conseils de Poil & Museau pour chiens et chats : santé, alimentation, comportement, toilettage et guides d'achat.",
           f"All {len(A)} Poil & Museau articles for dogs and cats: health, nutrition, behaviour, grooming and buying guides."),
         body, "conseils", jsonld=[crumbs_ld([(None, label)]), {"@context": "https://schema.org", "@type": "CollectionPage", "url": canon(path),
             "inLanguage": t("fr-CA", "en-CA"), "mainEntity": {"@type": "ItemList", "numberOfItems": len(A),
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": canon(art_path(x)), "name": x["t"]} for i, x in enumerate(A)]}}],
         alt=path_of("conseils", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- aliments
def build_aliments():
    path = begin(path_of("aliments"))
    label = t("Aliments à éviter", "Foods to avoid")
    rows = "".join(f'<tr><td><span aria-hidden="true">{f[0]}</span> <strong>{e(food(f)[0])}</strong></td><td><span class="badge {f[1]}" style="padding:4px 10px;border-radius:999px;font-weight:800;font-size:.75rem;text-transform:uppercase;white-space:nowrap">{verdict(f[1])}</span></td><td>{e(food(f)[1])}</td></tr>' for f in FOODS)
    rel = [art("aliments-dangereux-chien-chat"), art("que-faire-si-mon-chien-ou-mon-chat-mange-un-aliment-dangereux"), art("chien-chat-vomit-quand-sinquieter")]
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": t(f"Mon chien ou mon chat peut-il manger : {food(f)[0].lower()}?", f"Can my dog or cat eat {food(f)[0].lower()}?"),
         "acceptedAnswer": {"@type": "Answer", "text": f"{verdict(f[1])}. {food(f)[1]}"}} for f in FOODS]}
    body = f'''
<section class="block" style="padding-top:24px"><div class="wrap">
  {crumbs([(None, label)])}
  {foods_tool("h1")}
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Aide-mémoire", "Cheat sheet")}</span><h2 class="sec">{t("La liste <em>complète</em>", "The <em>full</em> list")}</h2></div>
  <p class="lead">{t("À garder sous la main, ou à montrer à la gardienne avant de partir en vacances.", "Keep it handy, or show it to your pet sitter before you leave on vacation.")}</p></div>
  <div class="table-scroll reveal"><table class="food-table"><thead><tr><th scope="col">{t("Aliment", "Food")}</th><th scope="col">Verdict</th><th scope="col">{t("Pourquoi", "Why")}</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="vet-note"><span aria-hidden="true">🚨</span><span>{t("<strong>En cas d'ingestion d'un aliment à éviter</strong>, appelez rapidement votre vétérinaire ou une clinique d'urgence. Ne faites pas vomir votre animal sans avis professionnel.",
                                                                  "<strong>If your pet eats a food to avoid</strong>, call your veterinarian or an emergency clinic right away. Do not make your pet vomit without professional advice.")}</span></div>
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Pour aller plus loin", "Learn more")}</span><h2 class="sec">{t("À lire <em>aussi</em>", "Read <em>next</em>")}</h2></div></div>
  <div class="grid">{"".join(card(a) for a in rel)}</div>
</div></section>'''
    page(path, t("Mon animal peut-il manger ça?", "Can my pet eat this?"),
         t("Chocolat, raisins, oignon, xylitol… Vérifiez en un clic si un aliment est sécuritaire pour votre chien ou votre chat, et que faire en cas d'ingestion.",
           "Chocolate, grapes, onion, xylitol… Check in one click whether a food is safe for your dog or cat, and what to do if they eat it."),
         body, "aliments", image=abs_img(rel[0]), jsonld=[crumbs_ld([(None, label)]), faq], alt=path_of("aliments", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- recommandations
RECO = [  # emoji, fond, animal, article FR, (titre FR, critères FR), (titre EN, critères EN)
 ("💧", "#DDE5C8", "chat", "fontaine-eau-chat-plastique-ceramique-acier-inoxydable",
  ("Fontaine à eau pour chat", ["Matériau facile à laver", "Filtre accessible et abordable", "Pompe silencieuse"]),
  ("Cat water fountain", ["Easy-to-clean material", "Affordable, easy-to-find filters", "Quiet pump"])),
 ("🧹", "#DDE5C8", "chat", "litiere-autonettoyante-chat",
  ("Litière autonettoyante", ["Taille adaptée à votre chat", "Capteurs de présence fiables", "Entretien réel à prévoir"]),
  ("Self-cleaning litter box", ["Right size for your cat", "Reliable presence sensors", "Realistic upkeep"])),
 ("🧴", "#DDE5C8", "chat", "les-essentiels-indispensables-pour-chat",
  ("Les essentiels du chat", ["Litière et emplacement", "Arbre à chat et griffoir", "Jouets d'activité"]),
  ("Cat essentials", ["Litter box and location", "Cat tree and scratching post", "Activity toys"])),
 ("🦮", "#FBE7B5", "chien", "comment-choisir-harnais-pour-chien",
  ("Harnais pour chien", ["Type adapté à sa démarche", "Ajustement aux épaules", "Points de réglage multiples"]),
  ("Dog harness", ["Type suited to its gait", "Fit around the shoulders", "Several adjustment points"])),
 ("🛏️", "#FBE7B5", "chien", "comment-choisir-le-bon-lit-pour-votre-chien",
  ("Lit pour chien", ["Taille selon sa position de sommeil", "Housse lavable", "Rebords ou non selon ses habitudes"]),
  ("Dog bed", ["Size based on how it sleeps", "Washable cover", "Bolsters or not, depending on its habits"])),
 ("🛁", "#FBE7B5", "chien", "toiletter-chien-maison",
  ("Toilettage à la maison", ["Brosse adaptée au pelage", "Coupe-griffes sécuritaire", "Shampoing pour chien"]),
  ("Grooming at home", ["Brush suited to the coat", "Safe nail clipper", "Dog shampoo"])),
 ("🧳", "#FBE7B5", "chien", "sac-voyage-chien-vacances",
  ("Sac de voyage du chien", ["Bol pliable et eau", "Trousse de premiers soins", "Copie du carnet de santé"]),
  ("Dog travel bag", ["Collapsible bowl and water", "First-aid kit", "Copy of health records"])),
 ("🥣", "#FBE7B5", "chien", "choisir-nourriture-chien",
  ("Nourriture pour chien", ["Mention « complète et équilibrée »", "Stade de vie indiqué", "Fabricant transparent"]),
  ("Dog food", ["“Complete and balanced” statement", "Life stage on the label", "Transparent manufacturer"])),
]
def build_reco():
    path = begin(path_of("reco"))
    label = t("Recommandations", "Recommendations")
    cards = ""
    for ic, bg, sp, h, fr, en in RECO:
        title, crit = fr if LANG == "fr" else en
        cards += (f'<a class="rc reveal" href="{art_url(art(h))}" data-sp="{sp}"><span class="ic" style="background:{bg}" aria-hidden="true">{ic}</span>'
                  f'<span class="tag t-{sp}" style="align-self:flex-start">{spl(sp)}</span><h3>{e(title)}</h3><ul>{"".join(f"<li>{e(c)}</li>" for c in crit)}</ul>'
                  f'<span class="go">{t("Lire le guide →", "Read the guide →")}</span></a>')
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--blush);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs([(None, label)])}
  <span class="kicker">{t("Guides d'achat", "Buying guides")}</span><h1 class="display">{t("Nos <em>recommandations</em>", "Our <em>recommendations</em>")}</h1>
  <p class="lead">{t("Avant de recommander un produit, on explique comment le choisir. Chaque guide présente les critères qui comptent vraiment, puis des modèles à considérer.",
                     "Before recommending a product, we explain how to choose one. Each guide covers the criteria that really matter, then models worth considering.")}</p></div></div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="reco four">{cards}</div>
  <p class="disclose reveal"><span aria-hidden="true">ℹ️</span><span>{t("Certains liens de nos guides sont des liens d'affiliation, notamment avec le programme Partenaires d'Amazon. Si vous achetez par leur entremise, Poil &amp; Museau peut recevoir une commission, sans frais supplémentaires pour vous.",
                                                                         "Some links in our guides are affiliate links, including through the Amazon Associates program. If you buy through them, Poil &amp; Museau may earn a commission at no extra cost to you.")} <a href="{u("divulgation")}">{t("Lire notre divulgation", "Read our disclosure")}</a></span></p>
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Notre méthode", "Our method")}</span><h2 class="sec">{t("Comment on <em>choisit</em>", "How we <em>choose</em>")}</h2></div></div>
  <div class="values">
    <div class="value reveal"><span class="ic" aria-hidden="true">🔍</span><h3>{t("On part du besoin", "We start from the need")}</h3><p>{t("On commence par ce dont votre animal a besoin, pas par le produit à vendre.", "We start with what your pet needs, not with a product to sell.")}</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">📚</span><h3>{t("On s'appuie sur des sources", "We rely on sources")}</h3><p>{t("Organisations vétérinaires, écoles de médecine vétérinaire et références reconnues.", "Veterinary organizations, veterinary schools and recognized references.")}</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">🤝</span><h3>{t("On reste transparents", "We stay transparent")}</h3><p>{t("Les liens d'affiliation sont toujours identifiés et ne changent pas nos critères.", "Affiliate links are always identified and never change our criteria.")}</p></div>
  </div>
</div></section>
{newsletter()}'''
    page(path, t("Nos recommandations", "Our recommendations"),
         t("Guides d'achat pour chiens et chats : fontaine à eau, litière autonettoyante, harnais, lit, toilettage et nourriture. Les critères qui comptent vraiment.",
           "Buying guides for dogs and cats: water fountain, self-cleaning litter box, harness, bed, grooming and food. The criteria that really matter."),
         body, "reco", jsonld=[crumbs_ld([(None, label)])], alt=path_of("reco", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- à propos
def build_apropos():
    path = begin(path_of("apropos"))
    label = t("À propos", "About")
    prose = t('''<p><strong>Les chiens et les chats ne sont pas simplement des animaux de compagnie.</strong> Ils partagent nos vies, nos habitudes et occupent une place essentielle dans notre quotidien.</p>
    <p>Poil &amp; Museau est un site indépendant consacré aux chiens et aux chats. Il a été pensé pour vous aider à faire des choix éclairés, sans perdre de temps ni vous compliquer la vie.</p>
    <p>Vous y trouverez des conseils pratiques pour améliorer leur bien-être jour après jour, ainsi que des produits soigneusement sélectionnés : alimentation, accessoires utiles, hygiène et confort.</p>
    <h2>Notre mission et notre approche</h2>
    <p>Notre objectif est de partager des conseils pratiques, des informations utiles et des recommandations de produits afin d'aider les propriétaires à prendre soin de leurs compagnons.</p>
    <p>Les contenus sont rédigés avec soin à partir de recherches, de références reconnues, de recommandations d'organisations spécialisées et d'informations accessibles au grand public.</p>
    <p><em><strong>Prenez soin de lui simplement, avec ce qu'il y a de mieux. 🐾</strong></em></p>''',
    '''<p><strong>Dogs and cats aren't just pets.</strong> They share our lives and our routines, and they hold an essential place in our everyday.</p>
    <p>Poil &amp; Museau is an independent website dedicated to dogs and cats. It was designed to help you make informed choices without wasting time or overcomplicating things.</p>
    <p>You'll find practical advice to improve their well-being day after day, along with carefully selected products: food, useful accessories, hygiene and comfort.</p>
    <h2>Our mission and approach</h2>
    <p>Our goal is to share practical advice, useful information and product recommendations to help owners take care of their companions.</p>
    <p>Our content is carefully written based on research, recognized references, recommendations from specialized organizations and publicly available information.</p>
    <p><em><strong>Take care of them simply, with the very best. 🐾</strong></em></p>''')
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--sky);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs([(None, label)])}
  <span class="kicker">{label}</span><h1 class="display">{t("Parce que leur bonheur <em>compte autant que le nôtre</em>", "Because their happiness <em>matters as much as ours</em>")}</h1></div></div></section>
<div class="wrap"><div class="text-page">
  <div class="prose">{prose}</div>
  <aside class="side-card reveal"><img src="{ROOT}images/logo.webp" alt="{t("Logo Poil &amp; Museau, complice de vos animaux", "Poil &amp; Museau logo")}" width="300" height="229" style="margin:-6px auto 4px;width:100%;max-width:300px"><h2>{t("Une question?", "A question?")}</h2><p class="meta">{t("Une suggestion d'article ou une question sur un produit recommandé? Écrivez-nous.", "An article idea or a question about a recommended product? Write to us.")}</p>
    <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">{t("Copier", "Copy")}</button></div>
    <a class="link-arrow" href="{u("contact")}">{t("Page Nous joindre →", "Contact page →")}</a></aside>
</div>
<section class="block" style="padding-top:0">
  <div class="sec-head reveal"><div><span class="kicker">{t("Ce qui nous guide", "What guides us")}</span><h2 class="sec">{t("Trois <em>principes</em>", "Three <em>principles</em>")}</h2></div></div>
  <div class="values">
    <div class="value reveal"><span class="ic" aria-hidden="true">🤝</span><h3>{t("Transparence", "Transparency")}</h3><p>{t("Les liens d'affiliation sont identifiés, et nos critères de sélection sont expliqués.", "Affiliate links are identified, and our selection criteria are explained.")}</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">💛</span><h3>{t("Bien-être animal", "Animal well-being")}</h3><p>{t("Chaque conseil part de ce qui est bon pour l'animal, pas de ce qui se vend le mieux.", "Every piece of advice starts from what's good for the animal, not what sells best.")}</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">✨</span><h3>{t("Simplicité", "Simplicity")}</h3><p>{t("Des explications claires, sans jargon, qu'on peut appliquer dès aujourd'hui.", "Clear, jargon-free explanations you can apply today.")}</p></div>
  </div>
</section></div>'''
    page(path, label, t("Poil & Museau est un site indépendant consacré aux chiens et aux chats : conseils pratiques et produits choisis avec transparence pour leur bien-être.",
                        "Poil & Museau is an independent website dedicated to dogs and cats: practical advice and transparently chosen products for their well-being."),
         body, "apropos", jsonld=[crumbs_ld([(None, label)]), dict(ORG_LD, **{"@type": "Organization"}),
                                   {"@context": "https://schema.org", "@type": "AboutPage", "url": canon(path), "inLanguage": t("fr-CA", "en-CA"), "about": {"@id": SITE + "/#organization"}}], alt=path_of("apropos", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- contact
def build_contact():
    path = begin(path_of("contact"))
    label = t("Nous joindre", "Contact us")
    opts = t(["Question sur un article", "Suggestion d'article", "Question sur un produit recommandé", "Partenariat", "Autre"],
             ["Question about an article", "Article suggestion", "Question about a recommended product", "Partnership", "Other"])
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--butter);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs([(None, label)])}
  <span class="kicker">{label}</span><h1 class="display">{t("Écrivez-<em>nous</em>", "Write <em>to us</em>")}</h1>
  <p class="lead">{t("Merci de votre visite chez Poil &amp; Museau 🐾 Une question, une idée d'article ou un commentaire sur un produit? On vous répond avec plaisir.",
                     "Thanks for visiting Poil &amp; Museau 🐾 A question, an article idea or a comment about a product? We're happy to answer.")}</p></div></div></section>
<div class="wrap"><div class="text-page">
  <form class="form side-card" data-demo style="padding:30px">
    <label for="c-nom">{t("Nom", "Name")}<input id="c-nom" type="text" autocomplete="name" required></label>
    <label for="c-courriel">{t("Courriel", "Email")}<input id="c-courriel" type="email" autocomplete="email" required></label>
    <label for="c-sujet">{t("Sujet", "Subject")}<select id="c-sujet">{"".join(f"<option>{e(o)}</option>" for o in opts)}</select></label>
    <label for="c-msg">Message<textarea id="c-msg" required></textarea></label>
    <button class="btn btn-primary" type="submit" style="justify-content:center">{t("Envoyer le message", "Send message")}</button>
    <p class="notice" data-ok hidden>{t("Merci! Votre message a bien été pris en note.", "Thank you! Your message has been noted.")} 💛</p>
  </form>
  <aside style="display:flex;flex-direction:column;gap:16px">
    <div class="side-card"><h2>{t("Par courriel", "By email")}</h2>
      <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">{t("Copier", "Copy")}</button></div></div>
    <div class="side-card"><h2>{t("Une commande?", "About an order?")}</h2><p class="meta">{t("Nous recommandons des produits par l'entremise de partenaires de confiance. Pour une question sur une commande, une livraison ou un retour, communiquez directement avec le marchand concerné.",
                                                                                            "We recommend products through trusted partners. For questions about an order, delivery or return, please contact the merchant directly.")}</p>
      <a class="link-arrow" href="{u("divulgation")}">{t("Notre divulgation d'affiliation →", "Our affiliate disclosure →")}</a></div>
  </aside>
</div></div>'''
    page(path, label, t("Une question, une idée d'article ou un commentaire? Écrivez à Poil & Museau à info@poiletmuseau.com.",
                        "A question, an article idea or a comment? Write to Poil & Museau at info@poiletmuseau.com."),
         body, "contact", jsonld=[crumbs_ld([(None, label)]), {"@context": "https://schema.org", "@type": "ContactPage", "url": canon(path),
                                   "inLanguage": t("fr-CA", "en-CA"), "about": {"@id": SITE + "/#organization"}}], alt=path_of("contact", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- divulgation
def build_divulgation():
    path = begin(path_of("divulgation"))
    label = t("Divulgation d'affiliation", "Affiliate disclosure")
    prose = t('''<p>Chez <strong>Poil &amp; Museau</strong> 🐾, je prends le temps de sélectionner avec soin des produits pour le bien-être de vos compagnons.</p>
    <p>Certains liens présents sur ce site peuvent être des liens d'affiliation, notamment par l'entremise du programme Partenaires d'Amazon. Cela signifie que je peux recevoir une commission si vous effectuez un achat par ces liens, sans frais supplémentaires pour vous.</p>
    <p class="tip"><strong>En tant que Partenaire d'Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</strong></p>
    <p>💛 Ces recommandations sont faites en toute transparence et reflètent mes choix personnels, basés sur la qualité, la fiabilité et l'intérêt pour vos animaux.</p>
    <p>Je vous remercie sincèrement de soutenir mon travail et de contribuer à faire vivre cette plateforme.</p>''',
    '''<p>At <strong>Poil &amp; Museau</strong> 🐾, I take the time to carefully select products for the well-being of your companions.</p>
    <p>Some links on this website may be affiliate links, including through the Amazon Associates program. This means I may earn a commission if you make a purchase through these links, at no extra cost to you.</p>
    <p class="tip"><strong>As an Amazon Associate, I earn from qualifying purchases.</strong></p>
    <p>💛 These recommendations are made transparently and reflect my personal choices, based on quality, reliability and their value for your pets.</p>
    <p>Thank you sincerely for supporting my work and helping keep this platform alive.</p>''')
    body = f'''
<section class="page-hero"><div class="wrap"><div>{crumbs([(None, label)])}
  <span class="kicker">{t("Transparence", "Transparency")}</span><h1 class="display">{t("Divulgation <em>d'affiliation</em>", "Affiliate <em>disclosure</em>")}</h1></div></div></section>
<div class="wrap"><div class="text-page">
  <div class="prose">{prose}</div>
  <aside class="side-card"><h2>{t("Comment reconnaître un lien d'affiliation?", "How to spot an affiliate link?")}</h2><p class="meta">{t("Dans nos articles, les produits recommandés sont présentés dans un encadré pointillé, comme celui-ci :", "In our articles, recommended products appear in a dotted box like this one:")}</p>
    <div class="prose" style="font-size:.95rem"><div class="aff"><p>👉 <strong>{t("Voir le produit recommandé", "See the recommended product")}</strong></p></div></div></aside>
</div></div>'''
    page(path, label, t("Poil & Museau participe au programme Partenaires d'Amazon. Comment fonctionnent nos liens d'affiliation et comment les reconnaître.",
                        "Poil & Museau participates in the Amazon Associates program. How our affiliate links work and how to recognize them."),
         body, "", jsonld=[crumbs_ld([(None, label)])], alt=path_of("divulgation", "en" if LANG == "fr" else "fr"))

# ---------------------------------------------------------------- articles
def slug(s):
    s = unicodedata.normalize("NFD", re.sub(r"<[^>]+>", "", html.unescape(s)))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "section"

def clean_body(b):
    b = re.sub(r"<meta[^>]*>", "", b)
    b = re.sub(r'\sdata-[\w-]+="[^"]*"', "", b)
    b = re.sub(r'\sstyle="[^"]*"', "", b)
    seen = set()
    def h2(m):
        attrs, inner = m.group(1), m.group(2)
        mid = re.search(r'id="([^"]+)"', attrs)
        hid = mid.group(1) if mid else slug(inner)
        base, k = hid, 2
        while hid in seen: hid = f"{base}-{k}"; k += 1
        seen.add(hid)
        return f'<h2 id="{hid}">{inner.strip()}</h2>'
    b = re.sub(r"<h2([^>]*)>(.*?)</h2>", h2, b, flags=re.S)
    b = re.sub(r'href="(?:https?:?/+(?:www\.)?(?:poiletmuseau\.com)?)?/?blogs/actualites/([\w-]+)/?"', r'href="\1.html"', b)
    b = re.sub(r'<a ([^>]*href="https://(?:amzn\.to|link\.amazon|(?:www\.)?amazon\.(?:ca|com))[^"]*"[^>]*)>',
               lambda m: "<a " + re.sub(r'\srel="[^"]*"', "", m.group(1)) + ' rel="nofollow sponsored noopener">', b)
    shop_pages = {"produits-chiens": "chiens", "chiens-produits": "chiens", "produits-chats": "chats", "chats-produits": "chats",
                  "contact": "contact", "divulgation-daffiliation": "divulgation", "nos-recommandations": "reco", "produits": "reco"}
    b = re.sub(r'href="(?:https?://(?:www\.)?poiletmuseau\.com)?/pages/([\w-]+)/?"',
               lambda m: f'href="{u(shop_pages.get(m.group(1), "conseils"))}"', b)
    b = re.sub(r"<img (?![^>]*loading=)", '<img loading="lazy" decoding="async" ', b)
    b = re.sub(r"<table>", '<div class="tbl"><table>', b); b = re.sub(r"</table>", "</table></div>", b)
    b = re.sub(r"<p>\s*(&nbsp;| )?\s*</p>", "", b)
    return b

def localize_links(b):
    """Dans un article anglais, les liens vers un article français traduit pointent vers sa version anglaise."""
    if LANG != "en":
        return b
    return re.sub(r'href="([\w-]+)\.html(#[\w-]*)?"', lambda m: f'href="{FR2EN[m.group(1)]["h"]}.html{m.group(2) or ""}"' if m.group(1) in FR2EN
                  else (f'href="../../articles/{m.group(1)}.html{m.group(2) or ""}"' if m.group(1) in BY_FR else m.group(0)), b)

def faq_from(b):
    """Questions = intertitres H2/H3 qui se terminent par « ? » ; réponse = texte qui suit, jusqu'au prochain intertitre."""
    out = []
    parts = re.split(r"(<h[23][^>]*>.*?</h[23]>)", b, flags=re.S)
    for i in range(1, len(parts) - 1, 2):
        q = html.unescape(re.sub(r"<[^>]+>", "", parts[i])).strip()
        if not q.endswith("?") or len(q) < 12:
            continue
        txt = html.unescape(re.sub(r"<[^>]+>", " ", parts[i + 1]))
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) < 40:
            continue
        words = txt.split(" ")
        ans = " ".join(words[:70]) + ("…" if len(words) > 70 else "")
        out.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}})
    return out[:8]

def related(a, A, n=3):
    same = [x for x in A if x is not a and (x["sp"] == a["sp"] or "both" in (x["sp"], a["sp"])) and x["cat"] == a["cat"]]
    more = [x for x in A if x is not a and x not in same and (x["sp"] == a["sp"] or "both" in (x["sp"], a["sp"]))]
    return (same + more)[:n]

def build_article(i, a, A):
    path = begin(art_path(a))
    sp_key = "chiens" if a["sp"] == "chien" else "chats" if a["sp"] == "chat" else "conseils"
    sp_label = {"chiens": t("Chiens", "Dogs"), "chats": t("Chats", "Cats"), "conseils": t("Conseils", "Advice")}[sp_key]
    items = [(path_of(sp_key), sp_label), (None, a["t"])]
    newer = A[i-1] if i > 0 else None
    older = A[i+1] if i + 1 < len(A) else None
    b = localize_links(clean_body(a["body"])).replace('src="/images/', f'src="{ROOT}images/').replace('href="/images/', f'href="{ROOT}images/')
    words = len(re.sub(r"<[^>]+>", " ", b).split())
    mins = max(2, round(words / 200))
    heads = re.findall(r'<h2 id="([\w-]+)">(.*?)</h2>', b)
    skip = ("sources", "a-lire-aussi", "a-lire-egalement", "read-next", "related-articles", "further-reading")
    toc = "".join(f'<li><a href="#{hid}">{re.sub(r"<[^>]+>", "", ht).strip()}</a></li>' for hid, ht in heads
                  if hid not in skip and not re.sub(r"<[^>]+>", "", ht).strip().lower().startswith(("sources", "à lire", "read ", "related")))
    aside = f'''<aside class="toc" aria-label="{t("Dans cet article", "In this article")}">{f"<h2>{t('Dans cet article', 'In this article')}</h2><ol>" + toc + "</ol>" if toc else f"<h2>{t('Partager', 'Share')}</h2>"}
  <div class="share"><button class="btn btn-ghost" type="button" data-copy="url">{t("Copier le lien", "Copy link")}</button></div></aside>'''
    pager = f'<nav class="pager" aria-label="{t("Articles précédent et suivant", "Previous and next articles")}">'
    pager += f'<a href="{older["h"]}.html"><small>{t("← Article précédent", "← Previous article")}</small><b>{e(older["t"])}</b></a>' if older else "<span></span>"
    pager += f'<a class="next" href="{newer["h"]}.html"><small>{t("Article suivant →", "Next article →")}</small><b>{e(newer["t"])}</b></a>' if newer else ""
    pager += "</nav>"
    meta = f'<span class="tag t-{a["sp"]}">{spl(a["sp"])}</span><span>{cat(a["cat"])}</span><span aria-hidden="true">·</span><time datetime="{a["d"]}">{fmt(a["d"])}</time>'
    meta += f'<span aria-hidden="true">·</span><span>{mins} {t("min de lecture", "min read")}</span>'
    body = f'''
<article>
<div class="wrap art-hero"><div class="art-head">{crumbs(items)}
  <h1>{e(a["t"])}</h1><p class="lead">{e(a["s"])}</p><div class="art-meta">{meta}</div></div>
  <div class="art-cover"><img src="{img(a, 1400)}" alt="{e(a["alt"])}" width="1400" height="700"></div>
</div>
<div class="wrap art-layout">
  <div style="min-width:0"><div class="prose">{b}</div>
    <div class="vet-note"><span aria-hidden="true">🩺</span><span>{t("Cet article est informatif et ne remplace pas l'avis d'un vétérinaire. En cas de doute sur la santé de votre animal, consultez un professionnel.",
                                                                     "This article is for information only and does not replace a veterinarian's advice. If you have any doubt about your pet's health, consult a professional.")}</span></div>
    {pager}
  </div>
  {aside}
</div>
</article>
<section class="block" style="padding-top:20px"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">{t("Continuer la lecture", "Keep reading")}</span><h2 class="sec">{t("À lire <em>aussi</em>", "Read <em>next</em>")}</h2></div></div>
  <div class="grid">{"".join(card(x) for x in related(a, A))}</div>
</div></section>
{newsletter()}'''
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["t"], "description": a["desc"],
          "image": {"@type": "ImageObject", "url": abs_img(a), "caption": a["alt"]},
          "datePublished": a["d"], "dateModified": a["d"], "inLanguage": t("fr-CA", "en-CA"), "wordCount": words,
          "keywords": ", ".join(a["tags"]), "articleSection": cat(a["cat"]),
          "about": {"@type": "Thing", "name": {"chien": t("Chien", "Dog"), "chat": t("Chat", "Cat"), "both": t("Chiens et chats", "Dogs and cats")}[a["sp"]]},
          "author": {"@type": "Organization", "name": "Poil & Museau", "url": SITE + "/"},
          "publisher": {"@id": SITE + "/#organization"}, "isPartOf": {"@id": canon(path_of("home")) + "#website"},
          "mainEntityOfPage": canon(path),
          "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".art-head h1", ".art-head .lead"]}}
    if alt_lang := (FR2EN.get(a["h"]) if LANG == "fr" else BY_FR.get(a["fr"])):
        ld["workTranslation" if LANG == "fr" else "translationOfWork"] = {"@type": "Article", "@id": canon(art_path(alt_lang))}
    faq = faq_from(b)
    lds = [ld, crumbs_ld(items)] + ([{"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": t("fr-CA", "en-CA"), "mainEntity": faq}] if faq else [])
    if LANG == "fr":
        alt = art_path(FR2EN[a["h"]]) if a["h"] in FR2EN else path_of("conseils", "en")
    else:
        alt = art_path(BY_FR[a["fr"]])
    page(path, a["t"], re.sub(r"\s+", " ", a["desc"]), body, "conseils", image=abs_img(a), jsonld=lds, alt=alt,
         img_alt=a["alt"], published=a["d"], modified=a["d"])

# ---------------------------------------------------------------- pages texte (légales)
def build_text_pages():
    folder = os.path.join(CONTENT, "pages") if LANG == "fr" else os.path.join(CONTENT, "en", "pages")
    for f in html_files(folder):
        meta, b = read_doc(os.path.join(folder, f))
        title = meta.get("titre", f[:-5])
        path = begin(("" if LANG == "fr" else "en/") + f)
        if LANG == "fr":
            twin = [g for g in html_files(os.path.join(CONTENT, "en", "pages")) if read_doc(os.path.join(CONTENT, "en", "pages", g))[0].get("traduction_de") == f[:-5]]
            alt = "en/" + twin[0] if twin else path_of("home", "en")
        else:
            alt = meta.get("traduction_de", "index") + ".html"
        body = f'''
<section class="page-hero"><div class="wrap"><div>{crumbs([(None, title)])}
  <span class="kicker">{e(meta.get("surtitre", "Information"))}</span><h1 class="display">{e(title)}</h1>
  {f'<p class="lead">{e(meta["mise_a_jour"])}</p>' if meta.get("mise_a_jour") else ""}</div></div></section>
<div class="wrap"><div class="text-page"><div class="prose">{clean_body(b)}</div>
  <aside class="side-card"><h2>{t("Une question?", "A question?")}</h2><p class="meta">{t("Écrivez-nous, nous vous répondrons dans les meilleurs délais.", "Write to us and we'll get back to you as soon as possible.")}</p>
  <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">{t("Copier", "Copy")}</button></div>
  <a class="link-arrow" href="{u("contact")}">{t("Nous joindre →", "Contact us →")}</a></aside></div></div>'''
        page(path, title, meta.get("description", title), body, "", jsonld=[crumbs_ld([(None, title)])], alt=alt)

def build_404():
    global LANG
    LANG = "fr"; begin("404.html")
    body = '''<section class="block"><div class="wrap" style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:18px">
  <div style="font-size:5rem" aria-hidden="true">🐾</div><h1 class="display">Cette page a <em>filé</em></h1>
  <p class="lead">Elle a peut-être suivi une odeur intéressante. Essayez plutôt l'une de ces pistes.<br><span lang="en">This page wandered off. Try one of these instead.</span></p>
  <div class="cta-row" style="justify-content:center"><a class="btn btn-primary" href="/">Accueil</a><a class="btn btn-ghost" href="/conseils">Conseils</a><a class="btn btn-ghost" href="/en/" lang="en">English</a></div>
</div></section>'''
    page("404.html", "Page introuvable", "Cette page n'existe pas ou a été déplacée.", body, "")
    PAGES.pop()

# ---------------------------------------------------------------- génération
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copytree(os.path.join(HERE, "static"), OUT, dirs_exist_ok=True)
if os.path.isdir(os.path.join(HERE, "images")):
    shutil.copytree(os.path.join(HERE, "images"), os.path.join(OUT, "images"), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".gitkeep", ".DS_Store"))

for LANG in ("fr", "en"):
    build_text_pages()
    build_home(); build_species("chien"); build_species("chat"); build_conseils(); build_aliments()
    build_reco(); build_apropos(); build_contact(); build_divulgation()
    A_ = arts()
    for i, a in enumerate(A_):
        build_article(i, a, A_)
build_404()

# Plan du site bilingue (hreflang) — https://developers.google.com/search/docs/specialty/international/localized-versions
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for p_ in PAGES:
    sm.append(f"  <url><loc>{p_['loc']}</loc><lastmod>{p_['lastmod']}</lastmod>"
              f'<xhtml:link rel="alternate" hreflang="fr-CA" href="{p_["fr"]}"/><xhtml:link rel="alternate" hreflang="en-CA" href="{p_["en"]}"/>'
              f'<xhtml:link rel="alternate" hreflang="x-default" href="{p_["fr"]}"/></url>')
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")

# Flux RSS (découverte rapide des nouveaux articles par les moteurs et agrégateurs)
def rss(lang, items):
    global LANG
    LANG = lang
    home = canon(path_of("home"))
    def rfc(d):
        return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
           f"<title>Poil &amp; Museau</title><link>{home}</link><language>{t('fr-ca', 'en-ca')}</language>",
           f"<description>{e(t('Conseils pour chiens et chats', 'Dog and cat care advice'))}</description>",
           f'<atom:link href="{SITE}/{t("feed.xml", "en/feed.xml")}" rel="self" type="application/rss+xml"/>']
    for a in items[:20]:
        out.append(f"<item><title>{e(a['t'])}</title><link>{canon(art_path(a))}</link><guid>{canon(art_path(a))}</guid>"
                   f"<pubDate>{rfc(a['d'])}</pubDate><description>{e(a['desc'])}</description></item>")
    out.append("</channel></rss>")
    open(os.path.join(OUT, t("feed.xml", "en/feed.xml")), "w", encoding="utf-8").write("\n".join(out) + "\n")
rss("fr", A_FR); rss("en", A_EN)

# llms.txt : résumé du site pour les moteurs génératifs (https://llmstxt.org)
def llms():
    global LANG
    lines = ["# Poil & Museau", "",
             "> Site indépendant québécois de conseils pour chiens et chats (santé, alimentation, comportement, toilettage, guides d'achat), en français et en anglais. "
             "Les articles s'appuient sur des sources vétérinaires reconnues et ne remplacent pas l'avis d'un vétérinaire. Certains liens sont des liens d'affiliation Amazon, identifiés comme tels.", "",
             "Independent Québec website offering dog and cat care advice in French and English.", ""]
    for lang, items in (("fr", A_FR), ("en", A_EN)):
        LANG = lang
        lines.append(t("## Articles (français)", "## Articles (English)"))
        lines += [f"- [{a['t']}]({canon(art_path(a))}): {a['desc']}" for a in items]
        lines.append("")
    LANG = "fr"
    lines += ["## Pages", f"- [Aliments à éviter / Foods to avoid]({canon(path_of('aliments'))}): outil interactif sur les aliments sécuritaires ou toxiques pour chiens et chats",
              f"- [À propos]({canon(path_of('apropos'))})", f"- [Divulgation d'affiliation]({canon(path_of('divulgation'))})",
              f"- [Politique de confidentialité]({canon(path_of('confidentialite'))})", ""]
    open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines))
llms()

# Redirections des anciennes adresses Shopify vers les nouvelles pages.
# Une ligne explicite par ancienne adresse : aucune règle générique ne chevauche une règle précise.
redir = [f"/blogs/actualites/{a['h']} /articles/{a['h']} 301" for a in A_FR]
redir += [f"/blogs/actualites/{a['h']}/ /articles/{a['h']} 301" for a in A_FR]
shopify_pages = {
    "contact": "/contact", "divulgation-daffiliation": "/divulgation", "produits-chiens-chats": "/a-propos",
    "produits-chiens": "/chiens", "chiens-produits": "/chiens", "chiens-sante": "/chiens#sante",
    "chiens-alimentation": "/chiens#alimentation", "chiens-comportement": "/chiens#comportement",
    "chiens-toilettage": "/chiens#toilettage", "produits-chats": "/chats", "chats-produits": "/chats",
    "chats-sante": "/chats#sante", "chats-alimentation": "/chats#alimentation",
    "chats-comportement": "/chats#comportement", "chats-toilettage": "/chats",
    "nos-recommandations": "/recommandations", "nos-recommandations-pour-chiens-et-chats": "/recommandations",
    "essentiels-chien": "/recommandations", "essentiels-chat": "/recommandations", "produits": "/recommandations"}
redir += [f"/pages/{k} {v} 301" for k, v in shopify_pages.items()]
policies = {"privacy-policy": "/politique-de-confidentialite", "terms-of-service": "/conditions-utilisation",
            "legal-notice": "/conditions-utilisation", "contact-information": "/contact",
            "refund-policy": "/divulgation", "shipping-policy": "/divulgation", "divulgation-affiliation": "/divulgation"}
redir += [f"/policies/{k} {v} 301" for k, v in policies.items()]
redir += ["/blogs/actualites /conseils 301", "/blogs/actualites/ /conseils 301", "/blogs/actualites/tagged/* /conseils 301",
          "/collections/* / 301", "/collections / 301", "/products/* /recommandations 301", "/cart / 301",
          "/account / 301", "/account/* / 301", "/search /conseils 301", "/en/blogs/* /en/advice 301", "/fr/* /:splat 301"]
open(os.path.join(OUT, "_redirects"), "w").write("\n".join(redir) + "\n")
# Les robots des moteurs de recherche et des moteurs génératifs sont explicitement bienvenus (visibilité GEO).
bots = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot",
        "Google-Extended", "Applebot", "Applebot-Extended", "DuckDuckBot"]
open(os.path.join(OUT, "robots.txt"), "w").write("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    + f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
missing = [a["h"] for a in A_FR if a["h"] not in FR2EN]
print(f"Site généré dans {os.path.relpath(OUT)} : {len(PAGES)} pages · {len(A_FR)} articles FR · {len(A_EN)} articles EN"
      + (f" · {len(missing)} article(s) pas encore traduit(s)" if missing else ""))
