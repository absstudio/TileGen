# TileGen

**TileGen** (Tile + Generator) est un outil qui génère des noms de produits pour un catalogue de carreaux céramiques. Il crée des noms uniques et prononçables inspirés de lieux du monde (PETRA, SAHARA, MEDINA...) et d'éléments vintage (MARBLE, EMPIRE...), et leur associe automatiquement une courte description marketing.

Il est idéal pour trouver rapidement de nouveaux noms de collections sans retomber sur des noms déjà utilisés : chaque nom généré est mémorisé et ne sera jamais proposé deux fois.

---

## ⚡ Quick Start

**Prérequis** — c'est tout :
- [Python 3.8+](https://www.python.org/downloads/) (aucune dépendance externe : TileGen n'utilise que la bibliothèque standard)

> [!TIP]
> Sous Windows, cochez **« Add Python to PATH »** pendant l'installation de Python.

### Option A — Lancement en 1 commande (recommandé)

**Windows (PowerShell)** :
```powershell
.\quickstart.ps1
```

**Linux / macOS** :
```bash
./quickstart.sh
```

Le script vérifie Python, teste le démarrage et installe la commande globale `tilegen` (optionnel, non bloquant).

### Option B — Installation manuelle

```bash
# 1. Récupérer le projet
git clone https://github.com/absstudio/TileGen.git
cd TileGen

# 2. Lancer — c'est déjà installé, il n'y a rien d'autre à faire
python tilegen.py
```

*(Optionnel : enregistrez la commande globale avec `python -m pip install -e .` — ensuite `tilegen` fonctionne depuis n'importe quel terminal.)*

### Vérification rapide ("It works!")

Au lancement, cette console s'affiche — le programme tourne :

```
    ██████    ██    ██      ██████  ██████  ██████  ██  ██
      ██            ██      ██      ██      ██      ██████
      ██      ██    ██      ██████  ██  ██  ██████  ██  ██
      ██      ██    ██      ██      ██  ██  ██      ██  ██
      ████    ██    ██████  ██████  ██████  ██████  ██  ██

              /help pour les commandes  ·  v3.2

  ▌   Générez des noms... « 10 », /model, /help — Tab pour compléter
  ▌   Local · mode sans clé · /model pour l'IA

  ❯ 
```

Test direct sans console interactive :
```bash
python tilegen.py --count 2
```
Sortie attendue : deux noms uniques avec leurs descriptions (ex. `KYONO — Évoque Kyoto...`). C'est tout : aucune clé API, aucun fichier de configuration n'est requis pour démarrer.

---

## Exemple de sortie

```
CATALOGUE DE CARREAUX CÉRAMIQUES
================================================================================
NOM        | DESCRIPTION
--------------------------------------------------------------------------------
PETBOR     | Collection de style épuré. Inspiré des textures naturelles, offrant une touche de raffinement.
--------------------------------------------------------------------------------
SIVI       | Gamme aux tons minéraux. Né de l'harmonie des éléments, créant un espace harmonieux.
--------------------------------------------------------------------------------
```

---

## Utiliser TileGen sans rien installer (le plus simple)

Aucune installation nécessaire : ouvrez simplement la version web du générateur dans votre navigateur.

**Lien : https://absstudio.github.io/TileGen/**

1. Choisissez le nombre de noms à générer
2. Cliquez sur **Générer**
3. Les noms s'affichent avec leurs descriptions

Le bouton 🌙 / ☀️ en haut à droite permet de basculer entre le thème sombre et le thème clair. Les noms déjà générés sont mémorisés par votre navigateur et le bouton « Réinitialiser l'historique » permet de repartir de zéro.

---

## Installer TileGen sur votre PC (version complète)

### Étape 1 — Installer Python (une seule fois)

TileGen fonctionne avec **Python 3.8 ou plus récent**.

1. Allez sur https://www.python.org/downloads/
2. Cliquez sur le bouton jaune **Download Python 3.x.x**
3. Lancez le fichier téléchargé
4. **Important** : sur le premier écran de l'installeur, cochez la case **"Add Python to PATH"** avant de cliquer sur *Install Now*

### Étape 2 — Télécharger TileGen

Deux possibilités :

**Option A — Téléchargement simple (recommandé si vous ne connaissez pas Git)**
1. Ouvrez https://github.com/absstudio/TileGen
2. Cliquez sur le bouton vert **<> Code** puis **Download ZIP**
3. Décompressez le fichier ZIP où vous voulez (par exemple dans `Documents\TileGen`)

**Option B — Avec Git** (si Git est installé)
```bash
git clone https://github.com/absstudio/TileGen.git
cd TileGen
```

### Étape 3 — Lancer TileGen

Ouvrez un terminal **dans le dossier de TileGen** :
- Sous Windows : ouvrez le dossier décompressé, cliquez dans la barre d'adresse en haut, tapez `cmd` puis Entrée.

Puis lancez la commande :

```bash
python tilegen.py
```

#### Option : la commande `tilegen` partout dans le terminal

Si Python est déjà installé, vous pouvez enregistrer TileGen comme commande globale — ensuite, **plus besoin d'aller dans le dossier** : tapez simplement `tilegen` depuis n'importe quel terminal :

```bash
cd Chemin/vers/TileGen-main
python -m pip install -e .
```

Puis, où que vous soyez :

```bash
tilegen              # ouvre la console TileGen
tilegen --count 10   # génération directe de 10 noms
tilegen --help       # aide
```

La commande reste à jour automatiquement : elle lit les fichiers du dossier où TileGen est installé.

Une **console interactive** s'affiche (inspirée du terminal d'OpenCode) : logo TILEGEN en orange, barre de statut IA et invite de commande. Vous tapez des commandes comme dans un terminal moderne :

```
╭──────────────────────────────────────────────────────────╮
│ ia : non configurée  (/model pour démarrer)              │
╰──────────────────────────────────────────────────────────╯
  ❯ 
```

- **Un nombre** (ex. `10`) — génère 10 noms en local, aucune clé nécessaire ;
- `/model` — choisir le fournisseur d'IA et son modèle (OpenAI, Google AI Studio/Gemini, DeepSeek, Groq, Mistral) ;
- `/key` — saisir ou changer la clé API ;
- `/test` — vérifier que la connexion IA fonctionne ;
- `/gen 20` — générer 20 noms en local ;
- `/ai 10` — générer 10 noms avec l'IA ;
- `/export` — exporter les derniers résultats en CSV ;
- `/reset` — effacer l'historique ;
- `/clear` — nettoyer l'écran ;
- `/help` — liste des commandes ;
- `/exit` — quitter.

Après chaque génération : `Entrée` pour revenir à l'invite, `e` pour exporter en CSV, `q` pour retourner au menu principal.

> **Aucune installation supplémentaire n'est nécessaire** : TileGen n'utilise que des outils inclus dans Python. Pas de `pip install` à faire.

---

## Comment utiliser TileGen

### Générer un nombre précis de noms

```bash
python tilegen.py --count 10
```
Remplacez `10` par le nombre souhaité (par défaut : 20).

### Exporter les noms dans un fichier Excel (CSV)

```bash
python tilegen.py --count 15 --export catalogue.csv
```
Un fichier `catalogue.csv` est créé dans le dossier : ouvrez-le avec Excel ou LibreOffice. Il contient deux colonnes : *Nom* et *Description*.

### Effacer l'historique des noms générés

```bash
python tilegen.py --reset
```
TileGen mémorise chaque nom généré dans un fichier `noms_generes.json` pour ne jamais proposer deux fois le même nom. Si vous voulez repartir de zéro (par exemple pour un nouveau catalogue), utilisez cette commande.

### Afficher l'aide

```bash
python tilegen.py --help
```

### Utiliser le mode IA (facultatif)

TileGen peut aussi générer des noms avec une intelligence artificielle. Cela nécessite une clé API d'un service compatible OpenAI (OpenAI, DeepSeek, Groq, Mistral...). **Sans clé API, le mode local fonctionne parfaitement** — l'IA est une option.

**1. Configurez une seule fois** — lancez `python tilegen.py` puis tapez `/model` :
- **Étape 1/2** : choisissez votre **fournisseur** (la base URL est remplie automatiquement) ;
- **Étape 2/2** : choisissez le **modèle**, collez votre clé API quand elle est demandée.

| # | Fournisseur | Modèles proposés |
|---|---|---|
| 1 | OpenAI | gpt-4o-mini, gpt-4o... |
| 2 | **Google AI Studio (Gemini)** | gemini-flash-lite-latest, gemini-flash-latest, gemini-3.8-flash |
| 3 | DeepSeek | deepseek-chat |
| 4 | Groq | llama-3.3-70b-versatile |
| 5 | Mistral | mistral-small-latest |
| 6 | Autre / personnalisé | libre |

> Pour **Google AI Studio** : clé gratuite sur [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (bouton *Get API key* → *Create API key*). Collez-la quand le programme la demande (saisie masquée).

**2. Testez que ça marche :**
- tapez `/test` dans la console — le résultat affiche `Connexion réussie · modèle · temps · réponse : « OK »` ou la **cause précise** de l'échec (clé invalide, URL erronée, quota dépassé...) ;
- ou en ligne de commande : `python tilegen.py --test-ai`.

Le test envoie une requête minimale au service et affiche le résultat : `Connexion réussie · gemini-flash-lite-latest · 1.2s · réponse : « OK »` ou la cause précise de l'échec (clé invalide, URL erronée...).

**3. Générez avec l'IA :**
```bash
python tilegen.py --ai --count 10
```

> La clé API reste sur votre machine (`tilegen_config.json`, exclu de Git). Vous pouvez aussi passer par la variable d'environnement `TILEGEN_API_KEY`.

### Utiliser TileGen dans vos propres scripts Python

```python
from tilegen import suggest_names

# 5 suggestions de noms avec descriptions
suggestions = suggest_names(5)
for nom, description in suggestions:
    print(nom, "->", description)
```

---

## Dépannage

| Problème | Solution |
|---|---|
| `'python' n'est pas reconnu...` | Python n'est pas installé ou n'a pas été ajouté au PATH. Réinstallez Python en cochant **"Add Python to PATH"** |
| Sous Windows, `py` fonctionne mais pas `python` | Utilisez `py tilegen.py` à la place |
| Le fichier `catalogue.csv` s'ouvre mal | Ouvrez Excel → Données → À partir d'un fichier CSV, ou utilisez LibreOffice |
| Message "Aucun nom valide trouvé" | L'historique est plein. Lancez `python tilegen.py --reset` |
| Je veux retrouver un nom déjà généré | Ouvrez le fichier `noms_generes.json` : tous les noms générés y sont listés |

---

## Comment ça marche

TileGen combine deux méthodes de génération :
1. **Suffixe noble** : un lieu du monde tronqué à la voyelle + une terminaison italienne (PETRA → PETRINA, SAHARA → SAHANA, MILAN → MILAANA) ;
2. **Fusion** : le début de deux mots assemblé (ARCADE + MILAN → ARCAMILA, TOKYO + ARENA → TOARE).

Chaque nom est ensuite contrôlé :
- il ne doit pas déjà exister dans le catalogue ni dans l'historique ;
- il ne doit pas être un mot courant du dictionnaire (ARCH, RETRO, PLAZA... sont écartés) ;
- il doit être prononçable et se terminer par une voyelle (sonorité élégante).

La description de chaque nom affiche **son étymologie** : vous savez toujours de quoi il s'inspire (« Évoque Porto. Gamme aux tons minéraux... »).

---

## Structure du projet

```
TileGen/
├── tilegen.py               # Le générateur (programme principal)
├── exemple_utilisation.py   # Exemple d'utilisation du module
├── index.html               # Version web (site en ligne)
├── requirements.txt         # Aucune dépendance externe
└── README.md                # Ce guide
```

Fichiers créés automatiquement sur votre machine (non publiés) :
- `noms_generes.json` : historique des noms déjà générés ;
- `tilegen_config.json` : votre configuration IA (clé API), uniquement si vous utilisez `--configure-ai`.

**Aucune dépendance externe** — Python 3.8+ suffit.

---

TileGen — créé par [absstudio](https://github.com/absstudio)
