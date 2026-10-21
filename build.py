#!/usr/bin/env python3
"""Génère le site Poil & Museau à partir du dossier content/.

Utilisation :  python3 build.py            (produit le site dans dist/)
               python3 build.py autre_dossier

Chaque article est un fichier content/articles/<adresse>.html qui commence par
un en-tête (titre, date, animal, catégorie, image…) suivi du texte en HTML.
Voir README.md pour ajouter un article."""
import json, re, sys, html, os, datetime, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "dist")
CONTENT = os.path.join(HERE, "content")
SITE = "https://poiletmuseau.com"
CDN = "https://cdn.shopify.com/s/files/1/0995/7451/3945/articles/"
OLD = "https://poiletmuseau.com/blogs/actualites/"

REQUIRED = ("titre", "date", "animal", "categorie", "image", "image_alt", "resume")

def read_doc(path):
    """Lit un fichier de contenu : en-tête <!-- clé: valeur --> puis le corps HTML."""
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

def load_articles():
    out = []
    folder = os.path.join(CONTENT, "articles")
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".html") or f.startswith("_"):
            continue
        meta, body = read_doc(os.path.join(folder, f))
        if meta.get("brouillon", "non").lower() in ("oui", "yes", "true"):
            continue
        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            sys.exit(f"{f} : champ(s) manquant(s) dans l'en-tête : {', '.join(missing)}")
        if meta["animal"] not in ("chien", "chat", "both"):
            sys.exit(f"{f} : animal doit être chien, chat ou both (reçu : {meta['animal']})")
        if meta["categorie"] not in ("sante", "alimentation", "comportement", "produits", "toilettage"):
            sys.exit(f"{f} : categorie invalide ({meta['categorie']})")
        out.append(dict(h=f[:-5], t=meta["titre"], d=meta["date"], sp=meta["animal"], cat=meta["categorie"],
                        img=meta["image"], alt=meta["image_alt"], s=meta["resume"],
                        tags=[t.strip() for t in meta.get("mots_cles", "").split(",") if t.strip()], body=body))
    return sorted(out, key=lambda a: a["d"], reverse=True)

A = load_articles()

CATS = {"sante": "Santé", "alimentation": "Alimentation", "comportement": "Comportement", "produits": "Produits", "toilettage": "Toilettage"}
SPL = {"chien": "Chien", "chat": "Chat", "both": "Chien et chat"}
MOIS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
e = html.escape

def fmt(d):
    y, m, j = map(int, d.split("-"))
    return f"{j} {MOIS[m-1]} {y}"

def img(a, w=720, r=""):
    """Adresse d'une image : redimensionnée par le CDN Shopify, ou locale (images/…)."""
    u = a["img"]
    if u.startswith("http"):
        return u + ("&" if "?" in u else "?") + f"width={w}"
    return r + u.lstrip("/")

def abs_img(a, w=1200):
    """Adresse complète (partage sur les réseaux, données structurées)."""
    u = img(a, w)
    return u if u.startswith("http") else SITE + "/" + u

PAW = '<svg width="22" height="22" viewBox="0 0 24 24" fill="#EBB54F" aria-hidden="true"><ellipse cx="6" cy="9" rx="2.2" ry="2.8"/><ellipse cx="10.2" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="14.8" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="19" cy="9" rx="2.2" ry="2.8"/><path d="M12.5 11c-3.2 0-6.2 3.6-6.2 6.4 0 2 1.6 3 3.4 3 1.2 0 2-.6 2.8-.6s1.6.6 2.8.6c1.8 0 3.4-1 3.4-3 0-2.8-3-6.4-6.2-6.4z"/></svg>'
ARROW = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

NAV = [("index.html", "Accueil", "home"), ("chiens.html", "Chiens", "chiens"), ("chats.html", "Chats", "chats"),
       ("conseils.html", "Conseils", "conseils"), ("aliments-dangereux.html", "Aliments à éviter", "aliments"),
       ("recommandations.html", "Recommandations", "reco"), ("a-propos.html", "À propos", "apropos")]
MOBILE_EXTRA = [("contact.html", "Nous joindre", "contact")]

def logo(r):
    return (f'<a href="{r}index.html" class="logo" aria-label="Poil &amp; Museau, accueil">'
            f'<img src="{r}images/logo-illustration.webp" alt="" width="72" height="46">'
            '<span class="wm"><span class="w1">Poil</span><span class="amp">&amp;</span><span class="w2">Museau</span></span></a>')

def header(r, active):
    cur = lambda k: ' aria-current="page"' if k == active else ""
    links = "".join(f'<a href="{r}{h}"{cur(k)}>{l}</a>' for h, l, k in NAV)
    mob = "".join(f'<a href="{r}{h}"{cur(k)}>{l}</a>' for h, l, k in NAV + MOBILE_EXTRA)
    return f'''<a class="skip" href="#contenu">Aller au contenu</a>
<div id="progress" aria-hidden="true"></div>
<header class="site">
  <div class="wrap nav">
    {logo(r)}
    <nav class="links" aria-label="Navigation principale">{links}</nav>
    <div class="nav-right">
      <button class="icon-btn" id="theme" type="button" aria-label="Changer le thème clair ou sombre"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
      <button class="icon-btn burger" id="burger" type="button" aria-label="Ouvrir le menu" aria-expanded="false" aria-controls="mm"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg></button>
    </div>
  </div>
  <nav class="mobile-menu" id="mm" hidden aria-label="Menu mobile">{mob}</nav>
</header>'''

