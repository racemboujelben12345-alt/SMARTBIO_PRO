# SMARTBIO_PRO — Plan directeur scientifique et registre de suivi

> **Projet :** Quality-Aware Adaptive Optical Biomarker Research  
> **Périmètre :** estimation optique de l'hémoglobine (Hb) et de la bilirubine à partir d'images de smartphone.  
> **Statut :** prototype de recherche uniquement — non validé pour le diagnostic clinique.  
> **Règle de pilotage :** le plan suit le dépôt existant. Il ne prescrit pas de réécriture globale ni de déplacement massif de fichiers.

## Question centrale de recherche

Une calibration optique adaptative, associée à un contrôle de qualité et à une estimation de l'incertitude, améliore-t-elle la robustesse des estimations d'Hb et de bilirubine lorsque les appareils et les conditions d'acquisition changent ?

Cette question sera évaluée séparément pour chaque biomarqueur. Un résultat sur Hb ne prouve pas un bénéfice pour la bilirubine.

## Règles scientifiques non négociables

- Aucune performance annoncée sans exécution vérifiable et protocole documenté.
- Aucune modification de résultats pour faire réussir les tests.
- Aucune donnée synthétique présentée comme réelle.
- Aucun mélange silencieux des sources, des unités, de Hb et de bilirubine.
- Aucune fuite patient entre partitions ; le jeu final de test reste gelé.
- Les métadonnées inconnues restent inconnues : pas de valeurs inventées par défaut.
- Les références de laboratoire, les valeurs autodéclarées et les mesures d'appareils ne sont pas interchangeables.
- Les fichiers cliniques bruts ne sont pas publiés dans GitHub sans autorisation explicite.
- Une CI réussie prouve certains contrôles logiciels, pas la validité biomédicale ou clinique.
- Les modifications sont faites sur des branches dédiées et proposées en PR ; aucune fusion automatique.

## Tableau de suivi — source de vérité

Les statuts décrivent les preuves actuellement connues, pas une estimation optimiste du pourcentage d'avancement. Mettre à jour ce tableau seulement après vérification des commits, des fichiers, des tests et des rapports.

| Phase | État initial au 2026-10-13 | Prochaines actions | Critère de sortie |
|---|---|---|---|
| 0. Audit du dépôt | En grande partie réalisé ; registre à maintenir | Cartographier architecture, branches, PR, dépendances, tests, CI, modules expérimentaux et résultats historiques | Chaque risque prioritaire a une preuve, une action et un test |
| 1. Audit des données et provenance | En cours ; audits de sources documentés, audit des fichiers locaux incomplet | Vérifier licences, formats, intégrité, doublons, IDs patient, cibles, unités, références, flash/no-flash et métadonnées | Chaque observation quantitative satisfait un contrat et possède une provenance vérifiable |
| 2. Architecture et contrats stricts | Corrections de provenance engagées sur branche/PR | Vérifier schéma canonique, validateurs, interfaces, erreurs explicites, configurations et journaux structurés | Les entrées invalides/ambiguës sont rejetées ou signalées sans coercition silencieuse |
| 3. Pipeline reproductible d'imagerie | À auditer module par module | Tester décodage, dimensions, canaux, sRGB encodé/linéarisé, transformations et traçabilité source→features | Toute feature remonte à l'image source et aux transformations enregistrées |
| 4. Fondements biophysiques | Documentation et implémentation à vérifier | Documenter absorption/diffusion, réponse capteur, balance des blancs, densité optique relative, saturation et identifiabilité | Hypothèses et variables sont justifiées ou explicitement exploratoires |
| 5. Qualité des acquisitions | Infrastructure existante à examiner | Tester flou, exposition, saturation, bruit, reflets, seuils et états accept/retake/reject | Faux rejets et mauvaises acquisitions acceptées sont mesurés sur des données distinctes |
| 6. Calibration et adaptation | Capacités existantes à inventorier | Préspécifier baseline affine, stratégies fixes/adaptatives et correction flash uniquement sous hypothèses compatibles | Comparaison sur des données non utilisées pour choisir les méthodes |
| 7. Modélisation statistique et IA | À auditer ; pas de revendication de performance | Définir baseline, comparer modèles, figer seeds/hyperparamètres et calibrer l'incertitude ; Hb et bilirubine séparés | Gain reproductible face au baseline sans fuite de données, sinon résultat négatif/inconclusif documenté |
| 8. Validation expérimentale | Dépend des données admissibles et du protocole | Splits patient-disjoints, test gelé, appareils tenus à l'écart si possible, analyses de sous-groupes et IC | Chaque métrique renvoie à un protocole, un split et un artefact de résultat identifiable |
| 9. Incertitude et abstention | Diagnostics d'incertitude présents à auditer | Vérifier couverture, largeur des intervalles, risque parmi cas acceptés, couverture-erreur et politique de refus | Le mécanisme d'abstention est mesuré et ne masque pas les échecs |
| 10. Intégration et dashboard | À auditer | Relier l'interface aux sorties réellement calculées ; distinguer réel/synthétique/démonstration ; supprimer tout résultat codé en dur | Le dashboard reflète les résultats traçables sans ajouter de conclusions |
| 11. Assurance qualité et reproductibilité | CI existante ; dernière validation de chaque tête de branche à revérifier | Tests unitaires/intégration/régression, dépendances, confidentialité, manifeste, empreintes, versions et reprise d'expérience | Contrôles exécutés sur le commit concerné ; limites restantes documentées |
| 12. Rapport scientifique final | Après résultats reproductibles | Décrire hypothèses, données, méthodes, résultats positifs/négatifs/inconclusifs, biais et limites | Toute conclusion renvoie à des données et analyses identifiables ; aucune revendication clinique non justifiée |

