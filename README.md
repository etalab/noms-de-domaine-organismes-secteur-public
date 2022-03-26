# Liste de noms de domaine d’organismes publics

Ce dépôt contient une liste de noms de domaine d’organismes
remplissant des missions de service public.


## La liste des noms de domaines

Le dossier `sources/` contient les domaines connus, qu’ils soient
accessibles en HTTP ou non.

Les ajouts et suppresion s’y font soit manuellement soit via des
scripts de collecte.


## La liste des URLs

Le fichier `urls.txt` est une liste d’URLs basée sur les domaines du
dossier `sources/` et répondant `200 OK` en HTTP ou en HTTPS.

Les ajouts et suppresion s’y font automatiquement, il n’est pas
nécessaire de modifier ce fichier manuellement.

Attention, cette liste étant basée sur des noms de domaines
d’organismes publics, certaines pages d’organismes publics comme
https://sites.google.com/site/mairiedemacey/ ne peuvent pas y figurer.


# Les domaines inaccessibles en HTTP/HTTPS

La liste des domaines qui sont dans le dossier `sources/` mais ne sont
pas dans le fichier `urls.txt` sont inaccessibles en HTTP ou HTTPS
(n’ont pas d’adresse IP, ne répondent pas en HTTP, répondent autre
chose que 200 en HTTP…).

Pour obtenir cette liste vous pouvez utiliser :

    export LC_COLLATE=C
    comm -13 <(cut -d/ -f3 urls.txt | sort) <(sort sources/*.txt)


# Contribution

Ajoutez le ou les domaines que vous connaissez dans un des fichiers du
dossier `sources/`.

Pour trier le fichier que vous venez de modifier, vous pouvez utiliser :

    python scripts/sort.py sources/*.txt

Pour vérifier que tout va bien :

    python scripts/check.py

Et éventuellement pour consolider dans `urls.txt` (mais c’est long) :

    python scripts/consolidate.py sources/*.txt

pour consolider les sources dans `urls.txt`,
dans lequels seuls les domaines répondant en HTTP par une 200 sont
acceptés.


## Scripts de collecte

Le dossier `scripts/` contient plusieurs scripts de collecte :

- import-base-nationale-sur-les-intercommunalites.py
- import-from-ct-logs.py


# Licence

2020-2021, DINUM et les contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
