#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Couvertures 1400 x 1400 « pirogue » : un équipage d'élèves explorateurs sur une
pirogue double polynésienne (voile en pince de crabe), sur une mer déchaînée,
cap sur une étoile — la quête du savoir. Bandes rouges du drapeau et frises
de motifs inspirés du tatouage (motifs génériques, aucun tatouage réel copié).

Dessin en SVG, rendu par Chrome sans interface, puis JPEG avec Pillow.

    python3.13 outils/couverture_pirogue.py "Nom du podcast" [dossier]
"""
import json, math, random, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W = 1400
ROUGE, NUIT, ECUME = "#ce1126", "#0a0e1a", "#f3f6f7"


def dents(y, h, n, coul, bas=True, x0=0, x1=W):
    """Rangée de dents de requin (niho mano)."""
    pas = (x1 - x0) / n
    pts = []
    for i in range(n):
        x = x0 + i * pas
        if bas:
            pts.append(f'<polygon points="{x:.1f},{y} {x+pas:.1f},{y} {x+pas/2:.1f},{y+h}"/>')
        else:
            pts.append(f'<polygon points="{x:.1f},{y+h} {x+pas:.1f},{y+h} {x+pas/2:.1f},{y}"/>')
    return f'<g fill="{coul}">{"".join(pts)}</g>'


def losanges(y, r, n, coul):
    pas = W / n
    return f'<g fill="{coul}">' + "".join(
        f'<polygon points="{pas*i+pas/2-r},{y} {pas*i+pas/2},{y-r*.6} {pas*i+pas/2+r},{y} {pas*i+pas/2},{y+r*.6}"/>'
        for i in range(n)) + "</g>"


def personnage(x, pose, h=1.0):
    """Silhouette d'élève debout sur le pont (pieds en y = 0)."""
    s = h
    tete = (0, -150 * s)
    epaule, bassin = (0, -122 * s), (0, -68 * s)
    jambes = [((-14 * s, 0), (-4 * s, -36 * s)), ((16 * s, 0), (6 * s, -36 * s))]
    bras = {
        "montre":  [(-10, -118, -40, -88, -46, -60), (8, -118, 52, -138, 92, -160)],
        "pagaie":  [(0, -116, 30, -92, 54, -74), (0, -116, 20, -84, 40, -62)],
        "barre":   [(0, -116, -34, -96, -56, -78), (0, -116, -24, -86, -40, -66)],
        "corde":   [(0, -118, 26, -150, 40, -184), (0, -118, -30, -96, -42, -70)],
        "longue":  [(0, -118, 34, -140, 64, -150), (0, -118, 22, -142, 50, -170)],
    }[pose]
    traits = []
    for (a, b), (c, d) in [(j[0], j[1]) for j in jambes]:
        traits.append(f'M{a:.1f},{b:.1f} L{c:.1f},{d:.1f} L{bassin[0]:.1f},{bassin[1]:.1f}')
    for bx in bras:
        a, b, c, d, e, f = [v * s for v in bx]
        traits.append(f'M{a:.1f},{b:.1f} L{c:.1f},{d:.1f} L{e:.1f},{f:.1f}')
    g = [f'<g transform="translate({x},0)">',
         f'<path d="{" ".join(traits)}" stroke="{NUIT}" stroke-width="{16*s:.1f}" '
         'fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
         f'<path d="M{bassin[0]},{bassin[1]} L{epaule[0]},{epaule[1]}" stroke="{NUIT}" '
         f'stroke-width="{34*s:.1f}" stroke-linecap="round"/>',
         f'<circle cx="{tete[0]}" cy="{tete[1]:.1f}" r="{17*s:.1f}" fill="{NUIT}"/>',
         # chignon / couronne de cheveux, pour varier les silhouettes
         f'<circle cx="{-11*s:.1f}" cy="{-160*s:.1f}" r="{7*s:.1f}" fill="{NUIT}"/>' if pose in ("corde", "pagaie") else "",
         ]
    if pose == "pagaie":
        g.append(f'<path d="M{70*s:.1f},{-100*s:.1f} L{20*s:.1f},{70*s:.1f}" stroke="{NUIT}" stroke-width="{6*s:.1f}"/>'
                 f'<ellipse cx="{18*s:.1f}" cy="{80*s:.1f}" rx="{8*s:.1f}" ry="{22*s:.1f}" fill="{NUIT}" transform="rotate(16 {18*s:.1f} {80*s:.1f})"/>')
    if pose == "barre":
        g.append(f'<path d="M{-20*s:.1f},{-110*s:.1f} L{-120*s:.1f},{110*s:.1f}" stroke="{NUIT}" stroke-width="{8*s:.1f}"/>'
                 f'<ellipse cx="{-124*s:.1f}" cy="{122*s:.1f}" rx="{11*s:.1f}" ry="{30*s:.1f}" fill="{NUIT}" transform="rotate(24 {-124*s:.1f} {122*s:.1f})"/>')
    if pose == "longue":
        # longue-vue / rouleau tenu vers l'étoile
        g.append(f'<path d="M{44*s:.1f},{-160*s:.1f} L{96*s:.1f},{-182*s:.1f}" stroke="{NUIT}" stroke-width="{11*s:.1f}" stroke-linecap="round"/>')
    g.append("</g>")
    return "".join(g)


