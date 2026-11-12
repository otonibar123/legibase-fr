# Légibase : le droit français en Markdown

Légibase est une bibliothèque des codes et textes juridiques français, en fichiers Markdown, conçue pour être utilisée comme **skill Claude**. Vous posez une question de droit, Claude cherche dans la bibliothèque et répond avec le texte de loi exact et sa source officielle (Légifrance).

**Ce que Légibase fait** : retrouver un article de loi, suivre les renvois entre articles, citer la source et la date de version.

**Ce que Légibase ne fait pas** : ce n'est pas un avocat et ce n'est pas un conseil juridique. Pour une situation précise, consultez un avocat ou un professionnel du droit.

## Contenu

La liste des codes disponibles, avec le nombre d'articles et les dates, est dans [INDEX.md](INDEX.md). La date de la dernière actualisation est dans [VERSION.md](VERSION.md). Seul le droit **en vigueur** est inclus.

## Installation comme skill Claude

1. Téléchargez le dossier depuis GitHub (bouton « Code » puis « Download ZIP ») et décompressez-le.
2. Installez le dossier comme skill Claude :
   - **Claude Code** : placez le dossier `legibase-fr` dans `~/.claude/skills/`.
   - **Claude.ai** : compressez le dossier en ZIP et ajoutez-le dans les réglages, rubrique « Skills ».
3. Ouvrez une conversation : la skill se déclenche d'elle-même pour les questions de droit français.

## Poser une question

- « Que dit l'article 1240 du code civil ? »
- « Quels articles du code civil encadrent la responsabilité extracontractuelle ? »
- « Quels textes citent l'article 1103 du code civil ? »

## Actualiser

Les lois changent. Pour avoir la dernière version, retéléchargez le dossier depuis GitHub et remplacez l'ancien. La date de la version installée est dans [VERSION.md](VERSION.md).

## Sources et licence

- Textes : base LEGI de la DILA (Direction de l'information légale et administrative), publiée en open data sous [Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/), sur `echanges.dila.gouv.fr/OPENDATA/LEGI/`.
- Chaque article renvoie à sa page Légifrance, qui reste la référence officielle.

## Pour le mainteneur

`python3 -I scripts/update.py` télécharge la dernière base LEGI et régénère tous les fichiers (Python 3, bibliothèque standard uniquement). Les téléchargements bruts restent dans `.cache/`, exclu de GitHub.
