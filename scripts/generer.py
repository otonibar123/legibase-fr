"""Légibase : transforme les XML de la base LEGI (DILA) en fichiers Markdown.

Bibliothèque standard uniquement. Utilisé par update.py.
Principe : un fichier .md par chapitre, les articles en vigueur uniquement,
et les liens « Renvoie à » / « Cité par » dans les deux sens.
"""
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

LEGIFRANCE_CODE = "https://www.legifrance.gouv.fr/codes/article_lc/"
LEGIFRANCE_AUTRE = "https://www.legifrance.gouv.fr/loda/article_lc/"

# Un lien LEGI porte l'état de l'article cité entre parenthèses : V = en vigueur, VD = vigueur différée.
# Les autres états (abrogé, modifié...) désignent d'anciennes versions : on ne les garde pas.
ETATS_LIENS_GARDES = {"V", "VD"}
MAX_EXTERNES = 10  # nombre maximal de renvois vers des textes hors bibliothèque affichés par article

# Codes cherchés dans le texte des articles (détection de mentions, en complément des liens LEGI).
NOMS_CODES = [
    "code civil", "code de procédure civile", "code du travail", "code de la consommation",
    "code de commerce", "code pénal", "code de procédure pénale", "code général des impôts",
    "code de la sécurité sociale", "code de la propriété intellectuelle", "code monétaire et financier",
    "code de l'urbanisme", "code de la construction et de l'habitation",
    "code de l'action sociale et des familles", "code de la santé publique", "code des assurances",
    "code de l'environnement", "code de justice administrative", "code de l'organisation judiciaire",
    "code général des collectivités territoriales", "code des procédures civiles d'exécution",
    "code rural et de la pêche maritime", "code de la route",
]
RE_MENTION_CODE = re.compile(
    r"articles? ((?:[LRD]\.? ?)?\d+(?:-\d+)*) (?:du|de la|de l[’']) ?("
    + "|".join(re.escape(n).replace("'", "['’]") for n in sorted(NOMS_CODES, key=len, reverse=True))
    + ")", re.IGNORECASE)
# « Code civil - art. 1366 (V) », « Loi ... - art. 4 », « Décret n°2007-1708 du 5 décembre 2007 (V) » (texte entier)
RE_LIBELLE = re.compile(r"^(.*?)(?: - art\. (.+?))?(?: \((\w+)\))?$")


# ---------- Petits outils ----------

def slug(texte):
    """« Chapitre Ier bis » -> « chapitre-ier-bis » (sans accents)."""
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "sans-titre"


def prefixe(titre):
    """« Chapitre II : Du ... » -> « Chapitre II » ; « Titre : XIV : Du ... » -> « Titre XIV » (écriture irrégulière de LEGI)."""
    parts = titre.split(":")
    p = parts[0].strip()
    if len(parts) > 2 and len(parts[1].strip()) <= 12:
        p += " " + parts[1].strip()
    return p


def date_fr(iso):
    """2016-10-01 -> 01/10/2016."""
    a, m, j = iso.split("-")
    return f"{j}/{m}/{a}"


def ancre(titre):
    """Ancre GitHub d'un titre : « Article 6-1 » -> « article-6-1 »."""
    return re.sub(r"[^\w\- ]", "", titre.lower()).replace(" ", "-")


def num_cle(num):
    """Tri naturel des numéros d'articles (2, 10, L. 110-1)."""
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", num)]


def en_texte(e, stats):
    """Convertit le HTML simple d'un article en texte (paragraphes, retours à la ligne, tableaux)."""
    sortie = [e.text or ""]
    for c in e:
        if c.tag == "table":
            stats["tableaux_aplatis"] += 1
        if c.tag == "br":
            sortie.append("  \n")
        if c.tag in ("td", "th"):
            sortie.append(" | ")
        sortie.append(en_texte(c, stats))
        if c.tag in ("p", "div", "li", "tr", "table", "ul", "ol"):
            sortie.append("\n\n")
        sortie.append(c.tail or "")
    return "".join(sortie)


def nettoyer(texte):
    lignes = []
    for l in texte.split("\n"):
        saut = l.endswith("  ")  # « deux espaces » = retour à la ligne en Markdown
        l = re.sub(r"[ \t]+", " ", l).strip()
        lignes.append(l + "  " if saut and l else l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lignes)).strip()