def footer(r):
    return f'''<footer class="site">
  <div class="wrap">
    <div class="fgrid">
      <div>
        <a href="{r}index.html" aria-label="Poil &amp; Museau, accueil"><img class="flogo" src="{r}images/logo.webp" alt="Poil &amp; Museau, complice de vos animaux" width="240" height="183" loading="lazy"></a>
        <p class="meta" style="margin-top:12px;max-width:320px">Conseils et produits choisis pour le bien-être des chiens et des chats. Fait au Québec.</p>
        <p style="margin-top:16px;font-weight:700">info@poiletmuseau.com</p>
      </div>
      <div><h2>Chiens</h2><ul>
        <li><a href="{r}chiens.html#sante">Santé</a></li><li><a href="{r}chiens.html#alimentation">Alimentation</a></li>
        <li><a href="{r}chiens.html#comportement">Comportement</a></li><li><a href="{r}chiens.html#toilettage">Toilettage</a></li>
        <li><a href="{r}chiens.html#produits">Produits</a></li></ul></div>
      <div><h2>Chats</h2><ul>
        <li><a href="{r}chats.html#sante">Santé</a></li><li><a href="{r}chats.html#comportement">Comportement</a></li>
        <li><a href="{r}chats.html#produits">Produits</a></li><li><a href="{r}aliments-dangereux.html">Aliments à éviter</a></li></ul></div>
      <div><h2>Infos</h2><ul>
        <li><a href="{r}a-propos.html">À propos</a></li><li><a href="{r}contact.html">Nous joindre</a></li>
        <li><a href="{r}divulgation.html">Divulgation d'affiliation</a></li>
        <li><a href="{r}politique-de-confidentialite.html">Politique de confidentialité</a></li>
        <li><a href="{r}conditions-utilisation.html">Conditions d'utilisation</a></li></ul></div>
    </div>
    <div class="bottom"><span>© <span id="yr">2026</span> Poil &amp; Museau. Tous droits réservés.</span><span>Nos conseils ne remplacent pas l'avis d'un vétérinaire.</span></div>
  </div>
</footer>
<button class="icon-btn" id="top" type="button" aria-label="Retour en haut"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg></button>'''

def page(path, title, desc, body, active="", image=None, jsonld=None, extra_head=""):
    depth = path.count("/")
    r = "../" * depth
    canon = SITE + "/" + ("" if path == "index.html" else path[:-5])
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    full_title = title if title.startswith("Poil & Museau") else f"{title} | Poil & Museau"
    og_img = image or abs_img(A[0])
    doc = f'''<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{"article" if path.startswith("articles/") else "website"}">
<meta property="og:locale" content="fr_CA">
<meta property="og:site_name" content="Poil &amp; Museau">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{e(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="{r}images/favicon.png">
<link rel="apple-touch-icon" href="{r}images/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,400..800,50..100&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/style.css">
<script src="{r}assets/site.js"></script>
{extra_head}{ld}
</head>
<body>
{header(r, active)}
<main id="contenu">
{body}
</main>
{footer(r)}
</body>
</html>
'''
    dest = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(doc)
    PAGES.append(canon)

PAGES = []

def card(a, r):
    return f'''<a class="card" href="{r}articles/{a["h"]}.html" data-sp="{a["sp"]}" data-cat="{a["cat"]}">
  <div class="thumb"><img loading="lazy" src="{img(a, r=r)}" alt="{e(a["alt"])}" width="720" height="495"><span class="tag t-{a["sp"]}">{SPL[a["sp"]]}</span></div>
  <div class="cb"><span class="cat-l">{CATS[a["cat"]]}</span><h3>{e(a["t"])}</h3><p>{e(a["s"])}</p>
  <div class="foot"><span>{fmt(a["d"])}</span><span class="read">Lire →</span></div></div></a>'''

def crumbs(r, items):
    out = [f'<a href="{r}index.html">Accueil</a>']
    for href, label in items:
        out.append('<span aria-hidden="true">/</span>')
        out.append(f'<a href="{r}{href}">{e(label)}</a>' if href else f'<span aria-current="page">{e(label)}</span>')
    return '<nav class="crumbs" aria-label="Fil d\'Ariane">' + "".join(out) + "</nav>"

def crumbs_ld(items):
    lst = [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"}]
    for i, (href, label) in enumerate(items, 2):
        it = {"@type": "ListItem", "position": i, "name": label}
        if href: it["item"] = SITE + "/" + href[:-5]
        lst.append(it)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lst}

def list_tools(articles, show_species):
    counts = {k: sum(1 for a in articles if a["cat"] == k) for k in CATS}
    chips = '<button class="chip on" type="button" data-cat="all" aria-pressed="true">Tout<span class="n">' + str(len(articles)) + '</span></button>'
    chips += "".join(f'<button class="chip" type="button" data-cat="{k}" aria-pressed="false">{v}<span class="n">{counts[k]}</span></button>' for k, v in CATS.items() if counts[k])
    seg = ('<div class="seg" id="seg" role="group" aria-label="Filtrer par animal"><span class="pill" aria-hidden="true"></span>'
           '<button type="button" data-sp="all" class="on" aria-pressed="true">Tous</button><button type="button" data-sp="chien" aria-pressed="false">🐶 Chiens</button>'
           '<button type="button" data-sp="chat" aria-pressed="false">🐱 Chats</button></div>') if show_species else ""
    return f'''<div class="toolbar">
  <div class="left">{seg}<div class="chips" id="chips" role="group" aria-label="Filtrer par sujet">{chips}</div></div>
  <label class="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="q" type="search" placeholder="Rechercher : harnais, litière, vomit…" aria-label="Rechercher un article"></label>
</div>
<p class="count-line" id="count" aria-live="polite">{len(articles)} articles</p>'''

def newsletter(r):
    return f'''<section class="block" style="padding-top:0"><div class="wrap"><div class="news reveal">
  <div><span class="kicker">Infolettre gratuite</span><h2 class="sec">Un conseil utile,<br><em>chaque lundi.</em></h2>
  <div class="perks"><span>✅ Le nouvel article de la semaine</span><span>✅ Le tableau comparatif des fontaines à eau offert</span><span>✅ Zéro pourriel, désabonnement en un clic</span></div></div>
  <form data-demo novalidate>
    <input id="nl-prenom" type="text" placeholder="Votre prénom" aria-label="Prénom" autocomplete="given-name">
    <input id="nl-courriel" type="email" required placeholder="votre@courriel.com" aria-label="Courriel" autocomplete="email">
    <button class="btn" type="submit">Je m'inscris 🐾</button>
    <p class="ok-msg" data-ok hidden>Merci! Surveillez votre boîte de réception. 💛</p>
    <small>Vos renseignements sont traités selon notre <a href="{r}politique-de-confidentialite.html" style="text-decoration:underline">politique de confidentialité</a> (Loi 25).</small>
  </form></div></div></section>'''

