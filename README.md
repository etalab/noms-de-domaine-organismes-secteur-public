# Liste de noms de domaine d'organismes publics

Ce dépôt contient une liste de noms de domaine pointant vers des
organismes remplissant des missions de service public.


# Contribution

Ajoutez le ou les domaines que vous connaissez dans un des fichiers du
dossier `sources/` et exécutez :

    python scripts/consolidate.py sources/*.txt

pour consolider les sources dans `domaines-organismes-publics.txt`,
dans lequels seuls les domaines répondant en HTTP par une 200 sont
acceptés.


# Licence

2020, DINUM et les contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
