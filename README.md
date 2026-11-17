# TileGen — Générateur de noms de carreaux céramiques

Outil Python qui génère des noms de produits pour un catalogue de carreaux céramiques, inspirés de lieux touristiques et d'éléments vintage, avec descriptions marketing automatiques. Chaque nom est unique, prononçable et mémorisé pour éviter les doublons entre les sessions.

---

## Utilisation

```bash
# Générer 20 suggestions (défaut)
python tilegen.py

# Générer un nombre précis
python tilegen.py --count 10

# Exporter en CSV (ouvrable dans Excel)
python tilegen.py --count 15 --export catalogue.csv

# Effacer l'historique des noms générés
python tilegen.py --reset
```

Aucune dépendance externe — Python 3.8+ suffit.

## Améliorations V2

| Amélioration | Description |
|---|---|
| Persistance JSON | Les noms générés sont sauvegardés dans `noms_generes.json` : jamais deux fois le même nom, même après relance |
| Anti boucle infinie | Maximum 1000 tentatives avec message d'erreur clair |
| Filtrage des mots réels | Les mots du dictionnaire (ARCH, RETRO, PLAZA...) ne sont plus proposés |
| Gestion des accents | FAÇADE, É, À... correctement évalués |
| CLI complète | `--count`, `--export`, `--reset` |
| Page web | `index.html` : version interactive consultable en ligne via GitHub Pages |
| Thèmes clair / sombre | La page web propose un thème clair (`#F2F2F2`) et un thème sombre (`#0F0E0E`), avec bouton de bascule et détection automatique de la préférence système |

---

# Guide complet : mettre à jour le projet sur GitHub

## Étape 0 — Prérequis (une seule fois)

1. **Créer un compte GitHub** sur [github.com](https://github.com) si ce n'est pas déjà fait.
2. **Installer Git** : télécharger sur [git-scm.com](https://git-scm.com/downloads), installer avec les options par défaut.
3. **Configurer son identité** (une seule fois) — ouvrir un terminal (cmd ou PowerShell) :

```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre-email@exemple.com"
```

> Utilisez l'email associé à votre compte GitHub.

## Étape 1 — Créer le dépôt sur GitHub (première fois seulement)

1. Aller sur [github.com/new](https://github.com/new)
2. **Repository name** : `generator-tiziri` (par exemple)
3. Choisir **Public** (nécessaire pour GitHub Pages gratuit)
4. **Ne pas** cocher "Add a README" (nous en avons déjà un)
5. Cliquer **Create repository**
6. GitHub affiche une page avec l'URL du dépôt, par exemple :
   `https://github.com/VOTRE-PSEUDO/generator-tiziri.git` — notez-la.

## Étape 2 — Envoyer le projet pour la première fois

Dans un terminal, positionnez-vous dans le dossier du projet :

```bash
cd "C:\Users\hp\Desktop\Ai\01.DEV APK\Github Project\generator_tiziri_V2-main"
```

Puis exécutez ces 4 commandes dans l'ordre :

```bash
# 1. Initialiser Git dans le dossier
git init

# 2. Préparer tous les fichiers
git add .

# 3. Créer le premier enregistrement (commit)
git commit -m "Première version V2 du générateur"

# 4. Lier le dossier local au dépôt GitHub et envoyer
git remote add origin https://github.com/VOTRE-PSEUDO/generator-tiziri.git
git branch -M main
git push -u origin main
```

> À la première commande `push`, une fenêtre de connexion GitHub s'ouvre : connectez-vous. Si GitHub demande un mot de passe, il faut en réalité un **Personal Access Token** : aller sur GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic), cocher `repo`, copier le token et l'utiliser comme mot de passe.

Le code est maintenant visible sur `https://github.com/VOTRE-PSEUDO/generator-tiziri`.

## Étape 3 — Mettre à jour le projet (à chaque modification)

Après avoir modifié un ou plusieurs fichiers, 3 commandes suffisent :

```bash
git add .
git commit -m "Description de la modification (ex: ajout de nouveaux lieux d'inspiration)"
git push
```

**Bonne pratique** : avant de commencer à travailler, récupérez les dernières versions avec `git pull`.

## Résumé des commandes

| Commande | Rôle |
|---|---|
| `git status` | Voir les fichiers modifiés |
| `git add .` | Préparer toutes les modifications |
| `git commit -m "..."` | Enregistrer les modifications avec un message |
| `git push` | Envoyer vers GitHub |
| `git pull` | Récupérer les dernières modifications depuis GitHub |

---

# Guide : rendre le projet consultable en ligne (GitHub Pages)

GitHub Pages publie gratuitement un site statique depuis votre dépôt. Le fichier `index.html` inclus dans ce projet devient alors une **page web interactive** où n'importe qui peut générer des noms depuis son navigateur, sans installer Python.

## Activation (une seule fois, après la première push)

1. Ouvrir votre dépôt sur GitHub : `https://github.com/VOTRE-PSEUDO/generator-tiziri`
2. Cliquer sur **Settings** (onglet en haut du dépôt)
3. Dans le menu de gauche, cliquer sur **Pages**
4. Dans la section **Build and deployment** :
   - **Source** : `Deploy from a branch`
   - **Branch** : sélectionner `main` et le dossier `/ (root)`
   - Cliquer **Save**
5. Attendre 1 à 2 minutes. Un bandeau vert apparaît :
   *"Your site is live at ..."*

## Votre lien consultable

Le site est accessible à l'adresse :

```
https://VOTRE-PSEUDO.github.io/generator-tiziri/
```

Ce lien est permanent, gratuit, et peut être partagé avec n'importe qui (collègues, clients).

## Mettre à jour le site en ligne

Dès que vous faites `git push` (Étape 3), GitHub Pages **met automatiquement à jour le site** en 1 à 2 minutes. Aucune manipulation supplémentaire n'est nécessaire.

## Astuce : lien direct dans le README

Le lien du site peut être ajouté en haut du README :

```markdown
[Ouvrir le générateur en ligne](https://VOTRE-PSEUDO.github.io/generator-tiziri/)
```

---

## Structure du projet

```
generator_tiziri_V2-main/
├── tilegen.py               # Cœur du générateur (Python) — TileGen
├── exemple_utilisation.py   # Exemple d'import du module
├── index.html               # Version web (GitHub Pages), thèmes clair/sombre
├── requirements.txt         # Aucune dépendance externe
├── .gitignore               # Fichiers exclus de Git
└── README.md                # Ce guide
```
