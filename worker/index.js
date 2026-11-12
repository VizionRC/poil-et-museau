// Petit script devant les fichiers statiques de dist/.
// 1. Sert le fichier de validation Google Search Console tel quel (sans la redirection .html → sans extension).
// 2. Répond « 410 Disparu » aux anciennes adresses techniques de Shopify (connexion, panier, suivi, API…),
//    pour que Google les retire de son index plus vite qu'avec une simple 404.
// Tout le reste est servi par les fichiers statiques.
const GOOGLE = "/googlec2a3e0344ac0125c.html";

const SHOPIFY = [
  /^\/password\/?$/,
  /^\/agents\.md$/,
  /^\/api(\/|$)/,
  /^\/v1(\/|$)/,
  /^\/wpm(@|\/|$)/,
  /^\/web-pixels/,
  /^\/services\//,
  /^\/customer_authentication(\/|$)/,
  /^\/checkouts?(\/|$)/,
  /^\/cdn\//,
  /^\/apps\//,
  /^\/\d+\/(checkouts|orders|digital_wallets)/,
  /^\/(en\/)?(cart|account)\/(login|register|add|change|update|clear)/,
  /^\/sf_private_access_tokens/,
  /^\/\.well-known\/shopify/,
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (path === GOOGLE) {
      return new Response("google-site-verification: googlec2a3e0344ac0125c.html", {
        headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-cache", "x-robots-tag": "noindex" },
      });
    }
    if (SHOPIFY.some((re) => re.test(path))) {
      return new Response("410 : cette ancienne adresse n'existe plus. Voir https://poiletmuseau.com/", {
        status: 410,
        headers: { "content-type": "text/plain; charset=utf-8", "x-robots-tag": "noindex", "cache-control": "public, max-age=86400" },
      });
    }
    return env.ASSETS.fetch(request);
  },
};
