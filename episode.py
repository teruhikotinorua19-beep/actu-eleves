#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique les épisodes des chaînes élèves (collège, lycée) à partir des scripts
validés par le professeur.

Pour chaque chaîne dont un script attend dans travail/<chaine>/ :
  - selection.json : {"items": [{"uid", "rubrique"}, …]}
  - script.txt     : le texte parlé
on fait lire le script (voix Microsoft, Piper en secours), on range le MP3
dans docs/<chaine>/episodes/, on régénère le flux docs/<chaine>/feed.xml et la
page docs/<chaine>/index.html, on marque la réserve comme vue, puis on efface
le script (sa présence signale un épisode à fabriquer).

    python3 episode.py              # fabrique (GitHub Actions, voir publier.yml)
    python3 episode.py --verifier   # contrôle seulement (routine Claude)
    python3 episode.py --pages      # régénère flux et pages, sans épisode
"""
import io, json, re, sys, wave
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
CONF = HERE / "chaines.json"
TRAVAIL = HERE / "travail"
DOCS = HERE / "docs"
VUS = HERE / "etat" / "vus.json"
TAHITI = timezone(timedelta(hours=-10))     # pas d'heure d'été à Tahiti
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
RUBRIQUES = {"polynesie": "Polynésie", "oceanie": "Océanie", "monde": "Monde"}


def lire(p, defaut):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defaut
    except Exception:
        return defaut


def ecrire(p, data):
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def nettoyer_oral(t):
    """Filet de sécurité si le script contient du Markdown ou des URL."""
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[*_#`>]+", "", t)
    t = re.sub(r"^\s*[-•]\s+", "", t, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


# ------------------------------------------------------------------- voix

def synthese_edge(texte, voix):
    """Voix neuronale Microsoft (service en ligne non officiel, via edge-tts).
    Sortie MP3 mono 24 kHz à 48 kbit/s constants : la durée se déduit de la taille."""
    import asyncio, edge_tts
    async def go():
        morceaux = []
        async for m in edge_tts.Communicate(texte, voix).stream():
            if m["type"] == "audio":
                morceaux.append(m["data"])
        return b"".join(morceaux)
    mp3 = asyncio.run(go())
    if len(mp3) < 10_000:
        raise RuntimeError("réponse audio vide")
    return mp3, len(mp3) * 8 / 48_000


def synthese_piper(texte, voix):
    """Piper → WAV en mémoire → MP3 64 kbit/s mono (lameenc, sans ffmpeg)."""
    from piper import PiperVoice
    import lameenc
    v = PiperVoice.load(str(HERE / "voix" / f"{voix}.onnx"))
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        v.synthesize_wav(texte, w)
    tampon.seek(0)
    with wave.open(tampon) as w:
        pcm, freq = w.readframes(w.getnframes()), w.getframerate()
    enc = lameenc.Encoder()
    enc.set_bit_rate(64); enc.set_in_sample_rate(freq); enc.set_channels(1); enc.set_quality(2)
    return enc.encode(pcm) + enc.flush(), len(pcm) / 2 / freq


def synthese(texte, conf):
    """Voix principale, puis voix de secours Piper si le service ne répond pas."""
    voix = conf.get("voix", "fr_FR-siwis-medium")
    if voix.startswith("edge:"):
        try:
            return synthese_edge(texte, voix[5:])
        except Exception as e:
            print(f"Voix {voix} indisponible ({e}) : secours Piper.", file=sys.stderr)
            voix = conf.get("voix_secours", "fr_FR-siwis-medium")
    return synthese_piper(texte, voix)


def duree_hms(s):
    s = int(round(s))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


# ------------------------------------------------------- flux et pages

def notes_episode(ep):
    """Notes d'épisode : les articles, rangés par rubrique, avec leur lien."""
    lignes = [f"<p>{escape(ep['description'])}</p>"]
    for r, nom in RUBRIQUES.items():
        lot = [it for it in ep["items"] if it.get("rubrique") == r]
        if not lot:
            continue
        lignes.append(f"<p><b>{nom}</b></p><ul>")
        for it in lot:
            lien = (f'<a href="{escape(it["url"])}">{escape(it["titre"])}</a>'
                    if it.get("url", "").startswith("http") else escape(it["titre"]))
            lignes.append(f"<li>{lien} — {escape(it.get('source', ''))}</li>")
        lignes.append("</ul>")
    return "".join(lignes)


