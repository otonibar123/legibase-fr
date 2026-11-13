# Légibase — bibliothèque du droit français en Markdown

## Objectif

Construire `legibase-fr/`, une skill Claude simple qui contient les codes et textes juridiques
français en Markdown. Chaque code a son propre dossier, et les liens entre les articles
(renvois, citations, jurisprudence) sont identifiés et navigables.

**Usage visé** : une personne télécharge le dossier depuis GitHub, l'installe comme skill,
pose ses questions, et Claude répond avec le texte de loi et sa source officielle.

## Principe de simplicité

- **Pour l'utilisateur** : aucune installation technique. Les fichiers .md sont déjà générés
  et publiés sur GitHub. Il télécharge, installe la skill, pose ses questions.
- **Pour le mainteneur** : Python sert uniquement à générer et actualiser les fichiers.
- **Technologies** : Python 3 avec la **bibliothèque standard uniquement**
  (`urllib`, `tarfile`, `xml.etree.ElementTree`, `json`, `re`, `pathlib`).
  Pas de paquets à installer, pas de base de données, pas de serveur.
- Le code doit rester court, lisible et commenté en français.
- Si un choix technique complique les choses, choisir la solution la plus simple et me le signaler.

## Règles absolues

- **Sources officielles uniquement.** Ne jamais écrire un texte de loi ou une décision de mémoire.
  Tout texte doit venir des sources listées ci-dessous.
- **Un code à la fois.** Ne jamais commencer le code suivant sans mon accord explicite.
- **Seulement le droit en vigueur.** Ne garder que les articles dont l'état est « VIGUEUR ».
- **Traçabilité.** Chaque article indique son identifiant officiel, sa date de version et son lien Légifrance.
- **Honnêteté pendant la construction.** Me dire toujours la vérité sur l'avancement : ne jamais
  annoncer qu'une étape est terminée si elle ne l'est pas, signaler chaque erreur, chaque article
  non traité et chaque doute, et ne jamais remplacer une donnée manquante par une donnée inventée.

## Sources

- **Textes** : base LEGI de la DILA (open data, Licence Ouverte 2.0),
  sur `echanges.dila.gouv.fr/OPENDATA/LEGI/`.
  Avant d'écrire un parseur, regarder comment des projets open source lisent ces XML
  (par exemple les projets Legilibre sur GitHub) pour comprendre le format,
  mais écrire notre propre script simple, sans dépendance.
- **Jurisprudence** : base CASS de la DILA (open data) ou API Judilibre de la Cour de cassation
  (via la plateforme PISTE, compte gratuit). Ne récupérer que la jurisprudence des thèmes que je choisis.
- **Règlement Intérieur National (RIN) des avocats** : il n'est pas dans LEGI. Le récupérer depuis
  le site du Conseil National des Barreaux et indiquer sa date de version.

## Structure

```
legibase-fr/
├── SKILL.md                      # mode d'emploi pour Claude (voir plus bas)
├── README.md                     # installation et usage, pour les humains
├── VERSION.md                    # date de la dernière actualisation + date de la base LEGI utilisée
├── INDEX.md                      # liste des codes, date de version, nombre d'articles
├── codes/
│   ├── code-civil/
│   │   ├── README.md             # plan du code (livres > titres > chapitres) avec liens
│   │   ├── livre-III/titre-III/chapitre-I.md   # un fichier par chapitre
│   │   └── renvois.md            # liens vers et depuis les autres codes
│   ├── code-de-procedure-civile/
│   ├── code-du-travail/
│   └── ...
├── textes-non-codifies/          # ex : loi n° 71-1130, décret n° 91-1197, RIN
├── jurisprudence/
│   └── <theme>/                  # une fiche .md par décision
├── liens/
│   ├── graphe.json               # tous les renvois (article source -> article cible)
│   └── carte-des-liens.md        # synthèse lisible : quels codes renvoient à quels codes
└── scripts/
    └── update.py                 # régénère tout et met à jour VERSION.md
```