# Aliments
FOODS = [
 ("🍫","Chocolat","bad","À éviter","Contient de la théobromine, toxique pour les chiens et les chats. Plus il est foncé, plus il est dangereux."),
 ("🍇","Raisins et raisins secs","bad","À éviter","Ils peuvent causer une atteinte rénale chez le chien, même en petite quantité."),
 ("🧅","Oignon et ail","bad","À éviter","Crus, cuits ou en poudre, ils peuvent endommager les globules rouges. Les chats y sont particulièrement sensibles."),
 ("🍬","Xylitol","bad","À éviter","Cet édulcorant (gommes, certains beurres d'arachide « sans sucre ») peut provoquer une chute brutale de la glycémie chez le chien."),
 ("☕","Café et caféine","bad","À éviter","La caféine stimule le cœur et le système nerveux. Gardez tasses, capsules et grains hors de portée."),
 ("🍷","Alcool","bad","À éviter","Même une petite quantité peut causer une intoxication. Attention aux verres laissés sur une table basse."),
 ("🌰","Noix de macadamia","bad","À éviter","Elles peuvent causer faiblesse, tremblements et fièvre chez le chien."),
 ("🍞","Pâte crue à la levure","bad","À éviter","Elle gonfle dans l'estomac et produit de l'alcool en fermentant."),
 ("🥑","Avocat","care","Prudence","La chair est riche en gras et le noyau peut causer une obstruction. Mieux vaut s'abstenir."),
 ("🥛","Lait","care","Prudence","Beaucoup de chiens et de chats digèrent mal le lactose. Un peu peut causer diarrhée et inconfort."),
 ("🧀","Fromage","care","Prudence","Gras et souvent salé. Un tout petit morceau comme récompense, pas plus."),
 ("🦴","Os cuits","care","Prudence","Les os cuits peuvent se briser en éclats coupants. Ne les donnez pas."),
 ("🥕","Carotte","ok","Sécuritaire","Crue ou cuite, nature et coupée en morceaux : une gâterie croquante et faible en calories."),
 ("🍎","Pomme","ok","Sécuritaire","Sans le cœur ni les pépins, en petits morceaux."),
 ("🍗","Poulet cuit nature","ok","Sécuritaire","Sans assaisonnement, sans peau grasse et surtout sans os."),
 ("🍚","Riz cuit","ok","Sécuritaire","Nature, il se digère facilement."),
 ("🎃","Citrouille nature","ok","Sécuritaire","En purée nature, pas la garniture à tarte sucrée et épicée."),
 ("🫐","Bleuets","ok","Sécuritaire","Riches en antioxydants, en petite quantité. Une gâterie bien d'ici!"),
]
LVL_COLOR = {"bad": "#B5651D", "care": "#EBB54F", "ok": "#A9BA82"}

def foods_tool(r, heading_tag="h2", intro=True, extra_cta=""):
    btns = "".join(f'<button class="food" type="button" data-i="{i}" aria-pressed="false"><span class="lvl" style="background:{LVL_COLOR[f[2]]}" aria-hidden="true"></span><span aria-hidden="true">{f[0]}</span>{e(f[1])}</button>' for i, f in enumerate(FOODS))
    data = json.dumps([dict(e=f[0], n=f[1], l=f[2], v=f[3], d=f[4]) for f in FOODS], ensure_ascii=False)
    cls = "display" if heading_tag == "h1" else "sec"
    return f'''<div class="checker reveal">
  <svg class="paw-bg" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><ellipse cx="6" cy="9" rx="2.2" ry="2.8"/><ellipse cx="10.2" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="14.8" cy="5.2" rx="2.2" ry="2.8"/><ellipse cx="19" cy="9" rx="2.2" ry="2.8"/><path d="M12.5 11c-3.2 0-6.2 3.6-6.2 6.4 0 2 1.6 3 3.4 3 1.2 0 2-.6 2.8-.6s1.6.6 2.8.6c1.8 0 3.4-1 3.4-3 0-2.8-3-6.4-6.2-6.4z"/></svg>
  <div class="checker-grid">
    <div><span class="kicker">Outil rapide</span><{heading_tag} class="{cls}">Mon animal peut-il <em>manger ça?</em></{heading_tag}>
      <p style="opacity:.85;margin-top:14px;max-width:440px">Touchez un aliment pour savoir s'il est sécuritaire pour votre chien ou votre chat.</p>
      <div class="foods" id="foods" data-base="{r}">{btns}</div>
      <div class="legend"><span><i class="lvl" style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#B5651D"></i>À éviter</span><span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#EBB54F"></i>Prudence</span><span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#A9BA82"></i>Sécuritaire</span></div>
      {extra_cta}
    </div>
    <div class="verdict" id="verdict" aria-live="polite"><div class="big" aria-hidden="true">🍫</div><span class="badge bad">⛔ À éviter</span><h3>Chocolat</h3><p>{FOODS[0][4]}</p><small>Touchez un autre aliment pour voir son verdict.</small></div>
  </div>
</div>
<script>window.PM_FOODS={data};</script>'''