def indexer_xml(dossier):
    """id (LEGIARTI..., LEGISCTA...) -> chemin du fichier XML."""
    return {p.stem: p for p in Path(dossier).rglob("*.xml")}


def lire_libelle(libelle):
    """Retourne (texte, article, état) ou None. Normalise les noms de textes irréguliers de LEGI :
    « Code général des impôts, CGI. » -> « Code général des impôts » ; « Code civil - Section 2 : ... » -> lien vers une section."""
    m = RE_LIBELLE.match(libelle)
    if not m:
        return None
    texte, num, etat = m.group(1).strip(), (m.group(2) or "").strip(), m.group(3)
    if texte.startswith("Code"):
        texte, _, reste = texte.partition(" - ")
        if reste and not num:
            num = reste.strip().rstrip(".")
        texte = re.sub(r",\s*[A-Z][A-Z0-9]+\.?$", "", texte).strip()
        if not texte.endswith("..."):  # LEGI coupe les noms longs à 50 caractères avec « ... » : on garde la coupure
            texte = texte.rstrip(". ")
    return texte, num, etat


# ---------- Lecture d'un code ----------

def lire_structure(dossier, id_code, index, stats):
    """Retourne (métadonnées, arbre). Seuls les éléments en vigueur sont gardés.
    Un nœud = {titre, id, enfants: [("art", id) | ("sec", nœud)]} (ordre d'origine conservé)."""
    v = ET.parse(next(Path(dossier).rglob(f"texte/version/{id_code}.xml"))).getroot()
    meta = {
        "nom": v.findtext("META/META_SPEC/META_TEXTE_VERSION/TITREFULL"),
        "id": id_code,
        "derniere_modification": v.findtext("META/META_SPEC/META_TEXTE_CHRONICLE/DERNIERE_MODIFICATION"),
    }
    struct = ET.parse(next(Path(dossier).rglob(f"texte/struct/{id_code}.xml"))).getroot().find("STRUCT")
    arbre = {"titre": meta["nom"], "id": id_code, "enfants": []}
    for e in struct:
        _descendre(e, arbre, index, stats)
    return meta, arbre


def _descendre(lien, parent, index, stats):
    if lien.tag == "LIEN_ART":
        if lien.get("etat") == "VIGUEUR":
            parent["enfants"].append(("art", lien.get("id")))
        else:
            stats["articles_non_gardes_" + lien.get("etat", "?")] += 1
        return
    if lien.get("etat") != "VIGUEUR":
        stats["sections_non_gardees"] += 1
        return
    noeud = {"titre": " ".join((lien.text or "").split()), "id": lien.get("id"), "enfants": []}
    parent["enfants"].append(("sec", noeud))
    fichier = index.get(lien.get("id"))
    if fichier is None:
        stats["sections_sans_fichier"] += 1
        return
    for e in ET.parse(fichier).getroot().find("STRUCTURE_TA"):
        _descendre(e, noeud, index, stats)


def lire_article(chemin, stats):
    a = ET.parse(chemin).getroot()
    m = "META/META_SPEC/META_ARTICLE/"
    bloc, nota = a.find("BLOC_TEXTUEL/CONTENU"), a.find("NOTA/CONTENU")
    liens = [dict(l.attrib, libelle=" ".join((l.text or "").split()))
             for l in a.findall("LIENS/LIEN") if l.get("typelien") == "CITATION"]
    return {
        "id": a.findtext("META/META_COMMUN/ID"),
        "num": (a.findtext(m + "NUM") or "").strip(),
        "debut": a.findtext(m + "DATE_DEBUT"),
        "fin": a.findtext(m + "DATE_FIN"),
        "texte": nettoyer(en_texte(bloc, stats)) if bloc is not None else "",
        "nota": nettoyer(en_texte(nota, stats)) if nota is not None else "",
        "liens": liens,
    }


# ---------- Plan des fichiers ----------

def sections(noeud):
    return [n for t, n in noeud["enfants"] if t == "sec"]