Un fichier par chapitre, pas un fichier par article.
Le dossier `scripts/` sert au mainteneur ; l'utilisateur n'en a pas besoin.

## Format d'un article

```markdown
### Article 1103
- Identifiant : LEGIARTI...
- État : en vigueur depuis le JJ/MM/AAAA
- Source : <lien Légifrance>
- Renvoie à : [art. X du code Y](chemin/relatif.md#article-x)
- Cité par : [art. Z du code W](chemin/relatif.md#article-z)
- Jurisprudence : [Cass. 2e civ., JJ/MM/AAAA, n° XX-XX.XXX](../../jurisprudence/theme/fiche.md)

<texte intégral de l'article>
```

## Format d'une fiche de jurisprudence

```markdown
# Cass. 2e civ., JJ/MM/AAAA, n° XX-XX.XXX
- Juridiction et formation :
- Date :
- Numéro de pourvoi :
- Solution : cassation / rejet / ...
- Articles visés : [liens vers les articles de la bibliothèque]
- Source : <lien Judilibre ou Légifrance>

## Résumé
<résumé fidèle de la décision, en distinguant les faits, la question posée et la solution>
```

## Liens entre les textes

1. Utiliser d'abord les liens officiels présents dans les XML LEGI (balises `LIENS` :
   citations, modifications, codifications).
2. Compléter en détectant dans le texte les mentions du type
   « article L. 1234-5 du code du travail » ou « article 10 de la loi du 31 décembre 1971 ».
3. Écrire chaque lien dans les deux sens (« Renvoie à » et « Cité par »), dans les fichiers
   `renvois.md` de chaque code et dans `liens/graphe.json`.
4. Relier chaque décision de jurisprudence aux articles qu'elle vise.
5. Quand un nouveau code est ajouté, mettre à jour les liens « Cité par » des codes déjà traités.
6. Lister à part les renvois vers des codes pas encore traités, pour les compléter plus tard.

## État d'avancement

- **Code civil : terminé** (généré le 11/11/2026, base LEGI du 08/11/2026) : 2 896 articles en vigueur,
  191 fichiers de chapitre, 4,4 Mo publiables. Texte vérifié identique aux XML (0 écart), 0 lien relatif cassé.
- `SKILL.md`, `README.md`, `INDEX.md`, `VERSION.md`, `liens/` et `scripts/` existent déjà.
- **Dépôt GitHub** : `otonibar123/legibase-fr` (public depuis le 13/11/2026, branche `main`, premier commit `dbdf26f` le 12/11/2026).
  Le jeton `GITHUB_TOKEN` de l'ordinateur ne donne accès qu'à ce compte. L'utilisateur a évoqué un autre compte
  (« ootnibar123 », peut-être une faute de frappe) : il fera lui-même `! gh auth login` plus tard, puis le dépôt
  sera recréé dessus si besoin.
- **iCloud** : le dossier est dans `~/Documents`, synchronisé par iCloud, qui a créé un dossier vide
  `codes/code-civil 3` après une régénération (supprimé). Recommandation en attente : déplacer le projet
  dans `~/Projects/` (puis mettre à jour le `CLAUDE.md` parent).
- **Prochain code proposé : code de procédure civile.** Ne pas le commencer sans l'accord explicite de l'utilisateur.
- **Points ouverts** :
  - vérifier à la main qu'un lien Légifrance « Cité par » vers un texte non codifié
    (`https://www.legifrance.gouv.fr/loda/article_lc/<id>`) s'ouvre bien ; sinon changer le format dans `lien_legifrance()` ;
  - détecter les mentions de lois citées par date (« article 10 de la loi du 31 décembre 1971 ») : à faire avec
    le bloc « profession d'avocat » (étape 3) ;
  - jurisprudence : pas commencée (attendre le choix des thèmes).

## Commandes