# ---------- ACCUEIL ----------
def build_home():
    r = ""
    f = A[0]
    latest = "".join(card(a, r) for a in A[1:7])
    facts = [("🍟","Pourquoi les pattes de mon chien sentent-elles les chips?","Des bactéries et levures naturellement présentes sur les coussinets produisent cette odeur. C'est normal, sauf si elle devient forte ou s'accompagne de rougeurs.","pattes-chien-sentent-chips"),
             ("🧶","Pourquoi mon chat pétrit-il ma couverture?","Ce geste remonte à l'allaitement. À l'âge adulte, il est souvent associé au confort et à la détente.","pourquoi-chat-fait-des-pattes"),
             ("🐕","Pourquoi mon chien penche-t-il la tête?","Les recherches suggèrent un lien avec l'attention portée aux mots qu'il reconnaît, et avec l'audition et la vision.","pourquoi-chien-penche-tete")]
    facts_html = "".join(f'<div class="flip reveal" tabindex="0" role="button" aria-label="Retourner la carte : {e(q)}"><div class="in"><div class="face front"><span class="e" aria-hidden="true">{em}</span><span class="q">{e(q)}</span><small>Touchez pour retourner ↻</small></div><div class="face back"><p>{e(ans)}</p><a href="articles/{h}.html">Lire l\'article complet →</a></div></div></div>' for em, q, ans, h in facts)
    by = {a["h"]: a for a in A}
    p1, p2, p3 = by["pourquoi-chien-penche-tete"], by["pourquoi-chat-fait-des-pattes"], by["choisir-nourriture-chien"]
    dog_img = by["comment-choisir-le-bon-lit-pour-votre-chien"]; cat_img = by["chat-boit-il-assez-deau"]
    nd = sum(1 for a in A if a["sp"] in ("chien","both")); nc = sum(1 for a in A if a["sp"] in ("chat","both"))
    body = f'''
<section class="hero" data-paws>
  <div class="blob b1" aria-hidden="true"></div><div class="blob b2" aria-hidden="true"></div><div class="blob b3" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div>
      <span class="eyebrow"><span class="dot" aria-hidden="true"></span> Nouvel article chaque lundi</span>
      <h1 class="display">Des conseils qui ont du <span class="swap" id="swap"><span>chien</span></span><br>pour des compagnons <span class="underline">bien dans leur poil.<svg viewBox="0 0 300 16" preserveAspectRatio="none" aria-hidden="true"><path d="M3 11 C 70 3, 150 3, 297 9"/></svg></span></h1>
      <p class="lead">Santé, alimentation, comportement, toilettage : des guides clairs, vérifiés et sans jargon pour mieux comprendre votre chien ou votre chat, et choisir les bons produits sans vous perdre dans le marketing.</p>
      <div class="cta-row">
        <a href="conseils.html" class="btn btn-primary">Explorer les conseils {ARROW}</a>
        <a href="aliments-dangereux.html" class="btn btn-ghost">Mon animal peut-il manger ça?</a>
      </div>
      <div class="stats">
        <div class="stat"><b data-count="{len(A)}">{len(A)}</b><small>guides et articles</small></div>
        <div class="stat"><b data-count="{nd}">{nd}</b><small>conseils pour chiens</small></div>
        <div class="stat"><b data-count="{nc}">{nc}</b><small>conseils pour chats</small></div>
      </div>
    </div>
    <div class="collage" aria-hidden="true">
      <div class="polaroid p1"><div class="imgbox"><img src="{img(p1,700)}" alt=""></div><div class="cap">Pourquoi penche-t-il la tête?</div></div>
      <div class="polaroid p2"><div class="imgbox"><img src="{img(p2,700)}" alt=""></div><div class="cap">Le mystère du pétrissage</div></div>
      <div class="polaroid p3"><div class="imgbox"><img src="{img(p3,700)}" alt=""></div><div class="cap">Bien lire l'étiquette</div></div>
      <div class="sticker"><span>Vérifié.<br>Expliqué.<br>Choisi 🐾</span></div>
    </div>
  </div>
</section>
<div class="marquee" aria-hidden="true"><div class="track"><span>Santé ✦ Alimentation ✦ Comportement ✦ Toilettage ✦ Guides d'achat ✦ Bien-être ✦</span><span>Santé ✦ Alimentation ✦ Comportement ✦ Toilettage ✦ Guides d'achat ✦ Bien-être ✦</span></div></div>

<section class="block"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Par où commencer?</span><h2 class="sec">Votre compagnon,<br><em>votre parcours.</em></h2></div>
  <p class="lead">Choisissez votre animal pour voir les conseils qui le concernent.</p></div>
  <div class="species">
    <a class="sp dog reveal" href="chiens.html"><div><h3>Chiens</h3><p>Promenades, gâteries, bains, harnais et petits comportements attachants.</p></div>
      <div class="pills"><span>Santé</span><span>Alimentation</span><span>Comportement</span><span>Toilettage</span></div>
      <div class="arrow">{ARROW}</div><img src="{img(dog_img,600)}" alt="{e(dog_img["alt"])}" loading="lazy"></a>
    <a class="sp cat reveal" href="chats.html"><div><h3>Chats</h3><p>Hydratation, litière, soins dentaires et langage félin enfin décodé.</p></div>
      <div class="pills"><span>Santé</span><span>Produits</span><span>Comportement</span></div>
      <div class="arrow">{ARROW}</div><img src="{img(cat_img,600)}" alt="{e(cat_img["alt"])}" loading="lazy"></a>
  </div>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Tout frais</span><h2 class="sec">Le dernier <em>article</em></h2></div></div>
  <a class="featured reveal" href="articles/{f["h"]}.html">
    <div class="img"><img src="{img(f,1200)}" alt="{e(f["alt"])}"></div>
    <div class="body"><span class="tag t-{f["sp"]}" style="align-self:flex-start">{SPL[f["sp"]]} · {CATS[f["cat"]]}</span>
      <h3>{e(f["t"])}</h3><p class="lead" style="font-size:1.02rem">{e(f["s"])}</p>
      <span class="meta">{fmt(f["d"])}</span><span class="btn btn-primary" style="align-self:flex-start">Lire l'article {ARROW}</span></div>
  </a>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Récemment publiés</span><h2 class="sec">Nos derniers <em>conseils</em></h2></div>
  <a class="link-arrow" href="conseils.html">Voir les {len(A)} articles →</a></div>
  <div class="grid">{latest}</div>
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  {foods_tool(r, extra_cta='<p style="margin-top:22px"><a class="link-arrow" style="color:var(--butter)" href="aliments-dangereux.html">Voir la liste complète →</a></p>')}
</div></section>

<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Le saviez-vous?</span><h2 class="sec">Petites questions, <em>grandes réponses</em></h2></div><p class="meta">Touchez une carte pour la retourner</p></div>
  <div class="facts">{facts_html}</div>
</div></section>
{newsletter(r)}'''
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Poil & Museau", "url": SITE + "/", "inLanguage": "fr-CA",
           "description": "Conseils, guides d'achat et produits choisis avec soin pour le bien-être des chiens et des chats."},
          {"@context": "https://schema.org", "@type": "Organization", "name": "Poil & Museau", "url": SITE + "/", "email": "info@poiletmuseau.com"}]
    page("index.html", "Poil & Museau : conseils pour chiens et chats",
         "Conseils, guides d'achat et produits choisis avec soin pour le bien-être des chiens et des chats. Santé, alimentation, comportement et toilettage, en français d'ici.",
         body, "home", jsonld=ld)

