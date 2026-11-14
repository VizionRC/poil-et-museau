# Adaptations du prompt maître au site actuel (novembre 2026)

Ces décisions ont préséance sur le texte de docs/prompt-maitre.md lorsqu'il y a contradiction.

- **Table des matières** : ne pas insérer de table des matières dans le texte. Le site affiche automatiquement une table des matières à droite, construite à partir des intertitres H2. Chaque H2 doit avoir un `id` unique et `style="scroll-margin-top: 140px;"`.
- **Page « Nos recommandations »** : remplacée par l'onglet « Produits » : /recommandations (coups de cœur), /produits/chiens et /produits/chats.
- **Typographie des visuels** : utiliser les polices du site (Fraunces pour les titres, Plus Jakarta Sans pour le texte) au lieu de Playfair et Inter.
- **Mention d'affiliation** : ajoutée automatiquement en haut de l'article par le site dès qu'un lien Amazon est présent. Ne pas l'écrire à la main.
- **Version anglaise** : chaque article est aussi publié en anglais (traduction adaptée, pas mot à mot), après l'approbation de la version française.
- **Validation** : la personne qui rédige donne les trois approbations et publie.
- **Publication** : programmée le lundi à 8 h (heure de Montréal) grâce aux champs `date` et `heure` ; le site la fait apparaître automatiquement.
- **Registre éditorial** : data/registre-editorial.csv (et data/historique-epingles.csv pour les épingles).
- **Réseaux sociaux** : aucun outil ne publie sur Pinterest, Facebook ou Instagram ; préparer les textes et visuels, la personne les programme elle-même.
- **Pas de mention « nouvel article chaque lundi »** sur le site, et pas d'infolettre.