def pirogue():
    """Pirogue double vue de côté, voile en pince de crabe. Origine : pont, centre."""
    coque = ('M-400,-58 C-380,-20 -360,-4 -330,0 L330,0 C370,-6 395,-30 420,-78 '
             'L432,-70 C420,-20 400,40 330,58 L-320,58 C-380,46 -400,0 -414,-50 Z')
    coque2 = ('M-340,-20 L300,-20 C340,-24 360,-40 372,-62 L380,-56 C372,-30 352,0 300,8 L-300,8 '
              'C-340,4 -356,-16 -360,-40 Z')
    voile = 'M30,-6 L-210,-470 C-120,-400 60,-380 170,-430 Z'
    motifs_voile = []
    # bandes de triangles rouges sur la voile, suivant ses deux bords
    for k in range(9):
        t = 0.15 + k * 0.085
        ax, ay = 30 + (-210 - 30) * t, -6 + (-470 + 6) * t
        bx, by = 30 + (170 - 30) * t, -6 + (-430 + 6) * t
        mx, my = (ax + bx) / 2, (ay + by) / 2 - 10
        motifs_voile.append(f'<polygon points="{ax+8:.1f},{ay:.1f} {bx-6:.1f},{by:.1f} {mx:.1f},{my-34:.1f}" fill="{ROUGE}" opacity=".9"/>')
    frise_coque = "".join(
        f'<polygon points="{x},{12} {x+26},{12} {x+13},{34}" fill="{ECUME}"/>' for x in range(-300, 300, 30))
    return f'''
<g>
  <path d="{coque2}" fill="#160d08"/>
  <rect x="-330" y="-30" width="680" height="14" fill="#2b1a10"/>
  <path d="M-150,-30 L-150,0 M120,-30 L120,0" stroke="#2b1a10" stroke-width="12"/>
  <path d="M30,-6 L-210,-470" stroke="#2b1a10" stroke-width="12" stroke-linecap="round"/>
  <path d="{voile}" fill="#efe3c8"/>
  {"".join(motifs_voile)}
  <path d="M30,-6 L-210,-470 M30,-6 L170,-430" stroke="#2b1a10" stroke-width="10" stroke-linecap="round" fill="none"/>
  <path d="M-210,-470 C-120,-400 60,-380 170,-430" stroke="#2b1a10" stroke-width="4" fill="none"/>
  <path d="M30,-6 L380,-62" stroke="#2b1a10" stroke-width="3"/>
  {personnage(-330, "barre", 1.0)}
  {personnage(-190, "pagaie", 0.92)}
  {personnage(-60, "corde", 0.95)}
  {personnage(100, "pagaie", 0.9)}
  {personnage(205, "longue", 0.98)}
  {personnage(345, "montre", 1.05)}
  <path d="{coque}" fill="#2b1a10"/>
  <g>{frise_coque}</g>
  <path d="M-320,44 L330,44" stroke="{ROUGE}" stroke-width="8"/>
  <path d="M420,-78 C432,-110 452,-118 466,-108 C450,-104 440,-92 432,-70 Z" fill="#2b1a10"/>
  <path d="M-414,-50 C-430,-84 -450,-92 -466,-82 C-448,-78 -436,-66 -400,-58 Z" fill="#2b1a10"/>
</g>'''