# ---------- CHIENS / CHATS ----------
def build_species(sp):
    r = ""
    dog = sp == "chien"
    arts = [a for a in A if a["sp"] in (sp, "both")]
    path = "chiens.html" if dog else "chats.html"
    label = "Chiens" if dog else "Chats"
    hero_a = next(a for a in A if a["h"] == ("toiletter-chien-maison" if dog else "regard-chat-signification-selon-situation"))
    intro = ("Promenades, gâteries, bains, harnais, petits comportements attachants : tout ce qu'il faut pour mieux comprendre votre chien et en prendre soin au quotidien."
             if dog else "Hydratation, litière, soins dentaires, pétrissage et regards insistants : des réponses claires pour mieux comprendre votre chat.")
    grid = "".join(card(a, r) for a in arts)
    guides = [a for a in arts if a["cat"] == "produits"][:3]
    guides_html = "".join(f'<a class="rc reveal" href="articles/{a["h"]}.html"><span class="ic" style="background:{"#FBE7B5" if dog else "#DDE5C8"}" aria-hidden="true">{"🦮" if dog else "🐈"}</span><h3>{e(a["t"])}</h3><p>{e(a["s"])}</p><span class="go">Voir le guide →</span></a>' for a in guides)
    body = f'''
<section class="page-hero {"dog" if dog else "cat"}"><div class="wrap split">
  <div>{crumbs(r, [(None, label)])}
    <h1 class="display">Tout pour votre <em>{"chien" if dog else "chat"}</em></h1>
    <p class="lead">{intro}</p>
    <div class="cta-row"><a class="btn btn-ghost" style="border-color:#2B1E14;color:#2B1E14" href="#liste">{len(arts)} conseils à lire ↓</a></div>
  </div>
  <div class="hero-photo"><img src="{img(hero_a,900)}" alt="{e(hero_a["alt"])}"></div>
</div></section>
<section class="block" id="liste"><div class="wrap">
  {list_tools(arts, False)}
  <div class="grid" data-list>{grid}</div>
  <div class="empty" id="empty" hidden><div style="font-size:3rem" aria-hidden="true">🐾</div><p>Aucun article ne correspond. Essayez un autre mot.</p></div>
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Guides d'achat</span><h2 class="sec">Bien choisir pour votre <em>{"chien" if dog else "chat"}</em></h2></div>
  <a class="link-arrow" href="recommandations.html">Toutes nos recommandations →</a></div>
  <div class="reco" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))">{guides_html}</div>
</div></section>
{newsletter(r)}'''
    desc = (f"Conseils pour chiens : santé, alimentation, comportement, toilettage et guides d'achat. {len(arts)} articles clairs et vérifiés."
            if dog else f"Conseils pour chats : santé, hydratation, comportement et guides d'achat. {len(arts)} articles clairs et vérifiés.")
    page(path, f"Conseils pour {'chiens' if dog else 'chats'}", desc, body, "chiens" if dog else "chats",
         image=abs_img(hero_a), jsonld=[crumbs_ld([(None, label)])])

# ---------- CONSEILS ----------
def build_conseils():
    r = ""
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--butter);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs(r, [(None, "Conseils")])}
  <span class="kicker">La bibliothèque</span><h1 class="display">Tous nos <em>conseils</em></h1>
  <p class="lead">{len(A)} articles pour chiens et chats. Filtrez par animal ou par sujet, ou cherchez un mot.</p></div></div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  {list_tools(A, True)}
  <div class="grid" data-list>{"".join(card(a, r) for a in A)}</div>
  <div class="empty" id="empty" hidden><div style="font-size:3rem" aria-hidden="true">🐾</div><p>Aucun article ne correspond. Essayez un autre mot.</p></div>
</div></section>
{newsletter(r)}'''
    page("conseils.html", "Tous nos conseils", f"Les {len(A)} conseils de Poil & Museau pour chiens et chats : santé, alimentation, comportement, toilettage et guides d'achat.",
         body, "conseils", jsonld=[crumbs_ld([(None, "Conseils")])])

# ---------- ALIMENTS ----------
def build_aliments():
    r = ""
    rows = "".join(f'<tr><td><span aria-hidden="true">{f[0]}</span> <strong>{e(f[1])}</strong></td><td><span class="badge {f[2]}" style="padding:4px 10px;border-radius:999px;font-weight:800;font-size:.75rem;text-transform:uppercase;white-space:nowrap">{f[3]}</span></td><td>{e(f[4])}</td></tr>' for f in FOODS)
    by = {a["h"]: a for a in A}
    rel = [by["aliments-dangereux-chien-chat"], by["que-faire-si-mon-chien-ou-mon-chat-mange-un-aliment-dangereux"], by["chien-chat-vomit-quand-sinquieter"]]
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f"Mon chien ou mon chat peut-il manger : {f[1].lower()}?", "acceptedAnswer": {"@type": "Answer", "text": f"{f[3]}. {f[4]}"}} for f in FOODS]}
    body = f'''
<section class="block" style="padding-top:24px"><div class="wrap">
  {crumbs(r, [(None, "Aliments à éviter")])}
  {foods_tool(r, "h1")}
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Aide-mémoire</span><h2 class="sec">La liste <em>complète</em></h2></div>
  <p class="lead">À garder sous la main, ou à montrer à la gardienne avant de partir en vacances.</p></div>
  <div class="table-scroll reveal"><table class="food-table"><thead><tr><th scope="col">Aliment</th><th scope="col">Verdict</th><th scope="col">Pourquoi</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="vet-note"><span aria-hidden="true">🚨</span><span><strong>En cas d'ingestion d'un aliment à éviter</strong>, appelez rapidement votre vétérinaire ou une clinique d'urgence. Ne faites pas vomir votre animal sans avis professionnel.</span></div>
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Pour aller plus loin</span><h2 class="sec">À lire <em>aussi</em></h2></div></div>
  <div class="grid">{"".join(card(a, r) for a in rel)}</div>