def ecrire_flux(conf, cle, histo):
    ch = conf["chaines"][cle]
    base = f"{conf['base_url'].rstrip('/')}/{cle}"
    items = []
    for ep in histo:
        items.append(f"""    <item>
      <title>{escape(ep['titre'])}</title>
      <description><![CDATA[{notes_episode(ep)}]]></description>
      <content:encoded><![CDATA[{notes_episode(ep)}]]></content:encoded>
      <pubDate>{ep['pubdate']}</pubDate>
      <guid isPermaLink="false">{cle}/{escape(ep['fichier'])}</guid>
      <enclosure url="{base}/episodes/{escape(ep['fichier'])}" length="{ep['taille']}" type="audio/mpeg"/>
      <itunes:duration>{ep['duree']}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")
    (DOCS / cle / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(ch['titre'])}</title>
    <link>{base}/</link>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>fr</language>
    <description>{escape(ch['description'])}</description>
    <itunes:author>{escape(conf['auteur'])}</itunes:author>
    <itunes:image href="{base}/couverture.jpg"/>
    <itunes:category text="Education"/>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
""", encoding="utf-8")


STYLE = """
:root{{--fond:#f6f5f2;--carte:#fff;--texte:#1c1c1c;--doux:#5d6470;--accent:{c}}}
@media (prefers-color-scheme:dark){{:root{{--fond:#14171c;--carte:#1d2128;--texte:#e9e7e2;--doux:#9aa3b0;--accent:#8fc9d0}}}}
body{{margin:0;padding:24px 16px;background:var(--fond);color:var(--texte);font:16px/1.5 -apple-system,system-ui,sans-serif}}
main{{max-width:640px;margin:auto}}
a{{color:var(--accent)}} h1{{line-height:1.2}} span{{color:var(--doux);font-size:13px}}
.bouton{{display:inline-block;margin:4px 0;background:var(--accent);color:#fff;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:600}}
.carte{{background:var(--carte);border-radius:12px;padding:14px 16px;margin:12px 0}}
audio{{width:100%;margin-top:6px}} ul{{padding-left:20px}} details li{{margin:6px 0}}
summary{{cursor:pointer;color:var(--accent)}} code{{word-break:break-all}} img{{border-radius:12px}}
"""


def ecrire_index(conf, cle, histo):
    ch = conf["chaines"][cle]
    base = f"{conf['base_url'].rstrip('/')}/{cle}"
    flux = f"{base}/feed.xml"
    sans_schema = flux.split("://", 1)[1]
    episodes = "".join(
        f'<div class="carte"><b>{escape(ep["titre"])}</b> <span>{ep["duree"][3:]}</span>'
        f'<audio controls preload="none" src="episodes/{escape(ep["fichier"])}"></audio>'
        f'<details><summary>Les articles</summary>{notes_episode(ep)}</details></div>'
        for ep in histo) or "<p>Premier épisode bientôt.</p>"
    (DOCS / cle / "index.html").write_text(f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{escape(ch['titre'])}</title>
<style>{STYLE.format(c=ch['couleur'])}</style></head><body><main>
<img src="couverture.jpg" alt="" width="120" height="120">
<h1>{escape(ch['titre'])}</h1>
<p>{escape(ch['description'])}</p>
<p><a class="bouton" href="overcast://x-callback-url/add?url={quote(flux, safe='')}">S’abonner dans Overcast</a>
<a class="bouton" href="pktc://subscribe/{sans_schema}">Pocket Casts</a>
<a class="bouton" href="podcasts://{sans_schema}">Apple Podcasts</a></p>
<p><span>Adresse du flux, pour une autre application :</span><br><code>{flux}</code></p>
{episodes}
</main></body></html>
""", encoding="utf-8")


def ecrire_accueil(conf):
    cartes = "".join(
        f'<div class="carte"><a href="{cle}/"><b>{escape(ch["titre"])}</b></a><br>{escape(ch["description"])}</div>'
        for cle, ch in conf["chaines"].items())
    (DOCS / "index.html").write_text(f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{escape(conf["nom"])}</title>
<style>{STYLE.format(c="#ce1126")}</style></head><body><main>
<h1>{escape(conf["nom"])}</h1>
<p>« Parau mau », les vraies nouvelles : l'actualité de la Polynésie, de l'Océanie et du monde, en podcast, pour les élèves.</p>
{cartes}
</main></body></html>
""", encoding="utf-8")


