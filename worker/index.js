// Sert le fichier de validation Google Search Console tel quel (sans la redirection .html → sans extension).
// Tout le reste est servi par les fichiers statiques de dist/.
const GOOGLE = "/googlec2a3e0344ac0125c.html";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === GOOGLE) {
      return new Response("google-site-verification: googlec2a3e0344ac0125c.html", {
        headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-cache" },
      });
    }
    return env.ASSETS.fetch(request);
  },
};