def ids_articles(noeud):
    """Tous les articles d'un nœud, sous-sections comprises, dans l'ordre."""
    res = []
    for t, x in noeud["enfants"]:
        res += [x] if t == "art" else ids_articles(x)
    return res


def planifier(noeud, dossier, fichiers, ancetres):
    """Un chapitre (ou un nœud sans sous-section) = un fichier ; les niveaux au-dessus
    (livre, titre...) = des dossiers. Les sous-sections d'un chapitre restent dans son fichier."""
    nom = _libre(dossier, slug(prefixe(noeud["titre"])), fichiers)
    if noeud["titre"].lower().startswith("chapitre") or not sections(noeud):
        fichiers.append({"chemin": dossier / (nom + ".md"), "noeud": noeud, "ancetres": ancetres})
        return
    sous = dossier / nom
    directs = [e for e in noeud["enfants"] if e[0] == "art"]
    if directs:  # articles posés directement sur un livre/titre qui a aussi des sous-divisions
        fichiers.append({"chemin": sous / "articles-directs.md", "ancetres": ancetres + [noeud["titre"]],
                         "noeud": {"titre": noeud["titre"] + " : articles rattachés directement", "id": noeud["id"],
                                   "enfants": directs}})
    for s in sections(noeud):
        planifier(s, sous, fichiers, ancetres + [noeud["titre"]])


def _libre(dossier, nom, fichiers):
    """Évite deux fichiers ou dossiers de même nom dans un dossier."""
    pris = {f["chemin"].relative_to(dossier).parts[0].removesuffix(".md")
            for f in fichiers if dossier in f["chemin"].parents}
    base, i = nom, 2
    while nom in pris:
        nom, i = f"{base}-{i}", i + 1
    return nom


# ---------- Lecture + liens ----------

def lire_tout(codes, dossiers_xml, sortie, date_base):
    """Lit tous les codes, planifie les fichiers et construit les liens dans les deux sens."""
    stats, donnees, emplacement = Counter(), {}, {}
    for cle, id_code in codes.items():
        index = indexer_xml(dossiers_xml[cle])
        meta, arbre = lire_structure(dossiers_xml[cle], id_code, index, stats)
        fichiers = []
        for s in sections(arbre):
            planifier(s, Path(sortie) / "codes" / cle, fichiers, [])
        directs = [e for e in arbre["enfants"] if e[0] == "art"]
        if directs:
            fichiers.append({"chemin": Path(sortie) / "codes" / cle / "articles-directs.md", "ancetres": [],
                             "noeud": {"titre": meta["nom"] + " : articles non rattachés", "id": id_code, "enfants": directs}})
        articles = {}
        for f in fichiers:
            for id_art in ids_articles(f["noeud"]):
                if id_art not in index:
                    stats["articles_sans_fichier"] += 1
                    continue
                art = lire_article(index[id_art], stats)
                # Garde-fou : l'état « VIGUEUR » ne suffit pas, la période de validité doit couvrir la date de la base.
                if not (art["debut"] <= date_base < art["fin"]):
                    stats["articles_hors_periode_de_validite"] += 1
                    continue
                art["fichier"] = f["chemin"]
                articles[id_art] = art
                if (meta["nom"], art["num"]) in emplacement:
                    stats["numeros_en_double"] += 1
                emplacement[(meta["nom"], art["num"])] = (f["chemin"], "article-" + ancre(art["num"]), id_art, cle)
        donnees[cle] = {"meta": meta, "fichiers": fichiers, "articles": articles}
    aretes, renvoie, cite_par = construire_liens(donnees, emplacement, stats)
    return stats, donnees, emplacement, aretes, renvoie, cite_par


