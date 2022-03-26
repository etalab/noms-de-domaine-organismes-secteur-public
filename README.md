# Liste de noms de domaine d'organismes publics

Ce dépôt contient une liste de noms de domaine d'organismes
remplissant des missions de service public.

Le dossier `sources/` contient tous les domaines connus, accessibles
en HTTP ou non.

Le fichier `urls.txt` est une liste d'URLs basée sur les domaines du
dossier `sources/` et répondant `200 OK` en HTTP ou en HTTPS.


# Les domaines inaccessibles en HTTP(S)

La liste des domaines qui sont dans le dossier `sources/` mais ne sont
pas dans le fichier `urls.txt` sont inaccessibles en HTTP ou HTTPS
(n'ont pas d'adresse IP, ne répondent pas en HTTP, répondent autre
chose que 200 en HTTP, ...).

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

Et éventuellement pour consolider dans `urls.txt` (mais c'est long) :

    python scripts/consolidate.py sources/*.txt

pour consolider les sources dans `urls.txt`,
dans lequels seuls les domaines répondant en HTTP par une 200 sont
acceptés.


## Scripts de collecte

Le dossier `scripts/` contient plusieurs scripts de collecte :

- import-base-nationale-sur-les-intercommunalites.py
- import-from-ct-logs.py

## Exemples de réutilisations
### [sources-de-confiance.fr](https://sources-de-confiance.fr)
Sources de confiance est une extension de navigateur qui permet d'identifier instantanément les résultats issus du secteur public dans son moteur de recherche habituel. Une initiative de l'association [Villes Internet](https://villes-internet.net).

### Audit d'accessibilité avec [Asqatasun](https://adullact.org/service-en-ligne-asqatasun)
L'association [Addulact](https://addullact.org) souhaite établir des statistiques concernant le respect du RGAA par les sites des organismes publics.

### Audits techniques variés avec [Dashlord](https://dashlord.incubateur.net/intro/)
DashLord est né à la [Fabrique des ministères sociaux](https://fabrique.social.gouv.fr/) pour répondre aux besoins d'évaluation et de mise en oeuvre des bonnes pratiques de développement web.

# Licence

2020-2021, DINUM et les contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
