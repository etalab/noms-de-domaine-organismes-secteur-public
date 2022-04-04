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
dossier `sources/` et répondant `200 OK` en HTTP ou en HTTPS
éventuellement après une redirection sur le **même** domaine
(typiquement l’ajout d’un `/fr/`).

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

Il est possible de savoir ce qui cause l’innaccessibilité en regardant
dans `domains.csv` :

    $ head -n 1 domains.csv; grep mairie-valognes.fr domains.csv
    name,http_last_check,http_status,https_last_check,https_status
    mairie-valognes.fr,2022-04-04,301 Moved Permanently https://www.valognes.fr/,2022-04-04,[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:997)

Ici on apprend qu’en HTTP le domaine redirige en HTTPS, et qu’en HTTPS
le certificat est expiré.


# Contribution

Ajoutez le ou les domaines que vous connaissez dans un des fichiers du
dossier `sources/`.

Pour trier le fichier que vous venez de modifier, vous pouvez utiliser :

    python scripts/sort.py sources/*.txt

Pour vérifier la cohérence des fichiers :

    python scripts/check.py

Et éventuellement pour consolider dans `urls.txt` :

    python scripts/http_checker.py
    python scripts/domains_csv_to_urls_txt.py

Le premier met à jour le fichier `domains.csv`, et le second crée
`urls.txt` à partir de `domains.csv`.


## Scripts de collecte

Le dossier `scripts/` contient plusieurs scripts de collecte :

- `import-base-nationale-sur-les-intercommunalites.py`
- `import-from-ct-logs.py`


## Exemples de réutilisations

### [sources-de-confiance.fr](https://sources-de-confiance.fr)

Sources de confiance est une extension de navigateur qui permet d'identifier instantanément les résultats issus du secteur public dans son moteur de recherche habituel. Une initiative de l'association [Villes Internet](https://villes-internet.net).

### Audit d'accessibilité avec [Asqatasun](https://adullact.org/service-en-ligne-asqatasun)

L'association [ADULLACT](https://adullact.org/) souhaite établir des statistiques concernant le respect du RGAA par les sites des organismes publics.

### Audits techniques variés avec [DashLord](https://dashlord.incubateur.net/intro/)

DashLord est né à la [Fabrique des ministères sociaux](https://fabrique.social.gouv.fr/) pour répondre aux besoins d'évaluation et de mise en oeuvre des bonnes pratiques de développement web.


# Licence

2020-2021, DINUM et les contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