</div></section>'''
    page("aliments-dangereux.html", "Mon animal peut-il manger ça?", "Chocolat, raisins, oignon, xylitol… Vérifiez en un clic si un aliment est sécuritaire pour votre chien ou votre chat, et que faire en cas d'ingestion.",
         body, "aliments", image=abs_img(rel[0]), jsonld=[crumbs_ld([(None, "Aliments à éviter")]), faq])

# ---------- RECOMMANDATIONS ----------
RECO = [
 ("💧","#DDE5C8","chat","Fontaine à eau pour chat",["Matériau facile à laver","Filtre accessible et abordable","Pompe silencieuse"],"fontaine-eau-chat-plastique-ceramique-acier-inoxydable"),
 ("🧹","#DDE5C8","chat","Litière autonettoyante",["Taille adaptée à votre chat","Capteurs de présence fiables","Entretien réel à prévoir"],"litiere-autonettoyante-chat"),
 ("🧴","#DDE5C8","chat","Les essentiels du chat",["Litière et emplacement","Arbre à chat et griffoir","Jouets d'activité"],"les-essentiels-indispensables-pour-chat"),
 ("🦮","#FBE7B5","chien","Harnais pour chien",["Type adapté à sa démarche","Ajustement aux épaules","Points de réglage multiples"],"comment-choisir-harnais-pour-chien"),
 ("🛏️","#FBE7B5","chien","Lit pour chien",["Taille selon sa position de sommeil","Housse lavable","Rebords ou non selon ses habitudes"],"comment-choisir-le-bon-lit-pour-votre-chien"),
 ("🛁","#FBE7B5","chien","Toilettage à la maison",["Brosse adaptée au pelage","Coupe-griffes sécuritaire","Shampoing pour chien"],"toiletter-chien-maison"),
 ("🧳","#FBE7B5","chien","Sac de voyage du chien",["Bol pliable et eau","Trousse de premiers soins","Copie du carnet de santé"],"sac-voyage-chien-vacances"),
 ("🥣","#FBE7B5","chien","Nourriture pour chien",["Mention « complète et équilibrée »","Stade de vie indiqué","Fabricant transparent"],"choisir-nourriture-chien"),
]
def build_reco():
    r = ""
    cards = "".join(f'<a class="rc reveal" href="articles/{h}.html" data-sp="{sp}"><span class="ic" style="background:{bg}" aria-hidden="true">{ic}</span><span class="tag t-{sp}" style="align-self:flex-start">{SPL[sp]}</span><h3>{e(t)}</h3><ul>{"".join(f"<li>{e(c)}</li>" for c in crit)}</ul><span class="go">Lire le guide →</span></a>' for ic, bg, sp, t, crit, h in RECO)
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--blush);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs(r, [(None, "Recommandations")])}
  <span class="kicker">Guides d'achat</span><h1 class="display">Nos <em>recommandations</em></h1>
  <p class="lead">Avant de recommander un produit, on explique comment le choisir. Chaque guide présente les critères qui comptent vraiment, puis des modèles à considérer.</p></div></div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="reco four">{cards}</div>
  <p class="disclose reveal"><span aria-hidden="true">ℹ️</span><span>Certains liens de nos guides sont des liens d'affiliation, notamment avec le programme Partenaires d'Amazon. Si vous achetez par leur entremise, Poil &amp; Museau peut recevoir une commission, sans frais supplémentaires pour vous. <a href="divulgation.html">Lire notre divulgation</a></span></p>
</div></section>
<section class="block" style="padding-top:0"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Notre méthode</span><h2 class="sec">Comment on <em>choisit</em></h2></div></div>
  <div class="values">
    <div class="value reveal"><span class="ic" aria-hidden="true">🔍</span><h3>On part du besoin</h3><p>On commence par ce dont votre animal a besoin, pas par le produit à vendre.</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">📚</span><h3>On s'appuie sur des sources</h3><p>Organisations vétérinaires, écoles de médecine vétérinaire et références reconnues.</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">🤝</span><h3>On reste transparents</h3><p>Les liens d'affiliation sont toujours identifiés et ne changent pas nos critères.</p></div>
  </div>
</div></section>
{newsletter(r)}'''
    page("recommandations.html", "Nos recommandations", "Guides d'achat pour chiens et chats : fontaine à eau, litière autonettoyante, harnais, lit, toilettage et nourriture. Les critères qui comptent vraiment.",
         body, "reco", jsonld=[crumbs_ld([(None, "Recommandations")])])

# ---------- À PROPOS ----------
def build_apropos():
    r = ""
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--sky);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs(r, [(None, "À propos")])}
  <span class="kicker">À propos</span><h1 class="display">Parce que leur bonheur <em>compte autant que le nôtre</em></h1></div></div></section>
<div class="wrap"><div class="text-page">
  <div class="prose">
    <p><strong>Les chiens et les chats ne sont pas simplement des animaux de compagnie.</strong> Ils partagent nos vies, nos habitudes et occupent une place essentielle dans notre quotidien.</p>
    <p>Poil &amp; Museau est un site indépendant consacré aux chiens et aux chats. Il a été pensé pour vous aider à faire des choix éclairés, sans perdre de temps ni vous compliquer la vie.</p>
    <p>Vous y trouverez des conseils pratiques pour améliorer leur bien-être jour après jour, ainsi que des produits soigneusement sélectionnés : alimentation, accessoires utiles, hygiène et confort.</p>
    <h2>Notre mission et notre approche</h2>
    <p>Notre objectif est de partager des conseils pratiques, des informations utiles et des recommandations de produits afin d'aider les propriétaires à prendre soin de leurs compagnons.</p>
    <p>Les contenus sont rédigés avec soin à partir de recherches, de références reconnues, de recommandations d'organisations spécialisées et d'informations accessibles au grand public.</p>
    <p><em><strong>Prenez soin de lui simplement, avec ce qu'il y a de mieux. 🐾</strong></em></p>
  </div>
  <aside class="side-card reveal"><img src="images/logo.webp" alt="Logo Poil &amp; Museau, complice de vos animaux" width="300" height="229" style="margin:-6px auto 4px;width:100%;max-width:300px"><h2>Une question?</h2><p class="meta">Une suggestion d'article ou une question sur un produit recommandé? Écrivez-nous.</p>
    <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">Copier</button></div>
    <a class="link-arrow" href="contact.html">Page Nous joindre →</a></aside>
</div>
<section class="block" style="padding-top:0">
  <div class="sec-head reveal"><div><span class="kicker">Ce qui nous guide</span><h2 class="sec">Trois <em>principes</em></h2></div></div>
  <div class="values">
    <div class="value reveal"><span class="ic" aria-hidden="true">🤝</span><h3>Transparence</h3><p>Les liens d'affiliation sont identifiés, et nos critères de sélection sont expliqués.</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">💛</span><h3>Bien-être animal</h3><p>Chaque conseil part de ce qui est bon pour l'animal, pas de ce qui se vend le mieux.</p></div>
    <div class="value reveal"><span class="ic" aria-hidden="true">✨</span><h3>Simplicité</h3><p>Des explications claires, sans jargon, qu'on peut appliquer dès aujourd'hui.</p></div>
  </div>
</section></div>'''
    page("a-propos.html", "À propos", "Poil & Museau est un site indépendant consacré aux chiens et aux chats : conseils pratiques et produits choisis avec transparence pour leur bien-être.",
         body, "apropos", jsonld=[crumbs_ld([(None, "À propos")])])

# ---------- CONTACT ----------
def build_contact():
    r = ""
    body = f'''