def construire_liens(donnees, emplacement, stats):
    aretes, vus_aretes = [], set()
    renvoie, cite_par = defaultdict(list), defaultdict(list)  # (cle, id article) -> autres articles

    def noeud(texte, num, id_=None):
        e = emplacement.get((texte, num))
        return {"texte": texte, "article": num, "id": e[2] if e else id_}

    def ajouter(de, vers, origine):
        k = (de["texte"], de["article"], vers["texte"], vers["article"])
        if k in vus_aretes or (de["texte"], de["article"]) == (vers["texte"], vers["article"]):
            return
        vus_aretes.add(k)
        aretes.append({"de": de, "vers": vers, "origine": origine})
        if (de["texte"], de["article"]) in emplacement:
            e = emplacement[(de["texte"], de["article"])]
            renvoie[(e[3], e[2])].append(vers)
        if (vers["texte"], vers["article"]) in emplacement:
            e = emplacement[(vers["texte"], vers["article"])]
            cite_par[(e[3], e[2])].append(de)

    for d in donnees.values():
        nom = d["meta"]["nom"]
        for id_art, art in d["articles"].items():
            ici = noeud(nom, art["num"])
            deja = set()
            # 1. Liens officiels LEGI. sens « source » : l'article cite la cible ; sens « cible » : il est cité.
            for l in art["liens"]:
                lu = lire_libelle(l["libelle"])
                if lu is None:
                    stats["libelles_illisibles"] += 1
                    continue
                texte_l, num_l, etat_l = lu
                if etat_l is None:
                    # Sans état, la cible est souvent une ancienne version : on ne garde que « l'article cite un
                    # article de la bibliothèque » (le numéro cité renvoie alors à la version en vigueur).
                    if not (l["sens"] == "source" and (texte_l, num_l) in emplacement):
                        stats["liens_sans_etat_ecartes"] += 1
                        continue
                elif etat_l not in ETATS_LIENS_GARDES:
                    stats["liens_ancienne_version_ecartes"] += 1
                    continue
                autre = noeud(texte_l, num_l, l["id"])
                if l["sens"] == "source":
                    deja.add((texte_l, num_l))
                    ajouter(ici, autre, "LEGI")
                else:
                    ajouter(autre, ici, "LEGI")
            # 2. Mentions « article X du code Y » repérées dans le texte et absentes des liens LEGI.
            for m in RE_MENTION_CODE.finditer(art["texte"]):
                num_l = m.group(1).replace(" ", "").replace(".", "")
                nom_l = m.group(2).lower().replace("’", "'").capitalize()  # « Code du travail »
                if nom_l != nom and (nom_l, num_l) not in deja:
                    deja.add((nom_l, num_l))
                    ajouter(ici, noeud(nom_l, num_l), "texte")
    return aretes, renvoie, cite_par


# ---------- Écriture ----------

def lien_legifrance(texte, id_art):
    if not id_art:
        return None
    if id_art.startswith(("JORFTEXT", "LEGITEXT")):  # lien vers un texte entier
        return "https://www.legifrance.gouv.fr/loda/id/" + id_art
    return (LEGIFRANCE_CODE if texte.lower().startswith("code") else LEGIFRANCE_AUTRE) + id_art


def etiquette(n):
    if not n["article"]:
        return n["texte"]
    if re.match(r"(Sous-)?(Section|Chapitre|Titre|Livre|Paragraphe|Sous-paragraphe|Partie)\b", n["article"]):
        return f"{n['texte']}, {n['article']}"  # lien vers une section, pas vers un article
    return f"art. {n['article']} du {n['texte']}" if n["texte"].lower().startswith("code") \
        else f"{n['texte']}, art. {n['article']}"


def lien_md(depuis, n, emplacement, court=False):
    """Lien relatif vers l'article s'il est dans la bibliothèque, sinon lien Légifrance, sinon texte simple."""
    texte = f"art. {n['article']}" if court and n["article"] else etiquette(n)
    e = emplacement.get((n["texte"], n["article"]))
    if e:
        rel = os.path.relpath(e[0], Path(depuis).parent).replace(os.sep, "/")
        return f"[{texte}]({rel}#{e[1]})"
    url = lien_legifrance(n["texte"], n.get("id"))
    return f"[{texte}]({url})" if url else texte


def uniques(liste):
    vus, res = set(), []
    for n in liste:
        if (n["texte"], n["article"]) not in vus:
            vus.add((n["texte"], n["article"]))
            res.append(n)
    return sorted(res, key=lambda n: (n["texte"], num_cle(n["article"])))


