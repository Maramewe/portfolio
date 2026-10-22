# Portfolio

Mon site personnel : [juan-fajardo.pages.dev](https://juan-fajardo.pages.dev)

Site statique (HTML, CSS, JavaScript et Three.js pour les animations 3D), sans serveur ni base de données, hébergé sur Cloudflare Pages.

## Modifier le site

1. Modifier `contenu.html` (le texte, et l'objet `CONFIG` en haut du script pour les coordonnées).
2. Reconstruire les pages : `python3 _outils/construire.py`
3. Vérifier en local : `python3 _outils/serveur.py . 8000` puis ouvrir http://127.0.0.1:8000
4. Publier : `git add -A`, `git commit -m "…"`, `git push`. Cloudflare Pages redéploie tout seul.

## Sécurité

- En-têtes HTTP de sécurité (CSP, HSTS…) dans `_headers`, générés par `construire.py`.
- Aucun cookie, aucun traceur, aucun service tiers : polices et scripts sont servis par le site lui-même.
- Le formulaire de contact ne stocke rien : il ouvre la messagerie du visiteur.
