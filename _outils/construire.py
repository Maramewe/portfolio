#!/usr/bin/env python3
"""Fabrique le site prêt à mettre en ligne à partir de contenu.html.

contenu.html est la source unique : c'est elle qu'on modifie, et c'est elle
qui est publiée telle quelle comme aperçu en ligne (artifact).

Produit à la racine du site :
  index.html                  la page complète, polices et Three.js servis par le site lui-même
  mentions-legales.html       obligatoires (LCEN), remplies avec l'objet CONFIG de contenu.html
  confidentialite.html        information RGPD sur le formulaire de contact
  404.html                    page introuvable
  favicon.svg, robots.txt, sitemap.xml, .well-known/security.txt
  _headers                    en-têtes de sécurité (Cloudflare Pages, Netlify), CSP calculée ici

Usage : construire.py          (ne fait rien si tout est déjà à jour)
        construire.py --zip    reconstruit tout et fabrique portfolio-site.zip
"""
import base64
import datetime
import hashlib
import html
import pathlib
import re
import sys
import zipfile

SITE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = SITE / "contenu.html"
CIBLE = SITE / "index.html"
ARCHIVE = SITE / "portfolio-site.zip"

# Hébergeur cité dans les mentions légales : à changer si le site n'est pas sur Cloudflare Pages
HEBERGEUR = "Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, États-Unis (cloudflare.com)"

# Fichiers à mettre en ligne (le reste du dossier sert seulement à travailler)
EN_LIGNE = [
    "index.html", "mentions-legales.html", "confidentialite.html", "404.html",
    "favicon.svg", "apple-touch-icon.png", "images/partage.png",
    "robots.txt", "sitemap.xml", ".well-known/security.txt", "_headers",
    "js/three-r128.min.js", "polices",
]

POLICES_GOOGLE = re.compile(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n'
                            r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\n'
                            r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]+">\n')
