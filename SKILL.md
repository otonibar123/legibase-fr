---
name: legibase-fr
description: Bibliothèque du droit français en Markdown (codes et textes officiels, avec renvois entre articles). À utiliser pour toute question sur le droit français, un article de code, une loi, un décret ou une décision de justice française.
---

# Légibase : droit français

Bibliothèque de textes juridiques français en vigueur, issus de la base LEGI de la DILA (Légifrance, Licence Ouverte 2.0).
Chaque article indique son identifiant officiel, sa date de version et son lien Légifrance.

## Honnêteté : la règle la plus importante

Dire toujours la vérité. Ne jamais inventer. Cette règle passe avant toutes les autres.

- **Ne jamais inventer** un article, un numéro d'article, un texte de loi, une date, une décision de justice, un numéro de pourvoi ou un lien.
- **Ne jamais répondre de mémoire.** Ne citer que ce qui est écrit dans les fichiers de la bibliothèque.
- **Si le code n'est pas dans la bibliothèque** (absent de `INDEX.md`), le dire clairement : « Ce code n'est pas encore dans Légibase. » Puis donner la liste des codes disponibles et proposer de vérifier sur Légifrance.
- **Si l'article ou la réponse n'est pas trouvé**, le dire clairement : « Je n'ai pas trouvé cette information dans Légibase. » Ne pas combler le vide.
- **Si la réponse est incertaine** (texte ambigu, plusieurs articles possibles, jurisprudence contradictoire), le dire et expliquer pourquoi, au lieu de trancher.
- **Séparer toujours** ce qui vient du texte (cité avec sa source) de ce qui est une explication ou une interprétation (présentée comme telle).
- **Ne jamais exagérer** : ne pas présenter une interprétation comme une certitude, ni promettre l'issue d'un litige.
- Mieux vaut répondre « je ne sais pas » que donner une réponse fausse.

## Comment chercher

1. Lire `INDEX.md` : liste des codes disponibles, nombre d'articles, dates.
2. Ouvrir `codes/<code>/README.md` : plan du code (livres, titres, chapitres) avec un lien vers chaque fichier.
3. Ouvrir le fichier du chapitre concerné. Un article commence par `### Article <numéro>`. Pour aller vite, chercher `### Article 1103` avec grep plutôt que de lire tout le fichier.
4. Suivre les renvois : chaque article indique « Renvoie à » (articles qu'il cite) et « Cité par » (articles et textes qui le citent). Les suivre pour donner une réponse complète (par exemple un article du code du travail qui renvoie au code civil). `codes/<code>/renvois.md` liste tous les renvois vers et depuis les autres textes, et `liens/graphe/<code>.json` tous les renvois du code.
5. Citer la jurisprudence liée avec sa juridiction, sa date et son numéro de pourvoi (dossier `jurisprudence/`, s'il existe pour le thème).

Ne pas lire en entier les gros fichiers : chercher l'article voulu, puis lire seulement autour.

## Règles obligatoires pour CHAQUE réponse

1. **Le texte et sa source** : citer l'article exact, sa date de version (« en vigueur depuis le … ») et son lien Légifrance.
2. **La date de la bibliothèque** : indiquer la date de dernière actualisation lue dans `VERSION.md`.
3. **L'actualisation** : si cette date a plus d'un mois, dire que des textes ont pu changer depuis, et proposer à l'utilisateur de télécharger la dernière version sur GitHub ou de vérifier l'article sur Légifrance.
4. **L'avertissement** : terminer par un rappel court, par exemple : « Légibase est un outil d'aide pour trouver les textes de loi. Ce n'est pas un avocat et ce n'est pas un conseil juridique. Pour une situation précise, consultez un avocat ou un professionnel du droit. »

## Limites à connaître

- Seuls les articles **en vigueur** à la date de la bibliothèque sont présents : les anciennes versions et les articles abrogés n'y sont pas.
- Les articles dont l'entrée en vigueur est différée (à une date future) ne sont pas inclus tant qu'ils ne sont pas en vigueur.
- Pour les renvois vers des textes qui ne sont pas dans la bibliothèque, seul un lien Légifrance est donné : le texte lui-même n'est pas disponible ici.