## Phase 0 — Audit du dépôt

### Actions
1. Enregistrer commit de référence, branches actives, PR ouvertes/fermées et workflows.
2. Cartographier modules, dépendances, points d'entrée, tests et artefacts générés.
3. Classer chaque module : implémenté/testé, implémenté/non testé, expérimental, incomplet ou obsolète.
4. Tenir un registre des risques avec sévérité, preuve, correction, test, responsable et statut.

### Livrables
- Rapport d'audit versionné.
- Carte d'architecture réelle.
- Registre des risques et roadmap.

### Porte de sortie
Tous les risques prioritaires ont une preuve issue du dépôt et une action vérifiable.

## Phase 1 — Audit scientifique des données

### Audit par dataset
- Source officielle, version, licence et restrictions d'accès/redistribution.
- Inventaire des fichiers, format, dimensions, fichiers illisibles et chemins cassés.
- Hashes, doublons exacts et recherche de doublons visuels si les outils le permettent.
- Identifiants patients, images/vidéos, référence associée, unité, timing et type de référence.
- Valeurs manquantes/aberrantes et distributions, sans suppression arbitraire.
- Appareil, illumination, flash, exposition, ISO, balance des blancs et autres métadonnées.
- Rapport d'exclusions avec motif explicite et nombre d'observations concernées.

### Classes d'usage
- **Quantitatif admissible :** référence et unité caractérisées, identité et lien image-référence fiables, licence/accès compatibles, métadonnées suffisantes pour le protocole.
- **Développement seulement :** utile pour ingestion/vision, mais cible ou référence non assez fiable pour évaluer l'estimation biologique.
- **Bloqué pour l'analyse concernée :** identité, unité, référence, licence ou séparation des patients non vérifiées.

### Porte de sortie
Pas de dataset déclaré « prêt » sur la seule base de sa page web ou de la présence de fichiers dans le dépôt.

## Phases 2–5 — Contrats, imagerie, biophysique et qualité

- Conserver les sources immuables et tracer chaque transformation.
- Centraliser types, unités, valeurs autorisées et provenance.
- Garder inconnues les métadonnées absentes ou ambiguës.
- Distinguer RGB sRGB encodé de RGB linéarisé.
- Documenter les ROI autorisées par biomarqueur et la provenance de leur localisation ; aucune localisation automatique non validée.
- Séparer ingestion canonique et admissibilité quantitative : une modalité exploratoire peut être conservée, mais refusée par le runner quantitatif.
- Caractériser le quality gate avec cas limites et données distinctes pour l'ajustement des seuils.

