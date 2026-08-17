# 🕊️ Application de suivi des obsèques

## MAKOSSO POATHY Jean Pierre

Application familiale de suivi budgétaire, financier et opérationnel des obsèques de Feu MAKOSSO POATHY Jean Pierre.

---

## 📅 Informations du dossier

* **Défunt :** MAKOSSO POATHY Jean Pierre
* **Date des obsèques :** 27 août 2026
* **Lieu prévu :** Mayumba
* **Budget prévisionnel :** 3 788 905 FCFA
* **Budget détaillé :** 3 488 905 FCFA
* **Budget non affecté :** 300 000 FCFA

---

## 🏗️ Architecture

L'application repose sur trois composants principaux :

### Backend

**Flask + SQLite**

Le backend fournit une API REST permettant :

* la consultation du budget ;
* la consultation des dépenses ;
* la mise à jour des dépenses réelles ;
* la gestion des cotisants ;
* la gestion des versements ;
* la gestion des tâches ;
* l'authentification administrateur.

Fichier principal :

```text
app/backend/flask_app.py
```

API locale :

```text
http://127.0.0.1:5000
```

### Frontend

**Streamlit**

L'interface utilisateur est organisée comme suit :

```text
app/frontend/
│
├── 0_Accueil.py
├── components.py
│
└── pages/
    ├── 1_Depenses.py
    ├── 2_Cotisations.py
    ├── 3_Suivi.py
    ├── 4_Tableau_de_bord.py
    └── 5_Reporting.py
```

Interface :

```text
http://localhost:8501
```

### Base de données

La base principale est :

```text
data/obseques.db
```

La base contient actuellement :

* **10 catégories**
* **86 dépenses**
* **13 cotisants**
* **13 versements**
* **0 tâche**

L'intégrité de la base SQLite a été vérifiée avec :

```sql
PRAGMA integrity_check;
```

Résultat :

```text
ok
```

---

## 💰 Gestion financière

L'application distingue trois notions principales.

### Budget prévisionnel

Montant global prévu pour les obsèques :

```text
3 788 905 FCFA
```

### Budget détaillé

Montant actuellement ventilé dans les dépenses détaillées :

```text
3 488 905 FCFA
```

### Budget non affecté

Montant restant à affecter à un poste précis :

```text
300 000 FCFA
```

### Dépenses réelles

Les dépenses réelles sont saisies progressivement par l'administrateur.

Situation actuelle :

```text
Dépenses prévisionnelles : 3 488 905 FCFA
Dépenses réelles         : 0 FCFA
```

---

## 📂 Postes budgétaires

Les dépenses sont organisées par catégories budgétaires.

La page :

```text
app/frontend/pages/1_Depenses.py
```

permet notamment de :

* sélectionner un poste budgétaire ;
* consulter le budget prévisionnel ;
* consulter le budget détaillé ;
* consulter le budget non affecté ;
* consulter les dépenses du poste ;
* saisir les dépenses réelles ;
* calculer automatiquement le prix unitaire réel ;
* calculer l'écart ;
* calculer la progression ;
* déterminer le statut ;
* supprimer une dépense en administration.

### Statuts des dépenses

* `A FAIRE`
* `EN COURS`
* `TERMINE`

---

## 👥 Gestion des cotisations

La page :

```text
app/frontend/pages/2_Cotisations.py
```

permet de gérer les contributions.

Deux listes sont actuellement utilisées :

* `Famille Bayema`
* `Enfants`

Chaque cotisant possède :

* un nom ;
* une liste ;
* un téléphone ;
* un montant prévu ;
* un montant versé ;
* un reste ;
* un statut.

### Situation actuelle

```text
Cotisations prévues : 1 300 000 FCFA
Cotisations versées :   730 000 FCFA
Reste à collecter   :   670 000 FCFA
```

### Statuts des cotisations

* `NON SOLDE`
* `PARTIEL`
* `SOLDE`
* `SUPER`

### Fonctions administratives

L'administrateur peut :

* ajouter un cotisant ;
* modifier un cotisant ;
* supprimer un cotisant ;
* enregistrer un versement ;
* consulter l'historique des versements ;
* supprimer un versement.

---

## ✅ Suivi des préparatifs

La page :

```text
app/frontend/pages/3_Suivi.py
```

permet de gérer les tâches opérationnelles.

Chaque tâche peut contenir :

* un nom ;
* une description ;
* une catégorie ;
* une progression ;
* une date prévue ;
* une date de réalisation ;
* un statut.

### Statuts

* `A FAIRE`
* `EN COURS`
* `TERMINE`

### Fonctions administratives

L'administrateur peut :

* créer une tâche ;
* modifier une tâche ;
* modifier sa progression ;
* supprimer une tâche.

Situation actuelle :

```text
Nombre de tâches : 0
```

---

## 📊 Tableau de bord

La page :

```text
app/frontend/pages/4_Tableau_de_bord.py
```

présente une vue consolidée de l'application.

Elle permet de suivre notamment :

* le budget prévisionnel ;
* le budget détaillé ;
* le budget non affecté ;
* les dépenses réelles ;
* l'écart budgétaire ;
* la progression financière ;
* les cotisations ;
* le taux de collecte ;
* les tâches ;
* l'avancement opérationnel ;
* les alertes.

