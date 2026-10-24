#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte quotidienne de l'actualité pour les chaînes élèves.

Interroge les sources de `veille_sources.json` (collecteurs de `veille.py`,
repris de la Ressourcerie) et ajoute les nouveautés à la réserve
`travail/candidats.json`. Les flux RSS ne gardent que leurs derniers articles :
on collecte donc chaque jour et on accumule, pour que l'épisode du lundi ou du
jeudi couvre les jours précédents. Sont écartés : ce qui a déjà servi
(`etat/vus.json`) et ce qui a plus de `GARDER_JOURS` jours.

Lancé par GitHub Actions (.github/workflows/collecter.yml) : le réseau de
l'environnement cloud de Claude bloque les sites des sources.

    python3 collecte.py
"""
import sys
import urllib.parse
from datetime import timedelta
from pathlib import Path

import veille as V

HERE = Path(__file__).resolve().parent
VUS = HERE / "etat" / "vus.json"
CANDIDATS = HERE / "travail" / "candidats.json"
GARDER_JOURS = 5           # un épisode couvre au plus les 4 ou 5 derniers jours
MAX_PAR_RUBRIQUE = 60      # plafond pour garder le fichier lisible par l'agent


def collecter_wordpress(src, depuis):
    """API REST de WordPress (/wp-json/wp/v2/posts), pour les sites dont le
    flux RSS est bloqué (Radio 1). Options : « categories », « exclure »."""
    params = {"per_page": src.get("max", 30), "after": depuis.strftime("%Y-%m-%dT%H:%M:%S"),
              "_fields": "date_gmt,link,title,excerpt,content"}
    if src.get("categories"):
        params["categories"] = ",".join(map(str, src["categories"]))
    if src.get("exclure"):
        params["categories_exclude"] = ",".join(map(str, src["exclure"]))
    url = src["url"].rstrip("/") + "/wp-json/wp/v2/posts?" + urllib.parse.urlencode(params)
    items = []
    for p in V.http_json(url):
        titre = V.nettoyer(p["title"]["rendered"], 300)
        lien = p.get("link", "")
        if not titre or not lien.startswith("https://"):
            continue
        resume = V.nettoyer(p["excerpt"]["rendered"]) or V.nettoyer(p["content"]["rendered"])
        items.append({"url": lien, "titre": titre, "resume": resume,
                      "date": (p.get("date_gmt") or "")[:10], "auteurs": "",
                      "source_id": src["id"], "source_nom": src["nom"], "pdf": ""})
    return items


def collecter_rss_filtre(src, depuis):
    """Flux RSS général dont on ne garde que les liens contenant
    « url_contient » (ex. la rubrique Pacifique d'Outremers360)."""
    motif = src.get("url_contient", "")
    return [i for i in V.collecter_rss(src, depuis) if motif in i["url"]]


V.COLLECTEURS["wordpress"] = collecter_wordpress
V.COLLECTEURS["rss_filtre"] = collecter_rss_filtre


def main():
    conf = V.charger(V.CONF, None)
    if not conf:
        sys.exit("veille_sources.json introuvable ou illisible.")
    rubriques = {s["id"]: s.get("rubrique", "monde") for s in conf["sources"]}
    vus = V.charger(VUS, {})
    reserve = V.charger(CANDIDATS, {}).get("items", [])

    limite = V.maintenant() - timedelta(days=GARDER_JOURS)
    journal = []
    bruts = V.collecter(conf, limite, journal)
    if not bruts and CANDIDATS.exists():
        print("\n".join(journal))
        sys.exit("Aucune source n'a répondu : la réserve est conservée telle quelle.")

    connus = {i["uid"] for i in reserve}
    for it in bruts:
        u = V.uid_de(it["url"], it["titre"])
        if u in connus:
            continue
        connus.add(u)
        reserve.append({"uid": u, "rubrique": rubriques.get(it["source_id"], "monde"),
                        "titre": it["titre"], "source": it["source_nom"],
                        "date": it.get("date", ""), "url": it.get("url", ""),
                        "resume": it.get("resume", "")[:400]})

    jour_min = limite.date().isoformat()
    reserve = [i for i in reserve if i["uid"] not in vus and (i["date"] or "9") >= jour_min]
    reserve.sort(key=lambda i: i["date"] or "", reverse=True)
    garde = []
    for r in ("polynesie", "oceanie", "monde"):
        garde += [i for i in reserve if i["rubrique"] == r][:MAX_PAR_RUBRIQUE]

    CANDIDATS.parent.mkdir(exist_ok=True)
    V.ecrire_json(CANDIDATS, {"genere": V.maintenant().isoformat(timespec="minutes"),
                              "items": garde}, indent=1)
    compte = {r: sum(i["rubrique"] == r for i in garde) for r in ("polynesie", "oceanie", "monde")}
    journal.append(f"Réserve : {len(garde)} article(s) — {compte}")
    print("\n".join(journal))


if __name__ == "__main__":
    main()