## Phases 6–9 — Protocole expérimental central

Les expériences sont préspécifiées et exécutées séparément pour Hb et bilirubine, seulement si le dataset satisfait les prérequis.

| ID | Comparaison | Question |
|---|---|---|
| E1 | Baseline statistique vs calibration affine | La calibration améliore-t-elle l'estimation ? |
| E2 | Calibration fixe vs adaptative | L'adaptation apporte-t-elle un bénéfice supplémentaire ? |
| E3 | Sans vs avec quality gate | La qualité contrôlée réduit-elle les erreurs, et à quel coût de couverture ? |
| E4 | Sans correction vs correction admissible | La correction d'éclairage aide-t-elle lorsque ses hypothèses sont satisfaites ? |
| E5 | Prédiction seule vs incertitude/abstention | L'incertitude identifie-t-elle les cas moins fiables ? |
| E6 | Appareils vus vs appareil tenu à l'écart | La méthode généralise-t-elle à un appareil inédit ? |

### Métriques candidates
- Régression : MAE, RMSE, biais et intervalles de confiance.
- Accord : Bland–Altman si les hypothèses et le plan d'échantillonnage le permettent.
- Incertitude : couverture empirique, largeur des intervalles, calibration.
- Qualité : taux de rejet, faux rejets et taux d'images inadéquates acceptées.
- Robustesse : écarts d'erreur par appareil/conditions/sous-groupes admissibles.
- Généralisation : test patient-disjoint et, si faisable, appareil-disjoint.

La corrélation seule n'établit pas l'accord. Le test final ne sert ni à sélectionner les hyperparamètres ni à choisir le meilleur modèle.

## Phases 10–12 — Intégration, reproductibilité et publication

- Dashboard connecté uniquement aux résultats calculés et traçables.
- Manifestes d'expérience : commit, configuration, versions, seeds, source/version de dataset, hashes, partitions et date d'exécution.
- CI sur les versions Python déclarées ; rapporter les résultats du commit exact.
- Ne pas inclure les données brutes protégées dans le dépôt.
- Rapport final distinguant résultats positifs, négatifs et inconclusifs.
- Déclarer explicitement les limites de représentativité et l'absence de validation clinique.

## Cycle de travail GitHub pour chaque lot

1. Auditer le code réel et citer le problème précis.
2. Définir le changement minimal et les critères d'acceptation.
3. Créer une branche dédiée ; ne pas travailler directement sur `main`.
4. Modifier le code et ajouter les tests associés.
5. Exécuter les tests et workflows disponibles.
6. Examiner les diffs et la sortie des tests.
7. Ouvrir/mettre à jour une PR avec preuves, limites et statut CI.
8. Fusionner seulement après revue et autorisation explicite.

## Prochaine action immédiate

1. Vérifier le statut CI du commit HEAD actuel de la PR de provenance ; ne pas réutiliser le résultat d'un ancien commit comme preuve du nouveau.
2. Vérifier les validateurs de référence, les valeurs autorisées de `reference_type` et le contrat ROI avant de finaliser les corrections d'adaptateurs.
3. Examiner les datasets localement uniquement si l'accès est autorisé ; commencer par inventaire, intégrité, identifiants, cibles et provenance, sans entraîner de modèle.
4. Mettre à jour ce registre avec liens vers commits, rapports et runs CI réellement vérifiés.
5. Passer à la phase suivante uniquement quand le critère de sortie correspondant est documenté.

## Journal des décisions et preuves

| Date | Décision / preuve | Référence |
|---|---|---|
| 2026-10-13 | Source audit SEWA : compatibilité avec le schéma publié en cours ; l'audit des fichiers locaux reste nécessaire | `docs/audits/2026-10-13-dataset-source-audit.md` |
| 2026-10-13 | Corrections de provenance et tests en revue sur une branche/PR ; vérifier la CI de la tête courante avant de déclarer validé | PR de provenance (voir liens du dépôt) |

**Mise à jour du statut :** conserver les statuts prudents. Ne marquer une phase comme terminée qu'avec une preuve vérifiable liée à un commit, un test, un rapport ou une décision documentée.