Se placer dans `legibase-fr/` (Python 3, bibliothèque standard uniquement ; `-I` isole l'interpréteur des fichiers téléchargés).

```
python3 -I scripts/update.py                       # télécharge la dernière base LEGI, extrait, régénère tout
python3 -I scripts/update.py --sans-telechargement # réutilise l'archive déjà dans .cache/
python3 -I scripts/update.py --sans-extraction     # réutilise aussi les XML déjà extraits (quelques secondes)
```

- Pour ajouter un code : l'ajouter au dictionnaire `CODES` de `scripts/update.py` (`dossier: identifiant LEGITEXT`),
  un seul à la fois et avec l'accord de l'utilisateur. Tout est régénéré à chaque lancement, donc les liens
  « Cité par » des codes déjà traités se mettent à jour d'eux-mêmes.
- **`.cache/`** (2 Go, exclu de GitHub par `.gitignore`) contient l'archive `Freemium_legi_global_*.tar.gz` (1,26 Go)
  et un dossier `extrait-<code>/` par code. L'extraction relit toute l'archive : compter plus de 10 minutes
  (lancer en arrière-plan). Les scripts sont dans `scripts/generer.py` (lecture XML, plan des fichiers, liens,
  écriture) et `scripts/update.py` (téléchargement, extraction, appel).
- Après chaque génération, vérifier par script (sans afficher les fichiers) : nombre d'articles = nombre d'articles
  « VIGUEUR » des XML, texte identique à la source, liens relatifs et ancres existants.

## Particularités de la base LEGI (à connaître avant de modifier le parseur)

- **Emplacement** : `legi/global/code_et_TNC_en_vigueur/code_en_vigueur/LEGI/TEXT/.../<LEGITEXT>/`, avec
  `texte/struct`, `texte/version`, `section_ta/` et `article/`. Une section peut contenir à la fois des
  sous-sections et des articles ; les anciennes versions sont mélangées aux versions en vigueur.
- **État et dates** : l'état « VIGUEUR » ne suffit pas. Il faut aussi que la période de validité (début, fin) couvre
  la date de la base (cas de l'article 214 du code civil : 2e version « VIGUEUR » avec début = fin = 1976).
  Les articles « VIGUEUR_DIFF » (vigueur future) sont exclus.
- **Sens des liens** (`typelien="CITATION"`) : `sens="source"` = l'article cite la cible (« Renvoie à ») ;
  `sens="cible"` = l'article est cité par l'autre texte (« Cité par »).
- **Libellés de lien** : « Code civil - art. 1366 (V) ». L'état entre parenthèses (V, VD = gardés ; M, Ab... = anciennes
  versions, écartés). Sans état : gardé seulement si l'article cité est dans la bibliothèque. Noms de textes irréguliers
  (« Code général des impôts, CGI. », liens vers une section) normalisés par `lire_libelle()` ; les noms longs sont
  coupés par LEGI à 50 caractères avec « ... » (conservés tels quels).
- **Titres** : LEGI écrit parfois « Titre : XIV : Des ... » (`prefixe()` gère ce cas pour les noms de fichiers).
- **Plafond d'affichage** : au plus 10 renvois vers des textes hors bibliothèque par article (`MAX_EXTERNES`) ;
  la liste complète est dans `renvois.md`.

## Actualisation

- `scripts/update.py` télécharge la dernière base LEGI, régénère les fichiers et écrit dans
  `VERSION.md` la date de l'actualisation et la date de la base LEGI utilisée.
- Pour l'utilisateur, actualiser = télécharger la dernière version du dossier sur GitHub.
- Option à proposer à la fin du projet (seulement si c'est simple) : une GitHub Action qui lance
  `update.py` une fois par mois et publie la nouvelle version automatiquement.

## Méthode de travail : un code à la fois

- **Étape 1** : préparer les outils (téléchargement de LEGI, parseur, `scripts/update.py`),
  puis générer uniquement le code civil.
- **À la fin de chaque code**, s'arrêter et me donner :
  - le nombre d'articles et de fichiers créés ;
  - la taille du dossier de ce code et la taille totale de `legibase-fr/` ;
  - 2 ou 3 exemples d'articles avec leurs renvois, pour que je vérifie le format ;
  - les renvois vers des codes pas encore traités ;
  - le code proposé ensuite.

  Puis **attendre ma réponse** avant de continuer.
- **Ordre proposé** (je peux le changer) :
  1. code civil
  2. code de procédure civile
  3. textes sur la profession d'avocat (loi n° 71-1130, décret n° 91-1197, RIN)
  4. code du travail
  5. code de la consommation
  6. code de commerce
- **Taille** : si la bibliothèque devient trop grande pour une skill, me prévenir avant de continuer
  et proposer de la séparer en plusieurs skills (une par domaine).

## Économie de tokens

- Ne jamais afficher ni lire en entier les fichiers XML de LEGI ou les fichiers .md générés.
- Pour vérifier un résultat, utiliser des scripts qui affichent seulement des comptes,
  des tailles et quelques lignes d'exemple.
- Tester le parseur sur un petit échantillon (quelques articles) avant de le lancer sur tout un code.

## Contenu du SKILL.md à générer

### Frontmatter

La description doit dire quand utiliser la skill : toute question sur le droit français,
un article de code, une loi ou une décision de justice française.

### Comment chercher

- Chercher d'abord dans `INDEX.md`, puis dans le dossier du code concerné.
- Suivre les renvois pour donner une réponse complète (ex : un article du code du travail
  qui renvoie au code civil).
- Citer la jurisprudence liée avec sa juridiction, sa date et son numéro de pourvoi.
- Séparer clairement ce que dit le texte et ce qui relève de l'interprétation.
- Si la réponse n'est pas dans la bibliothèque, le dire clairement au lieu de répondre de mémoire.

### Honnêteté : la règle la plus importante

Dire toujours la vérité. Ne jamais inventer. Cette règle passe avant toutes les autres.

- **Ne jamais inventer** un article, un numéro d'article, un texte de loi, une date,
  une décision de justice, un numéro de pourvoi ou un lien.
- **Ne jamais répondre de mémoire.** Ne citer que ce qui est écrit dans les fichiers de la bibliothèque.
- **Si le code n'a pas été téléchargé** (absent de `INDEX.md`), le dire clairement :
  « Ce code n'est pas encore dans Légibase. » Puis donner la liste des codes disponibles
  et proposer de vérifier sur Légifrance.
- **Si l'article ou la réponse n'est pas trouvé**, le dire clairement :
  « Je n'ai pas trouvé cette information dans Légibase. » Ne pas combler le vide.
- **Si la réponse est incertaine** (texte ambigu, plusieurs articles possibles, jurisprudence
  contradictoire), le dire et expliquer pourquoi, au lieu de trancher.
- **Séparer toujours** ce qui vient du texte (cité avec sa source) de ce qui est une explication
  ou une interprétation (présentée comme telle).
- **Ne jamais exagérer** : ne pas présenter une interprétation comme une certitude,
  ni promettre l'issue d'un litige.
- Mieux vaut répondre « je ne sais pas » que donner une réponse fausse.

### Règles obligatoires pour CHAQUE réponse

1. **Le texte et sa source** : citer l'article exact, sa date de version et son lien Légifrance.
2. **La date de la bibliothèque** : indiquer la date de dernière actualisation lue dans `VERSION.md`.
3. **L'actualisation** : si cette date a plus d'un mois, dire que des textes ont pu changer depuis,
   et proposer à l'utilisateur de télécharger la dernière version sur GitHub
   ou de vérifier l'article sur Légifrance.
4. **L'avertissement** : terminer par un rappel court, par exemple :
   « Légibase est un outil d'aide pour trouver les textes de loi. Ce n'est pas un avocat et ce n'est
   pas un conseil juridique. Pour une situation précise, consultez un avocat ou un professionnel du droit. »

## README.md à générer (pour les humains)

Court et simple, en français :
- ce que fait Légibase, et ce qu'elle ne fait pas (pas un avocat, pas un conseil juridique) ;
- comment l'installer comme skill Claude, étape par étape ;
- comment poser une question (2 ou 3 exemples) ;
- comment actualiser (télécharger la dernière version) ;
- les sources officielles et leur licence (Licence Ouverte 2.0 pour les données de la DILA).