def ecrire_fichier(f, d, cle, emplacement, renvoie, cite_par, dossier_code):
    nom, chemin = d["meta"]["nom"], f["chemin"]
    chemin.parent.mkdir(parents=True, exist_ok=True)
    out = [f"# {f['noeud']['titre']}", "", " › ".join([nom] + f["ancetres"]), ""]
    nb = 0

    def ecrire_noeud(n, fil):
        nonlocal nb
        if fil:
            out.extend([f"## {' › '.join(fil)}", ""])
        for t, x in n["enfants"]:
            if t == "sec":
                ecrire_noeud(x, fil + [x["titre"]])
                continue
            a = d["articles"].get(x)
            if a is None:
                continue
            nb += 1
            etat = f"en vigueur depuis le {date_fr(a['debut'])}"
            if a["fin"] and not a["fin"].startswith("2999"):
                etat += f", jusqu'au {date_fr(a['fin'])}"
            out.extend([f"### Article {a['num']}", f"- Identifiant : {a['id']}", f"- État : {etat}",
                        f"- Source : {lien_legifrance(nom, a['id'])}"])
            for libelle, liste in (("Renvoie à", renvoie), ("Cité par", cite_par)):
                if liste.get((cle, x)):
                    tous = uniques(liste[(cle, x)])
                    # Les renvois vers des textes hors bibliothèque sont plafonnés (le reste est dans renvois.md).
                    interne = [n for n in tous if (n["texte"], n["article"]) in emplacement]
                    externe = [n for n in tous if (n["texte"], n["article"]) not in emplacement]
                    items = [lien_md(chemin, n, emplacement) for n in interne + externe[:MAX_EXTERNES]]
                    if len(externe) > MAX_EXTERNES:
                        rel = os.path.relpath(dossier_code / "renvois.md", chemin.parent).replace(os.sep, "/")
                        items.append(f"… et {len(externe) - MAX_EXTERNES} autres textes (liste complète dans [renvois.md]({rel}))")
                    out.append(f"- {libelle} : " + " ; ".join(items))
            out.extend(["", a["texte"] or "_(texte vide dans la source)_", ""])
            if a["nota"]:
                out.extend(["> Nota : " + a["nota"].replace("\n", "\n> "), ""])

    ecrire_noeud(f["noeud"], [])
    chemin.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return nb


def ecrire_tout(codes, dossiers_xml, sortie, date_base, date_maj):
    sortie = Path(sortie)
    stats, donnees, emplacement, aretes, renvoie, cite_par = lire_tout(codes, dossiers_xml, sortie, date_base)
    for cle, d in donnees.items():
        d["nb_articles"] = sum(ecrire_fichier(f, d, cle, emplacement, renvoie, cite_par, sortie / "codes" / cle)
                                 for f in d["fichiers"])
        d["nb_fichiers"] = len(d["fichiers"])
        _readme_code(cle, d, sortie)
        _renvois(cle, d, aretes, emplacement, sortie)
        (sortie / "codes" / cle / "meta.json").write_text(json.dumps(
            {**d["meta"], "nb_articles": d["nb_articles"], "nb_fichiers": d["nb_fichiers"]},
            ensure_ascii=False, indent=1), encoding="utf-8")
    (sortie / "liens").mkdir(exist_ok=True)
    (sortie / "liens" / "graphe.json").write_text(json.dumps(aretes, ensure_ascii=False, indent=0), encoding="utf-8")
    _carte(aretes, donnees, sortie)
    _index_et_version(donnees, sortie, date_base, date_maj)
    return stats, donnees, aretes


