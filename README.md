# Liste de noms de domaine d'organismes publics

Ce dépôt contient une liste de noms de domaine pointant vers des
organismes remplissant des missions de service public.

Les domaines dans le fichier `domaines-organismes-publics.txt` doivent
être accessible en HTTP ou HTTPS.

Le dossier `sources/` contient tous les domaines connus, accessibles ou non.


# Les domaines inaccessibles

La liste des domaines qui sont dans le dossier `sources/` mais ne sont
pas dans le fichier `domaines-organismes-publics.txt` sont
inaccessibles en HTTP ou HTTPS (n'ont pas d'adresse IP, ne répondent
pas, ...).

Pour obtenir cette liste vous pouvez utiliser :

    export LC_COLLATE=C
    comm -13 domaines-organismes-publics.txt <(sort sources/*.txt)


# Contribution

Ajoutez le ou les domaines que vous connaissez dans un des fichiers du
dossier `sources/` et exécutez :

    python scripts/consolidate.py sources/*.txt

pour consolider les sources dans `domaines-organismes-publics.txt`,
dans lequels seuls les domaines répondant en HTTP par une 200 sont
acceptés.


# Licence

2020-2021, DINUM et les contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
