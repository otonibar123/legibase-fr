"""Légibase : télécharge la dernière base LEGI (DILA) et régénère la bibliothèque.

Usage (depuis le dossier legibase-fr) :
    python3 -I scripts/update.py               # télécharge si besoin, extrait, régénère
    python3 -I scripts/update.py --sans-telechargement   # réutilise l'archive déjà présente dans .cache/

Python 3 et bibliothèque standard uniquement. Réservé au mainteneur.
"""
import re
import shutil
import sys
import tarfile
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # nécessaire avec « python3 -I »
import generer  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
CACHE = RACINE / ".cache"          # archive brute et XML extraits : jamais publiés sur GitHub
URL_LEGI = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"

# Codes traités : dossier -> identifiant LEGITEXT. On en ajoute un seul à la fois, avec l'accord de l'utilisateur.
CODES = {
    "code-civil": "LEGITEXT000006070721",
}


def derniere_archive_globale():
    """Nom du fichier « Freemium_legi_global_AAAAMMJJ-HHMMSS.tar.gz » le plus récent."""
    page = urllib.request.urlopen(URL_LEGI).read().decode()
    noms = sorted(set(re.findall(r"Freemium_legi_global_\d{8}-\d{6}\.tar\.gz", page)))
    if not noms:
        sys.exit("Aucune archive globale trouvée sur " + URL_LEGI)
    return noms[-1]


def telecharger(nom):
    CACHE.mkdir(exist_ok=True)
    cible = CACHE / nom
    if cible.exists():
        print("Archive déjà présente :", cible.name)
        return cible
    print("Téléchargement de", nom, "(plusieurs centaines de Mo)...")
    urllib.request.urlretrieve(URL_LEGI + nom, str(cible) + ".part")
    Path(str(cible) + ".part").rename(cible)
    return cible


def extraire(archive):
    """Extrait en un seul passage les XML des codes demandés (articles, sections, structure).
    L'archive est lue séquentiellement : compter une dizaine de minutes."""
    dossiers = {cle: CACHE / ("extrait-" + cle) for cle in CODES}
    for d in dossiers.values():
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    par_id = {id_code: cle for cle, id_code in CODES.items()}
    n = 0
    with tarfile.open(archive, "r|gz") as tar:
        for membre in tar:
            if not membre.isfile() or "/code_en_vigueur/" not in membre.name:
                continue
            m = re.search(r"/(LEGITEXT\d{12})/", membre.name)
            if not m or m.group(1) not in par_id:
                continue
            cle = par_id[m.group(1)]
            # Chemin sûr : on reconstruit le nom du fichier sous le dossier du code, sans « .. ».
            relatif = Path(membre.name.split(m.group(1) + "/", 1)[1])
            if ".." in relatif.parts:
                continue
            destination = dossiers[cle] / relatif
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(tar.extractfile(membre).read())
            n += 1
    print(n, "fichiers XML extraits")
    return dossiers


def main():
    nom = derniere_archive_globale() if "--sans-telechargement" not in sys.argv else \
        sorted(p.name for p in CACHE.glob("Freemium_legi_global_*.tar.gz"))[-1]
    archive = telecharger(nom) if "--sans-telechargement" not in sys.argv else CACHE / nom
    d = re.search(r"global_(\d{4})(\d{2})(\d{2})", nom)
    date_base = "-".join(d.groups())
    dossiers = {cle: CACHE / ("extrait-" + cle) for cle in CODES}
    if "--sans-extraction" not in sys.argv:
        dossiers = extraire(archive)
    stats, donnees, aretes = generer.ecrire_tout(CODES, dossiers, RACINE, date_base, date.today().isoformat())
    print("--- Résumé ---")
    for cle, dd in donnees.items():
        print(f"{dd['meta']['nom']} : {dd['nb_articles']} articles dans {dd['nb_fichiers']} fichiers")
    print(len(aretes), "renvois")
    for k, v in sorted(stats.items()):
        print(f"  {k} : {v}")


if __name__ == "__main__":
    main()