def _readme_code(cle, d, sortie):
    base = sortie / "codes" / cle
    out = [f"# {d['meta']['nom']}", "",
           f"Dernière modification du texte dans LEGI : {date_fr(d['meta']['derniere_modification'])}. "
           f"{d['nb_articles']} articles en vigueur, répartis dans {d['nb_fichiers']} fichiers.", "",
           "Renvois vers et depuis les autres textes : [renvois.md](renvois.md)", ""]
    precedent = []
    for f in d["fichiers"]:
        for i, titre in enumerate(f["ancetres"]):  # affiche les niveaux (livre, titre...) qui changent
            if precedent[i:i + 1] != [titre] or precedent[:i] != f["ancetres"][:i]:
                out.append("  " * i + f"- **{titre}**")
        precedent = f["ancetres"]
        rel = str(f["chemin"].relative_to(base)).replace(os.sep, "/")
        n = len(ids_articles(f["noeud"]))
        out.append("  " * len(f["ancetres"]) + f"- [{f['noeud']['titre']}]({rel}) ({n} article{'s' if n > 1 else ''})")
    (base / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def _renvois(cle, d, aretes, emplacement, sortie):
    nom = d["meta"]["nom"]
    chemin = sortie / "codes" / cle / "renvois.md"
    vers_ext, depuis_ext = defaultdict(list), defaultdict(list)
    for a in aretes:
        if a["de"]["texte"] == nom and a["vers"]["texte"] != nom:
            vers_ext[(a["vers"]["texte"], a["origine"])].append(a)
        elif a["vers"]["texte"] == nom and a["de"]["texte"] != nom:
            depuis_ext[(a["de"]["texte"], a["origine"])].append(a)
    out = [f"# Renvois du {nom} avec les autres textes", "",
           "Renvois entre ce code et d'autres textes (articles en vigueur). Les renvois à l'intérieur du code "
           "figurent dans chaque article (« Renvoie à » / « Cité par »). Origine « LEGI » = lien officiel ; "
           "origine « texte » = mention repérée dans le texte de l'article.", ""]
    for titre, groupe, sens in (("Renvoie à", vers_ext, "vers"), ("Cité par", depuis_ext, "de")):
        out += [f"## {titre}", ""]
        for k in sorted(groupe, key=lambda k: (-len(groupe[k]), k)):
            dans_biblio = any(t == k[0] for (t, _) in emplacement)
            out += [f"### {k[0]} — origine {k[1]} ({len(groupe[k])})" + ("" if dans_biblio else " — pas encore traité"), ""]
            for a in sorted(groupe[k], key=lambda a: num_cle(a[("de" if sens == "vers" else "vers")]["article"])):
                mien, autre = (a["de"], a["vers"]) if sens == "vers" else (a["vers"], a["de"])
                g, dr = lien_md(chemin, mien, emplacement, court=True), lien_md(chemin, autre, emplacement, court=True)
                out.append(f"- {g} → {dr}" if sens == "vers" else f"- {dr} → {g}")
            out.append("")
    chemin.write_text("\n".join(out) + "\n", encoding="utf-8")


def _carte(aretes, donnees, sortie):
    traites = {d["meta"]["nom"] for d in donnees.values()}
    c = Counter((a["de"]["texte"], a["vers"]["texte"]) for a in aretes)
    out = ["# Carte des liens entre les textes", "",
           "Nombre de renvois (articles en vigueur) d'un texte vers un autre.", "",
           "| Texte source | Texte cible | Renvois | Cible dans Légibase |", "|---|---|---|---|"]
    for (de, vers), n in c.most_common(60):
        out.append(f"| {de} | {vers} | {n} | {'oui' if vers in traites else 'pas encore traité'} |")
    out += ["", f"Total : {len(aretes)} renvois entre {len(c)} couples de textes (les 60 plus fréquents sont affichés).", ""]
    (sortie / "liens" / "carte-des-liens.md").write_text("\n".join(out), encoding="utf-8")


def _index_et_version(donnees, sortie, date_base, date_maj):
    out = ["# Index des codes et textes de Légibase", "",
           f"Base LEGI du {date_fr(date_base)}. Actualisation de la bibliothèque : {date_fr(date_maj)}.", "",
           "| Code | Dossier | Articles en vigueur | Fichiers | Dernière modification du texte | Identifiant LEGI |",
           "|---|---|---|---|---|---|"]
    for cle, d in donnees.items():
        out.append(f"| {d['meta']['nom']} | [codes/{cle}/](codes/{cle}/README.md) | {d['nb_articles']} | "
                   f"{d['nb_fichiers']} | {date_fr(d['meta']['derniere_modification'])} | {d['meta']['id']} |")
    (sortie / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    (sortie / "VERSION.md").write_text(
        "# Version de Légibase\n\n"
        f"- Dernière actualisation de la bibliothèque : {date_fr(date_maj)}\n"
        f"- Date de la base LEGI utilisée (DILA, Licence Ouverte 2.0) : {date_fr(date_base)}\n"
        "- Seuls les articles dont l'état est « VIGUEUR » à cette date sont inclus.\n", encoding="utf-8")
