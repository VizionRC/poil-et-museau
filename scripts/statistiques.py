"""Statistiques hebdomadaires de poiletmuseau.com (Cloudflare Web Analytics, sans cookie).

Lancé chaque lundi par .github/workflows/statistiques.yml.
Lit la clé CF_API_TOKEN (secret GitHub, permission « Account Analytics : Read »)
et écrit stats/derniere-semaine.json, déposé ensuite dans la branche « statistiques ».
"""
import datetime as dt
import json
import os
import sys
import urllib.request

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "9bf11d8f11a15713801f848266c7afcd")
TOKEN = os.environ.get("CF_API_TOKEN", "")
HOSTS = ["poiletmuseau.com", "www.poiletmuseau.com"]
TZ = dt.timezone(dt.timedelta(hours=-5))  # heure de l'Est (approx.), pour les libellés seulement


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise SystemExit("Erreur Cloudflare : " + json.dumps(out["errors"], ensure_ascii=False))
    return out["data"]["viewer"]["accounts"][0]


Q = """
query($acct: String!, $f: AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject) {
  viewer { accounts(filter: {accountTag: $acct}) {
    total: rumPageloadEventsAdaptiveGroups(limit: 1, filter: $f) { count sum { visits } }
    pages: rumPageloadEventsAdaptiveGroups(limit: 10, filter: $f, orderBy: [count_DESC]) { count sum { visits } dimensions { requestPath } }
    sources: rumPageloadEventsAdaptiveGroups(limit: 10, filter: $f, orderBy: [sum_visits_DESC]) { sum { visits } dimensions { refererHost } }
    pays: rumPageloadEventsAdaptiveGroups(limit: 8, filter: $f, orderBy: [sum_visits_DESC]) { sum { visits } dimensions { countryName } }
    appareils: rumPageloadEventsAdaptiveGroups(limit: 5, filter: $f, orderBy: [sum_visits_DESC]) { sum { visits } dimensions { deviceType } }
    jours: rumPageloadEventsAdaptiveGroups(limit: 7, filter: $f, orderBy: [date_ASC]) { count sum { visits } dimensions { date } }
  } }
}"""


def periode(debut, fin):
    f = {"AND": [
        {"datetime_geq": debut.strftime("%Y-%m-%dT%H:%M:%SZ"), "datetime_lt": fin.strftime("%Y-%m-%dT%H:%M:%SZ")},
        {"OR": [{"requestHost": h} for h in HOSTS]},
    ]}
    d = gql(Q, {"acct": ACCOUNT, "f": f})
    tot = d["total"][0] if d["total"] else {"count": 0, "sum": {"visits": 0}}
    return {
        "debut": debut.date().isoformat(),
        "fin": (fin - dt.timedelta(days=1)).date().isoformat(),
        "visites": tot["sum"]["visits"],
        "pages_vues": tot["count"],
        "pages": [{"page": x["dimensions"]["requestPath"], "vues": x["count"], "visites": x["sum"]["visits"]} for x in d["pages"]],
        "sources": [{"source": x["dimensions"]["refererHost"] or "(accès direct)", "visites": x["sum"]["visits"]} for x in d["sources"]],
        "pays": [{"pays": x["dimensions"]["countryName"] or "(inconnu)", "visites": x["sum"]["visits"]} for x in d["pays"]],
        "appareils": [{"appareil": x["dimensions"]["deviceType"] or "(inconnu)", "visites": x["sum"]["visits"]} for x in d["appareils"]],
        "par_jour": [{"date": x["dimensions"]["date"], "visites": x["sum"]["visits"], "pages_vues": x["count"]} for x in d["jours"]],
    }


def main():
    if not TOKEN:
        sys.exit("CF_API_TOKEN manquant : ajoute-le dans GitHub > Settings > Secrets and variables > Actions.")
    # Semaine complète précédente, du lundi 00:00 au lundi 00:00 (UTC)
    auj = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    lundi = auj - dt.timedelta(days=auj.weekday())
    sem = periode(lundi - dt.timedelta(days=7), lundi)
    prec = periode(lundi - dt.timedelta(days=14), lundi - dt.timedelta(days=7))
    out = {"site": "poiletmuseau.com", "genere_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "source": "Cloudflare Web Analytics (sans cookie, toutes les visites)",
           "semaine": sem, "semaine_precedente": prec}
    os.makedirs("stats", exist_ok=True)
    with open("stats/derniere-semaine.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"Semaine du {sem['debut']} au {sem['fin']} : {sem['visites']} visites, {sem['pages_vues']} pages vues "
          f"(semaine précédente : {prec['visites']} visites).")


if __name__ == "__main__":
    main()
