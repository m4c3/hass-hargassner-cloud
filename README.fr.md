<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Logo Hargassner Cloud" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | <a href="README.md">English</a> | Français | <a href="README.es.md">Español</a> | <a href="README.nb.md">Norsk bokmål</a> | <a href="README.pl.md">Polski</a> | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud pour Home Assistant

Hargassner Cloud est une intégration personnalisée pour Home Assistant. Elle
lit les données de chauffage du portail web Hargassner et les expose sous forme
de capteurs et de capteurs binaires.

> [!IMPORTANT]
> Ce projet indépendant n’est ni affilié à Hargassner ni approuvé par
> Hargassner. Il utilise une API cloud non documentée qui peut changer.

## Fonctionnalités

- Configuration dans l’interface avec l’adresse e-mail et le mot de passe du
  compte Hargassner
- Détection et sélection automatiques des installations
- Aucune recherche manuelle d’un ID client ou secret client
- Actualisation automatique des identifiants publics du client web
- Interrogation centralisée avec `DataUpdateCoordinator`
- Réauthentification Home Assistant en cas d’identifiants personnels refusés
- Intervalle, zone suggérée et correspondances de champs configurables
- Diagnostics et journaux expurgés
- Affichage de la version logicielle de l’appareil lorsqu’elle est fournie par l’API cloud
- Détection sans limite artificielle des chaudières et circuits numérotés

## Systèmes testés

- **NanoPK :** connexion, détection des installations et récupération des widgets
  testées en conditions réelles
- **Neo-HV 20 :** validé avec de vraies données de diagnostic Home Assistant
  expurgées et un test de régression synthétique de sa topologie de widgets

D’autres systèmes Hargassner peuvent fonctionner s’ils exposent des widgets cloud
compatibles, mais ils n’ont pas encore été vérifiés par ce projet.

## Entités

Les entités dépendent des widgets renvoyés par l’installation : chauffage,
température extérieure, ballon tampon, chaudières et circuits de chauffage.
Tous les widgets `BOILER` numérotés et tous les types
`HEATING_CIRCUIT_*` numérotés sont détectés. Les pompes, charges forcées,
températures et états correspondants sont créés automatiquement.

Les températures actuelle/cible de la chaudière et des ballons ainsi que les
températures de source et de demande du régulateur Neo-HV sont également prises
en charge lorsqu’elles sont disponibles. Les canaux historiques optionnels
(oxygène, retour, pression, stock de granulés et humidité) ne sont pas encore
créés comme entités.

Plusieurs ballons tampons ne sont pas encore pris en charge, car leur schéma de
numérotation n’a pas encore été observé.

## Installation

### HACS

1. Ouvrir **HACS → Intégrations**.
1. Choisir **Dépôts personnalisés** dans le menu à trois points.
1. Ajouter `https://github.com/m4c3/hass-hargassner-cloud` comme
   **Intégration**.
1. Installer **Hargassner Cloud** et redémarrer Home Assistant.
1. Ouvrir **Paramètres → Appareils et services → Ajouter une intégration**.

### Installation manuelle

Copier `custom_components/hargassner_cloud` dans le répertoire
`custom_components` de Home Assistant, puis redémarrer Home Assistant et
ajouter l’intégration depuis l’interface.

## Configuration et options

La configuration demande l’adresse e-mail et le mot de passe du compte
Hargassner. L’URL par défaut est `https://web.hargassner.at`. Si le compte
contient plusieurs installations, une sélection est affichée.

Les options permettent de modifier l’intervalle d’actualisation (300 secondes
par défaut, 30 secondes minimum), la zone suggérée et les remplacements de
correspondance au format JSON. L’enregistrement recharge automatiquement
l’intégration.

## Authentification

L’intégration extrait les identifiants publics du client web depuis la page de
connexion Hargassner actuelle. Aucun secret client public n’est intégré au
dépôt. Le mot de passe n’est envoyé qu’à l’URL Hargassner configurée.

Un mot de passe refusé lance la réauthentification standard. Une modification
incompatible du portail crée plutôt un problème dans Réparations afin de ne pas
demander inutilement un nouveau mot de passe.

## Diagnostics et confidentialité

Les diagnostics ne contiennent que les noms de widgets, les noms de champs,
leurs types et un état API expurgé. Les mots de passe, jetons, identifiants
d’installation, valeurs de fonctionnement et URL de ressources sont exclus.
Vérifiez néanmoins le fichier avant de le publier.

## Dépannage

- **Échec de connexion :** vérifier le compte sur
  [`web.hargassner.at`](https://web.hargassner.at).
- **Connexion impossible :** vérifier l’accès HTTPS et un éventuel entretien
  du portail.
- **Entités manquantes :** télécharger les diagnostics et vérifier les noms de
  widgets et de champs; une correspondance JSON peut les adapter.

## Licence

Le code source et les illustrations originales du projet sont sous licence MIT.
Voir [LICENSE](LICENSE). Hargassner est une marque de son propriétaire respectif.