def vague(y, ampl, lg, phase, coul, ecume=True, epaisseur=10, crete=True):
    """Bande de houle : sinusoïde aux crêtes pointues, remplie jusqu'en bas."""
    pts = []
    for x in range(-40, W + 60, 10):
        u = (x / lg + phase) * 2 * math.pi
        yy = y - ampl * (abs(math.sin(u / 2)) ** 0.6) * (1 if crete else 1)
        pts.append((x, yy))
    d = "M" + " L".join(f"{x},{yy:.1f}" for x, yy in pts) + f" L{W+60},{W} L-40,{W} Z"
    out = f'<path d="{d}" fill="{coul}"/>'
    if ecume:
        ligne = "M" + " L".join(f"{x},{yy+4:.1f}" for x, yy in pts)
        out += f'<path d="{ligne}" stroke="{ECUME}" stroke-width="{epaisseur}" fill="none" opacity=".85" stroke-linejoin="round"/>'
    return out


def rouleau(cx, cy, r, sens=1, coul="#0e3a52"):
    """Grande vague qui déferle, avec griffes d'écume."""
    s = sens
    d = (f'M{cx - s*r*1.9},{cy + r*1.2} C{cx - s*r*1.2},{cy + r*0.6} {cx - s*r*0.9},{cy - r*0.9} {cx},{cy - r} '
         f'C{cx + s*r*0.9},{cy - r*1.05} {cx + s*r*1.25},{cy - r*0.2} {cx + s*r*0.9},{cy + r*0.25} '
         f'C{cx + s*r*0.6},{cy - r*0.2} {cx + s*r*0.1},{cy - r*0.3} {cx + s*r*0.05},{cy + r*0.2} '
         f'C{cx},{cy + r*0.7} {cx + s*r*0.6},{cy + r*1.0} {cx + s*r*1.6},{cy + r*1.2} Z')
    griffes = []
    for k in range(7):
        a = math.radians(-160 + k * 26) if s > 0 else math.radians(-20 - k * 26)
        x0 = cx + math.cos(a) * r * 1.0
        y0 = cy - r * 0.05 + math.sin(a) * r * 0.95
        x1 = x0 + s * 38 + math.cos(a) * 22
        y1 = y0 + 26
        griffes.append(f'<path d="M{x0:.1f},{y0:.1f} Q{x0 + s*30:.1f},{y0 - 6:.1f} {x1:.1f},{y1:.1f}" '
                       f'stroke="{ECUME}" stroke-width="12" fill="none" stroke-linecap="round"/>')
    crete = (f'M{cx - s*r*1.0},{cy - r*0.55} C{cx - s*r*0.6},{cy - r*1.0} {cx + s*r*0.7},{cy - r*1.1} '
             f'{cx + s*r*0.92},{cy + r*0.1}')
    spirale = (f'M{cx + s*r*0.9},{cy + r*0.2} C{cx + s*r*0.55},{cy - r*0.15} {cx + s*r*0.15},{cy - r*0.1} '
               f'{cx + s*r*0.2},{cy + r*0.25} C{cx + s*r*0.25},{cy + r*0.45} {cx + s*r*0.5},{cy + r*0.4} {cx + s*r*0.5},{cy + r*0.2}')
    return (f'<path d="{d}" fill="{coul}"/>'
            f'<path d="{crete}" stroke="{ECUME}" stroke-width="16" fill="none" stroke-linecap="round"/>'
            f'<path d="{spirale}" stroke="{ECUME}" stroke-width="9" fill="none" stroke-linecap="round" opacity=".9"/>'
            + "".join(griffes))


