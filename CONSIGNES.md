# Consignes de la routine — brouillons de « L'actu du fenua »

Tu prépares les brouillons de deux podcasts d'actualité pour des élèves de Polynésie française : une chaîne **collège** (11-15 ans) et une chaîne **lycée** (15-18 ans). Un professeur d'histoire-géographie-EMC relit et valide chaque brouillon avant publication. Suis les étapes dans l'ordre. Ne modifie ni le code, ni `chaines.json`, ni `veille_sources.json`, ni `voix/`, ni `docs/`, ni `etat/`.

## 1. Lire la réserve

`travail/candidats.json` est rempli chaque jour par GitHub Actions (ton réseau bloque les sites de presse, ne lance PAS `collecte.py`). Chaque article a : `uid`, `rubrique` (`polynesie`, `oceanie`, `monde`), `titre`, `source`, `date`, `url`, `resume`. Certains sont en anglais (RNZ Pacific) : traduis-les.

Si la réserve est vide, ne fabrique rien : termine en le signalant.

## 2. Choisir les sujets

Pour chaque chaîne, écris `travail/<chaine>/selection.json` :

```json
{"items": [{"uid": "…", "rubrique": "polynesie"}]}
```

- **Collège** : 3 sujets, un par rubrique (Polynésie, Océanie, monde).
- **Lycée** : 4 sujets, au moins un par rubrique.
- Les deux chaînes peuvent partager des sujets, traités différemment.
- S'il manque une rubrique dans la réserve, dis-le simplement dans l'épisode.

Règles de choix, à respecter strictement :

- **Pas de faits divers** : ni crime, ni accident, ni suicide, ni procès de particuliers.
- **Aucun nom de particulier**, et jamais de mineur. Les personnalités publiques (élus, responsables, sportifs, artistes) peuvent être nommées avec leur fonction.
- Préfère ce qui a une **valeur pour comprendre le monde** : institutions, environnement, océan, climat, santé publique, culture, sport, sciences, relations internationales, société.
- Pour le collège, évite les sujets violents ou angoissants (guerre détaillée, attentats). Pour le lycée, les conflits sont possibles, traités avec sobriété, sans détails choquants.
- Varie les sujets : pas deux sujets sur le même événement dans une chaîne.

## 3. Écrire les scripts

Écris `travail/<chaine>/script.txt` : le texte parlé, lu tel quel par une voix de synthèse.

**Collège** (450 à 600 mots, environ 4 minutes) :

- Ouverture : « Ia ora na ! C'est L'actu du fenua, l'actualité du … » avec la date en toutes lettres, puis l'annonce des trois sujets.
- Pour chaque sujet : ce qui s'est passé, puis « pourquoi on en parle » avec le contexte. Explique au moins un mot difficile par sujet (« un préavis de grève, c'est… »).
- Fin : « Le mot à retenir » (un des mots expliqués), puis une question à se poser ou à discuter en classe.

**Lycée** (700 à 900 mots, environ 6 minutes) :

- Ouverture : « Ia ora na ! C'est L'actu du fenua, édition lycée, du … » avec la date, puis l'annonce des quatre sujets.
- Pour chaque sujet : les faits, le contexte, les enjeux. Quand un débat existe, présente honnêtement les différents points de vue. Fais un lien avec les programmes d'histoire-géographie-EMC quand il est naturel (« c'est un bon exemple de… »).
- Fin : une question pour débattre.

Règles communes :

- Les élèves sont vouvoyés collectivement (« vous »). Ton clair, vivant et précis, sans infantiliser.
- **Neutralité** : aucune opinion personnelle. Sur la politique locale ou nationale, des faits et les positions de chacun, jamais de parti pris.
- **Cite la source à l'oral** (« selon Tahiti Infos », « d'après RNZ Pacific »).
- **N'invente rien** au-delà des titres et résumés fournis. Pas de chiffre, de date ni de citation qui n'y figure pas. Si le résumé est trop mince pour comprendre, choisis un autre sujet.
- Texte brut uniquement : pas de Markdown, de titre, de puce, d'emoji ni d'URL.
- Écris en toutes lettres ce qui se lit mal : nombres, dates, pour cent, siècles. Les sigles courants peuvent rester.
- Ne mets pas de mention sur l'IA à la fin : elle est ajoutée automatiquement.

## 4. Vérifier et envoyer au professeur

```bash
python3 episode.py --verifier
git checkout -b claude/brouillon-$(TZ=Pacific/Tahiti date +%Y-%m-%d)
git add -f travail/college travail/lycee
git commit -m "Brouillons du $(TZ=Pacific/Tahiti date +%Y-%m-%d)"
git push origin HEAD
```

Ne pousse JAMAIS sur `main` et ne lance pas `python3 episode.py` sans `--verifier`. GitHub Actions ouvre une demande de fusion (pull request) avec les deux scripts : le professeur la relit, la corrige au besoin et la fusionne. La fusion déclenche la fabrication de la voix et la publication.

## En cas de problème

Si `episode.py --verifier` échoue, corrige tes fichiers dans `travail/` et recommence. Si le push échoue, ne contourne pas en modifiant le code : termine en expliquant précisément ce qui a échoué, avec le message d'erreur.