<section class="page-hero"><div class="blob" style="width:380px;height:380px;background:var(--butter);top:-160px;right:-60px" aria-hidden="true"></div>
<div class="wrap"><div>{crumbs(r, [(None, "Nous joindre")])}
  <span class="kicker">Nous joindre</span><h1 class="display">Écrivez-<em>nous</em></h1>
  <p class="lead">Merci de votre visite chez Poil &amp; Museau 🐾 Une question, une idée d'article ou un commentaire sur un produit? On vous répond avec plaisir.</p></div></div></section>
<div class="wrap"><div class="text-page">
  <form class="form side-card" data-demo style="padding:30px">
    <label for="c-nom">Nom<input id="c-nom" type="text" autocomplete="name" required></label>
    <label for="c-courriel">Courriel<input id="c-courriel" type="email" autocomplete="email" required></label>
    <label for="c-sujet">Sujet<select id="c-sujet"><option>Question sur un article</option><option>Suggestion d'article</option><option>Question sur un produit recommandé</option><option>Partenariat</option><option>Autre</option></select></label>
    <label for="c-msg">Message<textarea id="c-msg" required></textarea></label>
    <button class="btn btn-primary" type="submit" style="justify-content:center">Envoyer le message</button>
    <p class="notice" data-ok hidden>Merci! Votre message a bien été pris en note. 💛</p>
  </form>
  <aside style="display:flex;flex-direction:column;gap:16px">
    <div class="side-card"><h2>Par courriel</h2>
      <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">Copier</button></div></div>
    <div class="side-card"><h2>Une commande?</h2><p class="meta">Nous recommandons des produits par l'entremise de partenaires de confiance. Pour une question sur une commande, une livraison ou un retour, communiquez directement avec le marchand concerné.</p>
      <a class="link-arrow" href="divulgation.html">Notre divulgation d'affiliation →</a></div>
  </aside>
</div></div>'''
    page("contact.html", "Nous joindre", "Une question, une idée d'article ou un commentaire? Écrivez à Poil & Museau à info@poiletmuseau.com.",
         body, "contact", jsonld=[crumbs_ld([(None, "Nous joindre")])])

# ---------- DIVULGATION ----------
def build_divulgation():
    r = ""
    body = f'''
<section class="page-hero"><div class="wrap"><div>{crumbs(r, [(None, "Divulgation d'affiliation")])}
  <span class="kicker">Transparence</span><h1 class="display">Divulgation <em>d'affiliation</em></h1></div></div></section>
<div class="wrap"><div class="text-page">
  <div class="prose">
    <p>Chez <strong>Poil &amp; Museau</strong> 🐾, je prends le temps de sélectionner avec soin des produits pour le bien-être de vos compagnons.</p>
    <p>Certains liens présents sur ce site peuvent être des liens d'affiliation, notamment par l'entremise du programme Partenaires d'Amazon. Cela signifie que je peux recevoir une commission si vous effectuez un achat par ces liens, sans frais supplémentaires pour vous.</p>
    <p class="tip"><strong>En tant que Partenaire d'Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</strong></p>
    <p>💛 Ces recommandations sont faites en toute transparence et reflètent mes choix personnels, basés sur la qualité, la fiabilité et l'intérêt pour vos animaux.</p>
    <p>Je vous remercie sincèrement de soutenir mon travail et de contribuer à faire vivre cette plateforme.</p>
  </div>
  <aside class="side-card"><h2>Comment reconnaître un lien d'affiliation?</h2><p class="meta">Dans nos articles, les produits recommandés sont présentés dans un encadré pointillé, comme celui-ci :</p>
    <div class="prose" style="font-size:.95rem"><div class="aff"><p>👉 <strong>Voir le produit recommandé</strong></p></div></div></aside>
</div></div>'''
    page("divulgation.html", "Divulgation d'affiliation", "Poil & Museau participe au programme Partenaires d'Amazon. Comment fonctionnent nos liens d'affiliation et comment les reconnaître.",
         body, "", jsonld=[crumbs_ld([(None, "Divulgation d'affiliation")])])

# ---------- ARTICLES ----------
def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFD", re.sub(r"<[^>]+>", "", html.unescape(s)))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "section"

def clean_body(b):
    b = re.sub(r"<meta[^>]*>", "", b)
    b = re.sub(r'\sdata-[\w-]+="[^"]*"', "", b)
    b = re.sub(r'\sstyle="[^"]*"', "", b)
    # Chaque H2 reçoit une ancre stable pour la table des matières
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
    b = re.sub(r'<a ([^>]*href="https://(?:amzn\.to|www\.amazon\.ca)[^"]*"[^>]*)>',
               lambda m: "<a " + re.sub(r'\srel="[^"]*"', "", m.group(1)) + ' rel="nofollow sponsored noopener">', b)
    b = re.sub(r"<table>", '<div class="tbl"><table>', b); b = re.sub(r"</table>", "</table></div>", b)
    b = re.sub(r"<p>\s*(&nbsp;| )?\s*</p>", "", b)
    return b

def related(a, n=3):
    same = [x for x in A if x is not a and (x["sp"] == a["sp"] or "both" in (x["sp"], a["sp"])) and x["cat"] == a["cat"]]
    more = [x for x in A if x is not a and x not in same and (x["sp"] == a["sp"] or "both" in (x["sp"], a["sp"]))]
    return (same + more)[:n]

def build_article(i, a):
    r = "../"
    has = bool(a["body"])
    sp_page = ("chiens.html", "Chiens") if a["sp"] == "chien" else ("chats.html", "Chats") if a["sp"] == "chat" else ("conseils.html", "Conseils")
    items = [sp_page, (None, a["t"])]
    newer = A[i-1] if i > 0 else None
    older = A[i+1] if i + 1 < len(A) else None
    if has:
        b = clean_body(a["body"]).replace('src="/images/', f'src="{r}images/').replace('href="/images/', f'href="{r}images/')
        words = len(re.sub(r"<[^>]+>", " ", b).split())
        mins = max(2, round(words / 200))
        heads = re.findall(r'<h2 id="([\w-]+)">(.*?)</h2>', b)
        skip = ("sources", "a-lire-aussi", "a-lire-egalement")
        toc = "".join(f'<li><a href="#{hid}">{re.sub(r"<[^>]+>", "", ht).strip()}</a></li>' for hid, ht in heads if hid not in skip and not re.sub(r"<[^>]+>", "", ht).strip().lower().startswith(("sources", "à lire")))
        main = f'<div class="prose">{b}</div>'
    else:
        mins = None; toc = ""
        main = f'''<div class="summary-box"><h2>L'essentiel</h2><p class="lead" style="max-width:none">{e(a["s"])}</p>
  <a class="btn btn-primary" style="align-self:flex-start" href="{r}conseils.html">Voir tous les conseils {ARROW}</a></div>'''
    aside = f'''<aside class="toc" aria-label="Dans cet article">{"<h2>Dans cet article</h2><ol>" + toc + "</ol>" if toc else "<h2>Partager</h2>"}
  <div class="share"><button class="btn btn-ghost" type="button" data-copy="url">Copier le lien</button></div></aside>'''
    rel = "".join(card(x, r) for x in related(a))
    pager = '<nav class="pager" aria-label="Articles précédent et suivant">'
    pager += f'<a href="{older["h"]}.html"><small>← Article précédent</small><b>{e(older["t"])}</b></a>' if older else "<span></span>"
    pager += f'<a class="next" href="{newer["h"]}.html"><small>Article suivant →</small><b>{e(newer["t"])}</b></a>' if newer else ""
    pager += "</nav>"
    meta = f'<span class="tag t-{a["sp"]}">{SPL[a["sp"]]}</span><span>{CATS[a["cat"]]}</span><span aria-hidden="true">·</span><time datetime="{a["d"]}">{fmt(a["d"])}</time>'
    if mins: meta += f'<span aria-hidden="true">·</span><span>{mins} min de lecture</span>'
    body = f'''
