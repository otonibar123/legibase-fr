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

# Codes traités : dossier -> identifiant LEGITEXT. Tous les codes en vigueur de LEGI (76), ajoutés le 13/11/2026
# avec l'accord de l'utilisateur.
CODES = {
    "code-civil": "LEGITEXT000006070721",
    "code-de-procedure-civile": "LEGITEXT000006070716",
    "code-du-travail": "LEGITEXT000006072050",
    "code-de-la-consommation": "LEGITEXT000006069565",
    "code-de-commerce": "LEGITEXT000005634379",
    "code-de-deontologie-des-architectes": "LEGITEXT000006074232",
    "code-de-justice-administrative": "LEGITEXT000006070933",
    "code-de-justice-militaire-nouveau": "LEGITEXT000006071360",
    "code-de-l-action-sociale-et-des-familles": "LEGITEXT000006074069",
    "code-de-l-artisanat": "LEGITEXT000006075116",
    "code-de-l-aviation-civile": "LEGITEXT000006074234",
    "code-de-l-education": "LEGITEXT000006071191",
    "code-de-l-energie": "LEGITEXT000023983208",
    "code-de-l-entree-et-du-sejour-des-etrangers-et-du-droit-d-asile": "LEGITEXT000006070158",
    "code-de-l-environnement": "LEGITEXT000006074220",
    "code-de-l-expropriation-pour-cause-d-utilite-publique": "LEGITEXT000006074224",
    "code-de-l-organisation-judiciaire": "LEGITEXT000006071164",
    "code-de-l-urbanisme": "LEGITEXT000006074075",
    "code-de-la-commande-publique": "LEGITEXT000037701019",
    "code-de-la-construction-et-de-l-habitation": "LEGITEXT000006074096",
    "code-de-la-defense": "LEGITEXT000006071307",
    "code-de-la-famille-et-de-l-aide-sociale": "LEGITEXT000006072637",
    "code-de-la-justice-penale-des-mineurs": "LEGITEXT000039086952",
    "code-de-la-legion-d-honneur-et-de-la-medaille-militaire": "LEGITEXT000006071007",
    "code-de-la-mutualite": "LEGITEXT000006074067",
    "code-de-la-propriete-intellectuelle": "LEGITEXT000006069414",
    "code-de-la-recherche": "LEGITEXT000006071190",
    "code-de-la-route": "LEGITEXT000006074228",
    "code-de-la-sante-publique": "LEGITEXT000006072665",
    "code-de-la-securite-interieure": "LEGITEXT000025503132",
    "code-de-la-securite-sociale": "LEGITEXT000006073189",
    "code-de-la-voirie-routiere": "LEGITEXT000006070667",
    "code-de-procedure-penale": "LEGITEXT000006071154",
    "code-des-assurances": "LEGITEXT000006073984",
    "code-des-communes": "LEGITEXT000006070162",
    "code-des-communes-de-la-nouvelle-caledonie": "LEGITEXT000006070300",
    "code-des-douanes": "LEGITEXT000006071570",
    "code-des-impositions-sur-les-biens-et-services": "LEGITEXT000044595989",
    "code-des-instruments-monetaires-et-des-medailles": "LEGITEXT000006070666",
    "code-des-juridictions-financieres": "LEGITEXT000006070249",
    "code-des-pensions-civiles-et-militaires-de-retraite": "LEGITEXT000006070302",
    "code-des-pensions-de-retraite-des-marins-francais-du-commerce-de-peche-ou-de-plaisance": "LEGITEXT000006074066",
    "code-des-pensions-militaires-d-invalidite-et-des-victimes-de-la-guerre": "LEGITEXT000006074068",
    "code-des-ports-maritimes": "LEGITEXT000006074233",
    "code-des-postes-et-des-communications-electroniques": "LEGITEXT000006070987",
    "code-des-procedures-civiles-d-execution": "LEGITEXT000025024948",
    "code-des-relations-entre-le-public-et-l-administration": "LEGITEXT000031366350",
    "code-des-transports": "LEGITEXT000023086525",
    "code-disciplinaire-et-penal-de-la-marine-marchande": "LEGITEXT000006071188",
    "code-du-cinema-et-de-l-image-animee": "LEGITEXT000020908868",
    "code-du-domaine-de-l-etat": "LEGITEXT000006070208",
    "code-du-domaine-de-l-etat-et-des-collectivites-publiques-applicable-a-la-collectivite-territoriale-de-mayotte": "LEGITEXT000006074235",
    "code-du-domaine-public-fluvial-et-de-la-navigation-interieure": "LEGITEXT000006074237",
    "code-du-patrimoine": "LEGITEXT000006074236",
    "code-du-service-national": "LEGITEXT000006071335",
    "code-du-sport": "LEGITEXT000006071318",
    "code-du-tourisme": "LEGITEXT000006074073",
    "code-du-travail-maritime": "LEGITEXT000006072051",
    "code-electoral": "LEGITEXT000006070239",
    "code-forestier-nouveau": "LEGITEXT000025244092",
    "code-general-de-la-fonction-publique": "LEGITEXT000044416551",
    "code-general-de-la-propriete-des-personnes-publiques": "LEGITEXT000006070299",
    "code-general-des-collectivites-territoriales": "LEGITEXT000006070633",
    "code-general-des-impots": "LEGITEXT000006069577",
    "code-general-des-impots-annexe-i": "LEGITEXT000006069568",
    "code-general-des-impots-annexe-ii": "LEGITEXT000006069569",
    "code-general-des-impots-annexe-iii": "LEGITEXT000006069574",
    "code-general-des-impots-annexe-iv": "LEGITEXT000006069576",
    "code-minier": "LEGITEXT000006071785",
    "code-minier-nouveau": "LEGITEXT000023501962",
    "code-monetaire-et-financier": "LEGITEXT000006072026",
    "code-penal": "LEGITEXT000006070719",
    "code-penitentiaire": "LEGITEXT000045476241",
    "code-rural-ancien": "LEGITEXT000006071366",
    "code-rural-nouveau": "LEGITEXT000006071367",
    "livre-des-procedures-fiscales": "LEGITEXT000006069583",
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
