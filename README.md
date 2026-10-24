# Parau Mau (« les vraies nouvelles ») — podcasts d'actualité pour les élèves

Deux chaînes (collège, lycée), deux épisodes par semaine : Polynésie, Océanie, monde.

1. Chaque jour à 17 h (Tahiti), GitHub Actions collecte l'actualité (`collecte.py`, sources dans `veille_sources.json`) dans la réserve `travail/candidats.json`.
2. Dimanche et mercredi vers 18 h, une routine Claude choisit les sujets et écrit les deux scripts (`CONSIGNES.md`), puis les pousse sur une branche `claude/brouillon-…`.
3. `brouillon.yml` ouvre une demande de fusion contenant les scripts : le professeur relit, corrige au besoin, fusionne.
4. La fusion déclenche `publier.yml` : voix (Microsoft Vivienne, Piper en secours), MP3, flux, pages (`episode.py`), GitHub Pages.

Pages : https://teruhikotinorua19-beep.github.io/actu-eleves/ — réglages dans `chaines.json`.

Règles éditoriales (dans `CONSIGNES.md`) : pas de faits divers, aucun nom de particulier ni de mineur, neutralité politique, source citée à l'oral, rien d'inventé, mention IA ajoutée automatiquement en fin d'épisode. Aucune donnée d'élève : pas de compte, pas de traceur.