<article>
<div class="wrap art-hero"><div class="art-head">{crumbs(r, items)}
  <h1>{e(a["t"])}</h1><p class="lead">{e(a["s"])}</p><div class="art-meta">{meta}</div></div>
  <div class="art-cover"><img src="{img(a,1400,r)}" alt="{e(a["alt"])}" width="1400" height="700"></div>
</div>
<div class="wrap art-layout">
  <div style="min-width:0">{main}
    <div class="vet-note"><span aria-hidden="true">🩺</span><span>Cet article est informatif et ne remplace pas l'avis d'un vétérinaire. En cas de doute sur la santé de votre animal, consultez un professionnel.</span></div>
    {pager}
  </div>
  {aside}
</div>
</article>
<section class="block" style="padding-top:20px"><div class="wrap">
  <div class="sec-head reveal"><div><span class="kicker">Continuer la lecture</span><h2 class="sec">À lire <em>aussi</em></h2></div></div>
  <div class="grid">{rel}</div>
</div></section>
{newsletter(r)}'''
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["t"], "description": a["s"], "image": [abs_img(a)],
          "datePublished": a["d"], "inLanguage": "fr-CA", "author": {"@type": "Organization", "name": "Poil & Museau"},
          "publisher": {"@type": "Organization", "name": "Poil & Museau", "url": SITE + "/"},
          "mainEntityOfPage": SITE + "/articles/" + a["h"]}
    page(f"articles/{a['h']}.html", a["t"], re.sub(r"\s+", " ", a["s"]), body, "conseils", image=abs_img(a), jsonld=[ld, crumbs_ld(items)])
    return has

def build_404():
    body = f'''<section class="block"><div class="wrap" style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:18px">
  <div style="font-size:5rem" aria-hidden="true">🐾</div><h1 class="display">Cette page a <em>filé</em></h1>
  <p class="lead">Elle a peut-être suivi une odeur intéressante. Essayez plutôt l'une de ces pistes.</p>
  <div class="cta-row" style="justify-content:center"><a class="btn btn-primary" href="/index.html">Retour à l'accueil</a><a class="btn btn-ghost" href="/conseils.html">Tous les conseils</a></div>
</div></section>'''
    page("404.html", "Page introuvable", "Cette page n'existe pas ou a été déplacée.", body, "")
    PAGES.pop()

def build_text_pages():
    folder = os.path.join(CONTENT, "pages")
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".html"):
            continue
        meta, b = read_doc(os.path.join(folder, f))
        title = meta.get("titre", f[:-5]); slug_ = f[:-5]
        body = f'''
<section class="page-hero"><div class="wrap"><div>{crumbs("", [(None, title)])}
  <span class="kicker">{e(meta.get("surtitre", "Information"))}</span><h1 class="display">{e(title)}</h1>
  {f'<p class="lead">{e(meta["mise_a_jour"])}</p>' if meta.get("mise_a_jour") else ""}</div></div></section>
<div class="wrap"><div class="text-page"><div class="prose">{clean_body(b)}</div>
  <aside class="side-card"><h2>Une question?</h2><p class="meta">Écrivez-nous, nous vous répondrons dans les meilleurs délais.</p>
  <div class="copybox"><span>info@poiletmuseau.com</span><button class="btn btn-primary" type="button" data-copy="info@poiletmuseau.com">Copier</button></div>
  <a class="link-arrow" href="contact.html">Nous joindre →</a></aside></div></div>'''
        page(f"{slug_}.html", title, meta.get("description", title), body, "", jsonld=[crumbs_ld([(None, title)])])

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copytree(os.path.join(HERE, "static"), OUT, dirs_exist_ok=True)
if os.path.isdir(os.path.join(HERE, "images")):
    shutil.copytree(os.path.join(HERE, "images"), os.path.join(OUT, "images"), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".gitkeep", ".DS_Store"))

build_text_pages()
build_home(); build_species("chien"); build_species("chat"); build_conseils(); build_aliments()
build_reco(); build_apropos(); build_contact(); build_divulgation()
full = [a["h"] for i, a in enumerate(A) if build_article(i, a)]
build_404()

today = datetime.date.today().isoformat()
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in PAGES) + "</urlset>\n")
# Redirections des anciennes adresses Shopify vers les nouvelles pages.
# Une ligne explicite par ancienne adresse : aucune règle générique ne chevauche une règle précise.
redir = [f"/blogs/actualites/{a['h']} /articles/{a['h']} 301" for a in A]
redir += [f"/blogs/actualites/{a['h']}/ /articles/{a['h']} 301" for a in A]
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
          "/account / 301", "/account/* / 301", "/search /conseils 301"]
open(os.path.join(OUT, "_redirects"), "w").write("\n".join(redir) + "\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"Site généré dans {os.path.relpath(OUT)} : {len(PAGES)} pages · {len(full)} article(s) au texte complet : {', '.join(full)}")