def pages(conf):
    for cle in conf["chaines"]:
        histo = lire(DOCS / cle / "episodes.json", [])
        ecrire_flux(conf, cle, histo)
        ecrire_index(conf, cle, histo)
    ecrire_accueil(conf)


# ------------------------------------------------------------- épisodes

def en_attente(conf):
    return [c for c in conf["chaines"] if (TRAVAIL / c / "script.txt").exists()]


def verifier(conf):
    attente = en_attente(conf)
    if not attente:
        sys.exit("Aucun script en attente dans travail/college ni travail/lycee.")
    reserve = {i["uid"] for i in lire(TRAVAIL / "candidats.json", {}).get("items", [])}
    for cle in attente:
        sel = lire(TRAVAIL / cle / "selection.json", None)
        if not isinstance(sel, dict) or not isinstance(sel.get("items"), list):
            sys.exit(f"travail/{cle}/selection.json manquant ou mal formé.")
        inconnus = [s.get("uid") for s in sel["items"] if s.get("uid") not in reserve]
        if inconnus:
            sys.exit(f"{cle} : uid absents de la réserve : {inconnus}")
        texte = nettoyer_oral((TRAVAIL / cle / "script.txt").read_text(encoding="utf-8"))
        if len(texte) < 300:
            sys.exit(f"travail/{cle}/script.txt vide ou trop court.")
        print(f"✓ {cle} : {len(sel['items'])} article(s), {len(texte.split())} mots")


def fabriquer(conf, cle, reserve, now):
    dossier = DOCS / cle
    (dossier / "episodes").mkdir(parents=True, exist_ok=True)
    sel = lire(TRAVAIL / cle / "selection.json", {"items": []})
    script = nettoyer_oral((TRAVAIL / cle / "script.txt").read_text(encoding="utf-8"))
    script += "\n\n" + conf["mention_finale"]
    histo = lire(dossier / "episodes.json", [])

    jour = now.date().isoformat()
    nom = f"actu-{jour}.mp3"
    k = 2
    while (dossier / "episodes" / nom).exists():
        nom = f"actu-{jour}-{k}.mp3"; k += 1

    items = []
    for s in sel.get("items", []):
        c = reserve.get(s.get("uid"), {})
        items.append({"uid": s.get("uid", ""), "rubrique": c.get("rubrique", s.get("rubrique", "")),
                      "titre": c.get("titre", ""), "url": c.get("url", ""), "source": c.get("source", "")})

    mp3, secondes = synthese(script, conf)
    (dossier / "episodes" / nom).write_bytes(mp3)
    histo.insert(0, {
        "fichier": nom, "date": jour, "pubdate": format_datetime(now),
        "titre": f"L'actu du {now.day} {MOIS[now.month - 1]}",
        "description": f"{len(items)} sujet(s) : Polynésie, Océanie, monde.",
        "duree": duree_hms(secondes), "taille": len(mp3), "items": items,
    })
    limite = (now - timedelta(days=int(conf.get("garder_jours", 60)))).date().isoformat()
    garde = []
    for ep in histo:
        if ep["date"] < limite:
            (dossier / "episodes" / ep["fichier"]).unlink(missing_ok=True)
        else:
            garde.append(ep)
    ecrire(dossier / "episodes.json", garde)
    for f in ("selection.json", "script.txt"):
        (TRAVAIL / cle / f).unlink(missing_ok=True)
    print(f"✓ {cle} : {nom} — {duree_hms(secondes)}, {len(mp3) // 1024} Ko, {len(items)} sujet(s)")


def main():
    conf = json.loads(CONF.read_text(encoding="utf-8"))
    if "--verifier" in sys.argv:
        return verifier(conf)
    if "--pages" in sys.argv:
        return pages(conf)
    attente = en_attente(conf)
    if not attente:
        print("Aucun script en attente.")
        return
    reserve = {i["uid"]: i for i in lire(TRAVAIL / "candidats.json", {}).get("items", [])}
    now = datetime.now(TAHITI)
    for cle in attente:
        fabriquer(conf, cle, reserve, now)
    pages(conf)
    # Toute la réserve a été proposée : on ne la repropose pas au prochain épisode.
    vus = lire(VUS, {})
    for u in reserve:
        vus[u] = now.date().isoformat()
    limite = (now - timedelta(days=30)).date().isoformat()
    ecrire(VUS, {u: d for u, d in vus.items() if d >= limite})
    ecrire(TRAVAIL / "candidats.json", {"genere": "", "items": []})


if __name__ == "__main__":
    main()