---

## 📑 Reporting

La page :

```text
app/frontend/pages/5_Reporting.py
```

présente une synthèse globale du dossier.

Elle comprend :

* la synthèse financière ;
* l'analyse par catégorie ;
* la situation des cotisations ;
* le suivi des préparatifs ;
* les alertes ;
* l'état des cotisants ;
* les exports CSV.

### Exports disponibles

```text
suivi_financier_obseques.csv
cotisations_obseques.csv
suivi_taches_obseques.csv
```

---

## 🔐 Authentification administrateur

Les opérations sensibles sont protégées par une authentification administrateur.

Les opérations protégées comprennent :

* ajout d'un cotisant ;
* modification d'un cotisant ;
* suppression d'un cotisant ;
* enregistrement d'un versement ;
* suppression d'un versement ;
* modification d'une dépense ;
* suppression d'une dépense ;
* création d'une tâche ;
* modification d'une tâche ;
* suppression d'une tâche.

Le mot de passe administrateur est fourni par la variable d'environnement :

```text
OBSEQUES_ADMIN_PASSWORD
```

Le mot de passe ne doit pas être écrit directement dans le code source.

---

## 💾 Sauvegarde

La base active est :

```text
data/obseques.db
```

Les sauvegardes sont stockées dans :

```text
backups/
```

Le script de sauvegarde est :

```text
backup_database.ps1
```

Une tâche du Planificateur de tâches Windows est configurée :

```text
Obseques_MAKOSSO_Sauvegarde
```

Cette tâche réalise automatiquement une sauvegarde quotidienne.

Le système conserve les **30 sauvegardes les plus récentes**.

### Sauvegarde manuelle

```powershell
powershell -ExecutionPolicy Bypass -File ".\backup_database.ps1"
```

---

## 🚀 Lancement rapide

Le lancement recommandé sous Windows est :

```text
run.bat
```

Il suffit de double-cliquer sur :

```text
run.bat
```

Le script lance automatiquement :

```text
Flask
+
Streamlit
```

Puis le navigateur s'ouvre automatiquement sur :

```text
http://localhost:8501
```

### Lancement manuel

Démarrer Flask :

```powershell
python ".\app\backend\flask_app.py"
```

Démarrer Streamlit :

```powershell
python -m streamlit run ".\app\frontend\0_Accueil.py"
```

---

## 🧪 Vérification de l'API

### Vérifier Flask

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/api/health"
```

Résultat attendu :

```text
database  status
--------  ------
connected ok
```

### Vérifier le tableau de bord

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/api/dashboard"
```

### Vérifier les tâches

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/api/taches"
```

---

## 📦 Dépendances Python

Les dépendances sont définies dans :

```text
requirements.txt
```

Installation :

```powershell
python -m pip install -r ".\requirements.txt"
```

### Dépendances principales

```text
Flask
Streamlit
Pandas
NumPy
Requests
OpenPyXL
```

---

## 📁 Structure finale du projet

```text
obseques_makosso/
│
├── app/
│   ├── backend/
│   │   ├── calculations.py
│   │   ├── data_processing.py
│   │   └── flask_app.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   ├── import_data.py
│   │   └── models.py
│   │
│   └── frontend/
│       ├── 0_Accueil.py
│       ├── components.py
│       │
│       └── pages/
│           ├── 1_Depenses.py
│           ├── 2_Cotisations.py
│           ├── 3_Suivi.py
│           ├── 4_Tableau_de_bord.py
│           └── 5_Reporting.py
│
├── backups/
│
├── data/
│   ├── categories_budget.csv
│   ├── depenses.xlsx
│   ├── depenses_propres.csv
│   └── obseques.db
│
├── backup_database.ps1
├── requirements.txt
├── run.py
├── run.bat
└── README.md
```

---

## ⚠️ Recommandations

La base :

```text
data/obseques.db
```

est la base principale de l'application.

Avant toute modification importante, effectuer une sauvegarde :

```powershell
powershell -ExecutionPolicy Bypass -File ".\backup_database.ps1"
```

Ne pas supprimer ou remplacer :

```text
data/obseques.db
```

sans disposer d'une sauvegarde récente.

Ne pas exécuter de scripts de nettoyage ou de suppression SQL inconnus sur la base principale.

---

## ✅ État actuel du projet

Les contrôles réalisés ont confirmé :

* API Flask opérationnelle ;
* SQLite opérationnelle ;
* intégrité SQLite : `ok` ;
* 10 catégories ;
* 86 dépenses ;
* 13 cotisants ;
* 13 versements ;
* 0 tâche ;
* authentification administrateur opérationnelle ;
* gestion des dépenses opérationnelle ;
* gestion des cotisations opérationnelle ;
* gestion des tâches opérationnelle ;
* tableau de bord opérationnel ;
* reporting opérationnel ;
* sauvegarde automatique opérationnelle ;
* lancement avec `run.bat` opérationnel ;
* ouverture automatique du navigateur opérationnelle.

---

## 🕊️ Projet

**Application de suivi des obsèques**

**Feu MAKOSSO POATHY Jean Pierre**

**27 août 2026 — Mayumba**

Application développée pour assurer le suivi familial du budget, des dépenses, des cotisations et des préparatifs des obsèques.