def svg(nom, niveau):
    rnd = random.Random(7)
    pluie = "".join(
        f'<line x1="{x}" y1="{y}" x2="{x-22}" y2="{y+70}" />'
        for x, y in ((rnd.randint(0, W + 200), rnd.randint(250, 1100)) for _ in range(160)))
    embruns = "".join(
        f'<circle cx="{rnd.gauss(1150, 90):.0f}" cy="{rnd.gauss(830, 50):.0f}" r="{rnd.uniform(2, 7):.1f}"/>'
        for _ in range(70))
    etoile_rayons = "".join(
        f'<polygon points="1130,{390-(150 if i%2==0 else 80)} 1122,390 1138,390" transform="rotate({i*22.5} 1130 390)"/>'
        for i in range(16))
    taille = 128 if len(nom) <= 13 else 112 if len(nom) <= 16 else 96
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">
<defs>
  <linearGradient id="ciel" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#121625"/><stop offset=".55" stop-color="#2c2a44"/><stop offset="1" stop-color="#4a3a52"/>
  </linearGradient>
  <radialGradient id="lueur" cx="1130" cy="390" r="620" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#fff4d6" stop-opacity=".95"/><stop offset=".18" stop-color="#ffc98a" stop-opacity=".55"/>
    <stop offset=".55" stop-color="#e0606a" stop-opacity=".22"/><stop offset="1" stop-color="#e0606a" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="mer" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#155a6e"/><stop offset="1" stop-color="#06202e"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{W}" fill="url(#ciel)"/>
<rect width="{W}" height="{W}" fill="url(#lueur)"/>
<g fill="#0c0f1c" opacity=".55">
  <ellipse cx="180" cy="420" rx="330" ry="90"/><ellipse cx="460" cy="360" rx="260" ry="70"/>
  <ellipse cx="80" cy="560" rx="260" ry="60"/><ellipse cx="620" cy="470" rx="220" ry="50"/>
</g>
<path d="M300,300 L262,420 L300,418 L240,560 L330,400 L292,402 L330,300 Z" fill="#fff6dd" opacity=".85"/>
<g fill="#fff8e6">{etoile_rayons}</g>
<circle cx="1130" cy="390" r="26" fill="#ffffff"/>
<g stroke="#c9d6e8" stroke-width="2" opacity=".28">{pluie}</g>
{vague(870, 95, 260, .1, "#1d5d70", True, 6)}
{rouleau(330, 850, 150, 1, "#1a566a")}
{vague(935, 90, 320, .55, "#164c60", True, 7)}
{rouleau(1230, 880, 110, -1, "#14495c")}
<g transform="translate(690 880) rotate(-8) scale(1.12)">{pirogue()}</g>
<g fill="{ECUME}" opacity=".8">{embruns}</g>
{vague(1065, 75, 380, .35, "#0f3d50", True, 10)}
{rouleau(150, 1090, 120, 1, "#0d3a4d")}
{vague(1150, 60, 300, .8, "url(#mer)", True, 9)}
{rouleau(1180, 1150, 95, -1, "#0b3244")}
<rect y="0" width="{W}" height="260" fill="{ROUGE}"/>
{dents(250, 34, 40, ROUGE)}
{dents(214, 26, 56, "#ffffff", False)}
{losanges(26, 14, 28, "#ffffff")}
<text x="700" y="{150 + taille*0.25:.0f}" text-anchor="middle" font-family="Arial Black" font-size="{taille}"
      fill="#ffffff" letter-spacing="1">{nom}</text>
<rect y="1230" width="{W}" height="170" fill="{ROUGE}"/>
{dents(1196, 34, 40, ROUGE, False)}
{dents(1230, 24, 56, "#ffffff")}
<text x="700" y="1352" text-anchor="middle" font-family="Arial Black" font-size="84" fill="#ffffff"
      letter-spacing="18">{niveau}</text>
</svg>'''


def rendre(nom, niveau, sortie):
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "c.svg"
        f.write_text(svg(nom, niveau), encoding="utf-8")
        png = Path(tmp) / "c.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size={W},{W}", f"--screenshot={png}", f.as_uri()],
                       check=True, capture_output=True)
        Image.open(png).convert("RGB").resize((W, W)).save(sortie, "JPEG", quality=90)


def main():
    nom = (sys.argv[1] if len(sys.argv) > 1 else "Parau Mau").replace("'", "’").replace("ʻ", "’")
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    for cle, niveau in (("college", "COLLÈGE"), ("lycee", "LYCÉE")):
        sortie = (dest / f"{cle}.jpg") if dest else HERE / "docs" / cle / "couverture.jpg"
        sortie.parent.mkdir(parents=True, exist_ok=True)
        rendre(nom, niveau, sortie)
        print("✓", sortie)


if __name__ == "__main__":
    main()
