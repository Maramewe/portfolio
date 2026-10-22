#!/usr/bin/env python3
"""Petit serveur local pour l'aperçu du site (127.0.0.1 uniquement).

Il sert le dossier du site sans cache et reconstruit index.html dès que
contenu.html a changé : chaque modification se voit immédiatement.
Usage : serveur.py <dossier_du_site> <port>
"""
import functools
import http.server
import sys

from construire import construire


class SansCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _a_jour(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            try:
                construire()
            except Exception as e:  # on sert l'ancienne version plutôt que rien
                print(f"Construction impossible : {e}", file=sys.stderr)

    def do_GET(self):
        self._a_jour()
        super().do_GET()

    def do_HEAD(self):
        self._a_jour()
        super().do_HEAD()

    def log_message(self, *args):
        pass  # pas de journal à chaque requête


dossier, port = sys.argv[1], int(sys.argv[2])
gestionnaire = functools.partial(SansCache, directory=dossier)
http.server.ThreadingHTTPServer(("127.0.0.1", port), gestionnaire).serve_forever()
