# Poil & Museau

Site de conseils pour chiens et chats : poiletmuseau.com.
Site statique généré par `build.py` (Python, aucune dépendance), hébergé sur Cloudflare.

## Organisation du dépôt

```
content/
  articles/      un fichier par article  →  /articles/<nom-du-fichier>
  pages/         pages légales (confidentialité, conditions)
images/
  articles/      photos des articles
static/
  assets/        style.css et site.js communs à toutes les pages
  images/        logo, icônes
scripts/
  rapatrier_images.py   copie les images de Shopify dans le dépôt
build.py         génère le site complet dans dist/
wrangler.jsonc   configuration Cloudflare
```

## Ajouter un article

1. Dépose la photo de couverture dans `images/articles/` (format .webp ou .jpg, environ 1600 px de large).
   Nom en minuscules, avec des tirets, sans accents ni espaces : `harnais-hiver.webp`.
2. Crée `content/articles/<adresse-de-l-article>.html`. Le nom du fichier devient l'adresse de la page.
3. Commence le fichier par cet en-tête, puis écris le texte en HTML :

```html
<!--
titre: Comment habiller son chien pour l'hiver
date: 2026-11-02
animal: chien
categorie: produits
image: /images/articles/harnais-hiver.webp
image_alt: Berger australien portant un manteau dans la neige
resume: Manteau, bottines, harnais : ce qu'il faut vraiment pour les grands froids.
mots_cles: hiver, manteau chien, bottines chien
-->
<p>Premier paragraphe…</p>
<h2>Premier intertitre</h2>
<p>…</p>
```

| Champ | Valeurs possibles |
|---|---|
| `animal` | `chien`, `chat` ou `both` (les deux) |
| `categorie` | `sante`, `alimentation`, `comportement`, `produits`, `toilettage` |
| `date` | format `AAAA-MM-JJ`. Les articles sont classés du plus récent au plus ancien |
| `brouillon` | facultatif : `oui` pour ne pas publier l'article |

Chaque `<h2>` apparaît automatiquement dans la table des matières de l'article.
Les liens Amazon (`amzn.to`, `amazon.ca`) reçoivent automatiquement `rel="nofollow sponsored"`.
Pour un encadré de produit recommandé : `<div class="aff">…</div>`. Pour un conseil : `<div class="tip">…</div>`.

4. Pousse sur GitHub : Cloudflare met le site à jour en une minute environ.

## Photos des articles

Pour l'instant, les articles affichent les photos hébergées chez Shopify.
**Avant de fermer la boutique Shopify**, lance une fois :
GitHub > onglet **Actions** > **Rapatrier les images Shopify** > **Run workflow**.
Toutes les photos sont alors copiées dans `images/articles/` et le contenu est mis à jour.

## Voir le site sur son ordinateur

```
python3 build.py
python3 -m http.server -d dist 8000
```
puis ouvrir http://localhost:8000

## Mise en ligne sur Cloudflare

1. Cloudflare > **Workers & Pages** > **Créer** > **Importer un dépôt** > `VizionRC/poil-et-museau`.
2. Commande de build : `python3 build.py` · Commande de déploiement : `npx wrangler deploy`.
3. Une fois le site en ligne sur l'adresse `*.workers.dev`, ajouter le domaine `poiletmuseau.com`
   dans **Paramètres > Domaines et routes**.

Les anciennes adresses Shopify (`/blogs/actualites/…`, `/pages/…`, `/policies/…`) sont redirigées
vers les nouvelles pages grâce au fichier `_redirects` généré par `build.py`.
