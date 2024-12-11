⚠️ Ce dépôt est désormais maintenu sur [la forge de l'ADULLACT](https://gitlab.adullact.net/dinum/noms-de-domaine-organismes-secteur-public).

# Liste de noms de domaine de la sphère publique

Ce dépôt contient une liste de noms de domaine d’organismes
remplissant des missions de service public.


## La liste des noms de domaines

Le fichier `domains.csv` contient les domaines connus, qu’ils soient
accessibles en HTTP ou non, qu’ils exposent un MX ou non, etc.

C'est le seul fichier modifiable manuellement, les ajouts et
suppressions s’y font soit manuellement, soit via des scripts de
collecte (voir [Contribution](#contribution)).

Les colonnes de  `domains.csv` sont les suivantes :

- `name`: Le nom de domaine
- `http_status`: la réponse à une requête http 80 ou vide
- `https_status`: la réponse à une requête http 443 ou vide
- `SIREN`: Le numéro SIREN de l'établissement ou vide
- `type`: Le type d'établissement ou vide
- `sources`: La source de la donnée
- `script`: Le nom du script de collecte qui a ajouté l'entrée


## La liste des URLs

Le fichier `urls.txt` est une liste d’URLs basée sur les domaines du
fichier `domains.csv` et répondant `200 OK` en HTTP ou en HTTPS
éventuellement après une redirection sur le **même** domaine
(typiquement l’ajout d’un `/fr/`).

Les ajouts et suppressions s’y font automatiquement, il n’est pas
nécessaire de modifier ce fichier manuellement.

Attention, cette liste étant basée sur des **noms de domaines**
d’organismes publics, il n'est pas possible pour des **URL**
d’organismes publics hébergés sur des domaines privés comme
https://sites.google.com/site/mairiedemacey/ d’y figurer.


# Contribution

Ajoutez le ou les domaines que vous connaissez dans le fichier
`domains.csv`.

Pré-requis pour utiliser les scripts python :

    pip install -r scripts/requirements.txt

Ce fichier doit rester trié, pour le trier automatiquement utilisez :

    python scripts/sort.py

Pour vérifier que tout va bien avant de commit :

    python scripts/check.py


## Maintenance des fichiers consolidés

L’action github `refresh` exécute périodiquement :

    python scripts/http_checker.py --partial $(date +%d)/28

Cette commande vérifie 1/28ème des domaines, garantissant que chaque
domaine est testé au moins une fois par mois.

Il est possible d’utiliser `--partial` en dehors de l'action github.
Par exemple, pour tout actualiser en deux invocations :

    python scripts/http_checker.py --partial 1/2  # Actualise une première moitiée,
    python scripts/http_checker.py --partial 2/2  # puis la seconde.


## Scripts de collecte

Le dossier `scripts/` contient plusieurs scripts de collecte :

- `import-base-nationale-sur-les-intercommunalites.py`
- `import-from-ct-logs.py`

Vous pouvez rédiger de nouveaux scripts de collecte, ils ne sont pas
exécutés automatiquement.


## Exemples de réutilisations

### [sources-de-confiance.fr](https://sources-de-confiance.fr)

Sources de confiance est une extension de navigateur qui permet d’identifier instantanément les résultats issus du secteur public dans son moteur de recherche habituel. Une initiative de l’association [Villes Internet](https://villes-internet.net).

### Audit d’accessibilité avec [Asqatasun](https://adullact.org/service-en-ligne-asqatasun)

L’association [ADULLACT](https://adullact.org/) souhaite établir des statistiques concernant le respect du RGAA par les sites des organismes publics.

### Audits techniques variés avec [DashLord](https://dashlord.incubateur.net/intro/)

DashLord est né à la [Fabrique des ministères sociaux](https://fabrique.social.gouv.fr/) pour répondre aux besoins d’évaluation et de mise en œuvre des bonnes pratiques de développement web.

### [Établi](https://etabli.incubateur.net/) : un annuaire des initiatives publiques numériques

Service qui référence les initiatives publiques numériques françaises, ce afin d'augmenter leur découvrabilité et leur (ré)utilisation. Il a été réalisé au sein de l'équipe [beta.gouv.fr](https://beta.gouv.fr/).

# Licence

2020-2023, DINUM et les contributrices et contributeurs du dépôt.

Le contenu de ce dépôt est sous [licence Ouverte 2.0](LICENCE.md).