THREE_CDN = re.compile(r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/three\.js/r128/three\.min\.js"[^>]*></script>')

MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<style>.t{stroke:#0f1a2e}.b{stroke:#2348c9}@media (prefers-color-scheme:dark){.t{stroke:#e7ecf6}.b{stroke:#7f9eff}}</style>
<path class="t" d="M16 3 27 7.5v8.2c0 6.6-4.6 11.4-11 13.3C9.6 27.1 5 22.3 5 15.7V7.5z" fill="none" stroke-width="2.6" stroke-linejoin="round"/>
<path class="b" d="M11 16h10" stroke-width="3.2" stroke-linecap="round"/>
</svg>
"""


def lire_config(texte):
    """Valeurs texte de l'objet CONFIG du script de contenu.html."""
    bloc = re.search(r"const CONFIG = \{(.*?)\n\};", texte, re.S).group(1)
    return dict(re.findall(r'^\s*(\w+): "([^"]*)"', bloc, re.M))


def date_fr(jour):
    return f"{jour.day} {MOIS[jour.month - 1]} {jour.year}"


def pour_la_mise_en_ligne(tete):
    """Polices et Three.js servis par le site lui-même : aucun appel à un tiers."""
    tete, n = POLICES_GOOGLE.subn('<link rel="stylesheet" href="polices/polices.css">\n', tete)
    assert n == 1, "balises Google Fonts introuvables dans contenu.html"
    return tete


def entete(config, titre, description, chemin):
    url = f"https://{config['domaine']}/{chemin}"
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{html.escape(description)}">
<meta name="theme-color" content="#f3f5f9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0b1220" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{url}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="{html.escape(config['nom'])}">
<meta property="og:title" content="{html.escape(titre)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://{config['domaine']}/images/partage.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
"""


def page_texte(tete, logo, config, chemin, titre, description, corps):
    """Page simple (mentions, confidentialité, 404) avec l'en-tête et le pied du site."""
    tete = re.sub(r"<title>.*?</title>", f"<title>{html.escape(titre)} · {html.escape(config['nom'])}</title>", tete, count=1)
    annee = datetime.date.today().year
    return f"""{entete(config, titre, description, chemin)}{tete}
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="barre">
  <div class="enveloppe">
    <a class="marque" href="./" aria-label="{html.escape(config['nom'])}, retour à l’accueil">
      {logo}
      <span>{html.escape(config['nom'])}<small>Réseaux · Cloud · Cybersécurité</small></span>
    </a>
    <nav class="nav" aria-label="Navigation">
      <a class="bouton bouton-plein" href="./#contact">Me contacter</a>
    </nav>
  </div>
</header>
<main class="page-texte" id="contenu">
  <div class="enveloppe">
{corps}
  </div>
</main>
<footer class="pied">
  <div class="enveloppe">
    <span>© {annee} {html.escape(config['nom'])} · Étudiant en cybersécurité</span>
    <nav aria-label="Informations légales"><a href="mentions-legales.html">Mentions légales</a><a href="confidentialite.html">Confidentialité</a><a href="./">Accueil</a></nav>
  </div>
</footer>
</body>
</html>
"""


def mentions(config):
    e = {k: html.escape(v) for k, v in config.items()}
    return f"""    <h1>Mentions légales</h1>
    <p class="maj">Dernière mise à jour : {date_fr(datetime.date.today())}</p>

    <h2>Éditeur du site</h2>
    <p>Ce site est le portfolio personnel et non commercial de {e['nom']}, étudiant.</p>
    <dl>
      <dt>Éditeur et directeur de la publication</dt><dd>{e['nom']}</dd>
      <dt>E-mail</dt><dd><a href="mailto:{e['email']}">{e['email']}</a></dd>
    </dl>
    <p>Conformément à l’article 6 III-2 de la loi n° 2004-575 du 21 juin 2004 (LCEN), l’éditeur, qui publie à titre non professionnel,
    a communiqué ses coordonnées complètes à l’hébergeur.</p>

    <h2>Hébergement</h2>
    <p>{html.escape(HEBERGEUR)}</p>

    <h2>Propriété intellectuelle</h2>
    <p>Les textes et la mise en page de ce site appartiennent à {e['nom']}. Toute reproduction sans autorisation écrite est interdite.
    Les logos des écoles et des outils cités appartiennent à leurs propriétaires respectifs.
    Les polices Familjen Grotesk, Public Sans et JetBrains Mono sont distribuées sous licence SIL Open Font License ; la bibliothèque Three.js sous licence MIT.</p>

    <h2>Données personnelles</h2>
    <p>Le traitement des informations envoyées par le formulaire de contact est décrit dans la page <a href="confidentialite.html">Confidentialité</a>.</p>

    <h2>Signaler une vulnérabilité</h2>
    <p>Vous avez trouvé une faille sur ce site ? Écrivez à <a href="mailto:{e['email']}">{e['email']}</a>. Les modalités figurent aussi dans
    <a href="/.well-known/security.txt">security.txt</a>. Merci de ne pas divulguer le problème avant sa correction.</p>"""


def confidentialite(config):
    e = {k: html.escape(v) for k, v in config.items()}
    return f"""    <h1>Confidentialité</h1>
    <p class="maj">Dernière mise à jour : {date_fr(datetime.date.today())}</p>

    <h2>En bref</h2>
    <ul>
      <li>Ce site ne dépose aucun cookie et n’utilise aucun outil de mesure d’audience.</li>
      <li>Il ne fait appel à aucun service tiers : polices et scripts sont servis par le site lui-même.</li>
      <li>Le formulaire de contact ne stocke rien : il prépare un e-mail que vous envoyez vous-même depuis votre messagerie.</li>
    </ul>

    <h2>Responsable du traitement</h2>
    <p>{e['nom']}. Contact : <a href="mailto:{e['email']}">{e['email']}</a>.</p>

    <h2>Données traitées</h2>
    <p>Quand vous m’écrivez, je reçois les informations que vous choisissez de transmettre : nom, entreprise, adresse e-mail,
    objet et message.</p>

    <h2>Finalité et base légale</h2>
    <p>Ces données servent uniquement à répondre à votre message, par exemple à une proposition de stage. Le traitement repose sur
    mon intérêt légitime à répondre aux personnes qui me contactent (article 6.1.f du RGPD).</p>

    <h2>Destinataires et durée de conservation</h2>
    <p>Je suis le seul destinataire de vos données ; elles ne sont ni vendues ni cédées. Elles sont supprimées
    deux ans après notre dernier échange.</p>

    <h2>Préférence d’affichage</h2>
    <p>Si vous choisissez le thème clair ou sombre, ce choix est enregistré dans votre navigateur (stockage local) et n’est jamais transmis.</p>

    <h2>Vos droits</h2>
    <p>Vous pouvez accéder à vos données, les faire rectifier ou effacer, en limiter le traitement, vous y opposer ou en demander
    la portabilité en écrivant à <a href="mailto:{e['email']}">{e['email']}</a>. Je réponds sous un mois. Si vous estimez que vos droits
    ne sont pas respectés, vous pouvez saisir la CNIL (<a href="https://www.cnil.fr">cnil.fr</a>).</p>"""


INTROUVABLE = """    <p class="code-erreur" aria-hidden="true">404</p>
    <h1>Cette page n’existe pas.</h1>
    <p>Pas de faille ici : la ressource demandée est introuvable. Elle a peut-être été déplacée, ou l’adresse contient une faute de frappe.</p>
    <div class="actions">
      <a class="bouton bouton-plein" href="./">Retour à l’accueil</a>
      <a class="bouton bouton-contour" href="./#contact">Me contacter</a>
    </div>"""


def empreintes_scripts(*pages):
    """Empreintes CSP des scripts en ligne : seuls ces scripts exacts pourront s'exécuter."""
    vus = set()
    for page in pages:
        for script in re.findall(r"<script>(.*?)</script>", page, re.S):
            vus.add("'sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() + "'")
    return " ".join(sorted(vus))


def en_tetes(empreintes):
    csp = "; ".join([
        "default-src 'self'",
        f"script-src 'self' {empreintes}",
        "style-src 'self' 'unsafe-inline'",  # attributs style="" et styles posés par le script
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self' mailto:",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
    ])
    return f"""# En-têtes HTTP de sécurité (Cloudflare Pages ou Netlify). Fichier généré par construire.py : ne pas modifier à la main.
/*
  Content-Security-Policy: {csp}
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  Cross-Origin-Opener-Policy: same-origin

/polices/*
  Cache-Control: public, max-age=31536000, immutable

/js/*
  Cache-Control: public, max-age=31536000, immutable
"""


def provisoires(config):
    """Valeurs encore fictives, à remplacer avant la mise en ligne."""
    return [] if config.get("email") else ["email manquant dans CONFIG"]


def construire(forcer=False):
    if not forcer and CIBLE.exists() and CIBLE.stat().st_mtime >= SOURCE.stat().st_mtime:
        return False
    texte = SOURCE.read_text(encoding="utf-8")
    config = lire_config(texte)
    fin_style = texte.index("</style>") + len("</style>")
    tete, corps = texte[:fin_style], texte[fin_style:].lstrip("\n")
    tete = pour_la_mise_en_ligne(tete)
    corps, n = THREE_CDN.subn('<script src="js/three-r128.min.js"></script>', corps)
    assert n == 1, "balise Three.js introuvable dans contenu.html"
    logo = re.search(r'<svg viewBox="0 0 32 32".*?</svg>', corps, re.S).group(0)
    jour = datetime.date.today()

    description = "Portfolio de Juan Fajardo, étudiant en Bachelor Réseaux, Cloud & Cybersécurité à Toulouse. Recherche de stage dès février 2027."
    titre = re.search(r"<title>(.*?)</title>", tete).group(1)
    pages = {
        "index.html": f"{entete(config, titre, description, '')}{tete}\n</head>\n<body>\n{corps}</body>\n</html>\n",
        "mentions-legales.html": page_texte(tete, logo, config, "mentions-legales.html", "Mentions légales",
                                            f"Mentions légales du site {config['nom']}.", mentions(config)),
        "confidentialite.html": page_texte(tete, logo, config, "confidentialite.html", "Confidentialité",
                                           f"Comment {config['nom']} traite vos données personnelles.", confidentialite(config)),
        "404.html": page_texte(tete, logo, config, "404.html", "Page introuvable", "Cette page n’existe pas.", INTROUVABLE),
    }
    for nom, contenu in pages.items():
        (SITE / nom).write_text(contenu, encoding="utf-8")

    base = f"https://{config['domaine']}"
    (SITE / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"  <url><loc>{base}/{chemin}</loc><lastmod>{jour.isoformat()}</lastmod></url>\n"
                   for chemin in ("", "mentions-legales.html", "confidentialite.html"))
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f"{urls}</urlset>\n", encoding="utf-8")
    # security.txt (RFC 9116) : l'expiration doit rester à moins d'un an, d'où une reconstruction chaque année
    (SITE / ".well-known").mkdir(exist_ok=True)
    (SITE / ".well-known/security.txt").write_text(
        f"Contact: mailto:{config['email']}\n"
        f"Expires: {(jour + datetime.timedelta(days=365)).isoformat()}T00:00:00Z\n"
        "Preferred-Languages: fr, en\n"
        f"Canonical: {base}/.well-known/security.txt\n"
        f"Policy: {base}/mentions-legales.html\n", encoding="utf-8")
    (SITE / "_headers").write_text(en_tetes(empreintes_scripts(*pages.values())), encoding="utf-8")
    return True


LISEZMOI = """SITE {nom} — À LIRE AVANT LA MISE EN LIGNE
{trait}

Ce dossier est le site complet, prêt à être hébergé tel quel (site statique : aucun serveur, aucune base de données).

1. METTRE EN LIGNE (Cloudflare Pages, gratuit)
   - Créer un compte sur dash.cloudflare.com → Workers & Pages → Créer → Pages → « Importer des fichiers ».
   - Déposer le CONTENU de ce dossier (pas le dossier lui-même), puis Déployer.
   - Relier le nom de domaine {domaine} dans l'onglet « Domaines personnalisés ».
   Le fichier _headers active les en-têtes de sécurité (CSP, HSTS…) et 404.html sert de page introuvable.
   Ça marche aussi sur Netlify. Ailleurs (OVH, o2switch…), recopier les en-têtes de _headers dans la configuration du serveur.

2. VÉRIFIER APRÈS LA MISE EN LIGNE
   - securityheaders.com et observatory.mozilla.org : la note doit être A ou mieux.
   - Envoyer un message depuis le formulaire : votre messagerie doit s'ouvrir avec le message prérempli.
   - Partager le lien sur LinkedIn : l'aperçu doit afficher images/partage.png.

3. CE QUI EST ENCORE PROVISOIRE
{provisoires}
   Pour modifier : éditer contenu.html (objet CONFIG en haut du script), puis lancer
   python3 _apercu/construire.py --zip   → ce zip est refait avec les nouvelles valeurs.

4. CHAQUE ANNÉE
   .well-known/security.txt expire le {expire} : relancer construire.py --zip et redéployer avant cette date.

Contenu : index.html (le site), mentions-legales.html, confidentialite.html, 404.html, favicon.svg,
apple-touch-icon.png, images/partage.png (aperçu réseaux sociaux), polices/ et js/ (servis localement,
aucun appel à Google ni à un CDN), robots.txt, sitemap.xml, .well-known/security.txt, _headers.
"""


def empaqueter():
    config = lire_config(SOURCE.read_text(encoding="utf-8"))
    manquants = [f for f in EN_LIGNE if not (SITE / f).exists()]
    if manquants:
        sys.exit(f"Fichiers manquants : {', '.join(manquants)}")
    reste = provisoires(config)
    expire = (datetime.date.today() + datetime.timedelta(days=365))
    titre = f"SITE {config['nom']} — À LIRE AVANT LA MISE EN LIGNE"
    lisezmoi = LISEZMOI.format(
        nom=config["nom"], trait="=" * len(titre), domaine=config["domaine"], expire=date_fr(expire),
        provisoires="\n".join(f"   - {r}" for r in reste) or "   - Rien de signalé dans CONFIG.",
    )
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("portfolio-site/LISEZMOI.txt", lisezmoi)
        for entree in EN_LIGNE:
            chemin = SITE / entree
            fichiers = sorted(p for p in chemin.rglob("*") if p.is_file()) if chemin.is_dir() else [chemin]
            for f in fichiers:
                z.write(f, "portfolio-site/" + f.relative_to(SITE).as_posix())
    return reste


if __name__ == "__main__":
    construire(forcer=True)
    print(f"{CIBLE} reconstruit (avec les pages légales, 404, security.txt et _headers).")
    if "--zip" in sys.argv:
        reste = empaqueter()
        print(f"{ARCHIVE} fabriqué ({ARCHIVE.stat().st_size // 1024} Ko).")
        if reste:
            print("Encore provisoire :", *reste, sep="\n  ")
