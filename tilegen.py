# -*- coding: utf-8 -*-
"""
TileGen — Générateur de noms pour catalogue de carreaux céramiques.

Améliorations par rapport à la V1 :
- Persistance des noms générés (fichier JSON) : unicité garantie entre les sessions
- Limite de tentatives dans generate_name (plus de boucle infinie possible)
- Filtrage des mots réels du dictionnaire (ARCH, RETRO, PLAZA... ne sont plus proposés)
- Gestion des accents (À, É, Ç...) dans la vérification de prononçabilité
- Interface en ligne de commande : --count, --export, --reset
"""

import argparse
import csv
import json
import random
import unicodedata
from pathlib import Path

# Fichier de persistance des noms générés
GENERATED_NAMES_FILE = Path(__file__).parent / "noms_generes.json"

# Nombre maximum de tentatives avant d'abandonner
MAX_ATTEMPTS = 1000

# Liste des noms existants (doublon "FLASH" corrigé)
EXISTING_NAMES = [
    "ARTIC", "ROYAL", "CASTLE", "ROCA", "FAÇADE", "TERRANGA", "AZAR",
    "ARDOISE", "SHERPA", "SAFRAN", "PLATINE", "FUJI", "TIGER",
    "TRAVARTINO", "ASTON", "DYNAMIC", "ELECTRA", "FLASH", "HOGGAR",
    "MIRAGE", "PLAYA", "SINA MARFIL", "STREET", "TECHNO", "VENUS",
    "VINTAGE", "VOYAGE", "ARAR", "BLACKOS", "BREAKING", "CAMEL",
    "COSTA", "DUNE", "ERUPTION"
]

# Inspiration de villes et lieux touristiques
PLACES_INSPIRATION = [
    # Villes historiques
    "PETRA", "ROMA", "CAIRO", "PARIS", "VENICE", "PORTO", "MILAN",
    "VIENNA", "PRAGUE", "SEOUL", "TOKYO", "KYOTO", "DELHI", "DUBAI",
    # Sites naturels
    "SAHARA", "ATLAS", "ANDES", "FUJI", "ALPES", "NILE", "CONGO",
    "AMAZON", "GOBI", "TUNDRA", "SIERRA", "OASIS",
    # Monuments
    "CASTLE", "PALACE", "TEMPLE", "TOWER", "OPERA", "PLAZA", "ARENA",
    # Quartiers célèbres
    "SOHO", "MARAIS", "BORGO", "MEDINA", "KASBAH"
]

# Éléments vintage et classiques
VINTAGE_ELEMENTS = [
    # Styles architecturaux
    "DECO", "RETRO", "LOFT", "MANOR", "VILLA", "ROYAL", "NOBLE",
    # Matériaux nobles
    "MARBLE", "ONYX", "BRASS", "COPPER", "SILVER", "PEARL", "IVORY",
    # Éléments de design
    "ARCADE", "COLUMN", "MOSAIC", "FRESCO", "VAULT", "ARCH",
    # Époques
    "EMPIRE", "REGENT", "LEGACY", "CROWN", "GLORY", "GRAND"
]

# Mots réels du dictionnaire à éviter dans les suggestions
# (un nouveau nom de produit ne doit pas être un mot courant existant)
REAL_WORDS_TO_AVOID = {
    "CASTLE", "PALACE", "TEMPLE", "TOWER", "OPERA", "PLAZA", "ARENA",
    "OASIS", "RETRO", "LOFT", "VILLA", "NOBLE", "MARBLE", "SILVER",
    "PEARL", "IVORY", "ARCADE", "COLUMN", "MOSAIC", "FRESCO",
    "VAULT", "ARCH", "EMPIRE", "LEGACY", "CROWN", "GLORY", "GRAND",
    "SOHO", "TUNDRA", "SIERRA", "AMAZON", "ROYAL", "VINTAGE",
    "DECO", "REGENT", "MANOR", "ONYX", "BRASS", "COPPER"
}


def strip_accents(text):
    """Retire les accents pour la vérification de prononçabilité (É -> E, Ç -> C)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class TileNameGenerator:
    def __init__(self, persistence_file=GENERATED_NAMES_FILE):
        self.persistence_file = Path(persistence_file)
        self.vowels = set('AEIOU')
        self.consonants = set('BCDFGHLMNPRSTVZ')
        self.places = PLACES_INSPIRATION
        self.vintage = VINTAGE_ELEMENTS
        # Fusionne les noms d'origine et les noms générés lors des sessions précédentes
        self.existing_names = set(EXISTING_NAMES) | self._load_generated_names()

    def _load_generated_names(self):
        """Charge les noms générés lors des sessions précédentes."""
        if self.persistence_file.exists():
            try:
                data = json.loads(self.persistence_file.read_text(encoding="utf-8"))
                return set(data.get("names", []))
            except (json.JSONDecodeError, OSError):
                # Fichier corrompu : on repart de la liste d'origine
                return set()
        return set()

    def _save_generated_names(self):
        """Sauvegarde les noms générés pour garantir l'unicité entre les sessions."""
        generated = self.existing_names - set(EXISTING_NAMES)
        try:
            self.persistence_file.write_text(
                json.dumps({"names": sorted(generated)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # La persistance est un plus, pas une obligation

    def reset_history(self):
        """Efface l'historique des noms générés (retour à la liste d'origine)."""
        self.existing_names = set(EXISTING_NAMES)
        if self.persistence_file.exists():
            self.persistence_file.unlink()

    def generate_name(self):
        """Génère un nouveau nom inspiré de lieux et d'éléments vintage.

        Lève RuntimeError si aucune combinaison valide n'est trouvée
        après MAX_ATTEMPTS tentatives (protection contre la boucle infinie).
        """
        for _ in range(MAX_ATTEMPTS):
            method = random.choice([
                self.generate_from_place,
                self.generate_from_vintage,
                self.generate_mixed_name
            ])
            name = method()

            if (name not in self.existing_names
                    and name not in REAL_WORDS_TO_AVOID
                    and self.is_pronounceable(name)):
                self.existing_names.add(name)
                self._save_generated_names()
                return name

        raise RuntimeError(
            f"Aucun nom valide trouvé après {MAX_ATTEMPTS} tentatives. "
            "Enrichissez les listes d'inspiration ou réinitialisez l'historique (--reset)."
        )

    def generate_from_place(self):
        """Génère un nom inspiré d'un lieu."""
        place = random.choice(self.places)
        if len(place) > 6:
            # Prend une partie du nom
            start = random.randint(0, len(place) - 4)
            length = random.randint(4, 6)
            return place[start:start + length].upper()
        return place.upper()

    def generate_from_vintage(self):
        """Génère un nom inspiré d'éléments vintage."""
        element = random.choice(self.vintage)
        if len(element) > 6:
            # Prend une partie du nom
            start = random.randint(0, len(element) - 4)
            length = random.randint(4, 6)
            return element[start:start + length].upper()
        return element.upper()

    def generate_mixed_name(self):
        """Combine des éléments de lieux et vintage."""
        source1 = random.choice(self.places + self.vintage)
        source2 = random.choice(self.places + self.vintage)

        # Prend quelques lettres de chaque source
        part1 = source1[:random.randint(2, 3)]
        part2 = source2[:random.randint(2, 3)]

        return (part1 + part2).upper()

    def is_pronounceable(self, name):
        """Vérifie si le nom est prononçable (accents gérés)."""
        name = strip_accents(name)
        if len(name) < 3:
            return False

        # Vérifie qu'il n'y a pas trop de consonnes consécutives
        consonant_count = 0
        for char in name:
            if char in self.consonants:
                consonant_count += 1
                if consonant_count > 3:
                    return False
            else:
                consonant_count = 0

        # Vérifie qu'il y a au moins une voyelle
        return any(char in self.vowels for char in name)

    def generate_meaning(self):
        """Génère une définition conceptuelle du carreau."""
        style = random.choice([
            "Collection inspirée de la nature",
            "Série évoquant la pureté des éléments",
            "Gamme aux tons minéraux",
            "Collection de style épuré",
            "Série aux lignes élégantes",
            "Gamme contemporaine raffinée"
        ])
        ambiance = random.choice([
            "pour une ambiance sereine",
            "créant une atmosphère apaisante",
            "apportant douceur et élégance",
            "pour un style intemporel",
            "offrant une touche de raffinement",
            "créant un espace harmonieux"
        ])
        inspiration = random.choice([
            "Inspiré des éléments naturels",
            "Puisant dans la beauté de la nature",
            "S'inspirant des matières nobles",
            "Évoquant la pureté des formes",
            "Né de l'harmonie des éléments",
            "Inspiré des textures naturelles"
        ])

        return f"{style}. {inspiration}, {ambiance}."

    def generate_multiple_names(self, count=5):
        """Génère plusieurs noms uniques avec leurs significations."""
        suggestions = []
        for _ in range(count):
            name = self.generate_name()
            meaning = self.generate_meaning()
            suggestions.append((name, meaning))
        return suggestions


def print_suggestions(suggestions):
    """Affiche un tableau formaté des suggestions."""
    print("\nCATALOGUE DE CARREAUX CÉRAMIQUES")
    print("=" * 80)
    print("NOM        | DESCRIPTION")
    print("-" * 80)

    for name, description in suggestions:
        print(f"{name:<10} | {description}")
        print("-" * 80)  # Ligne de séparation entre chaque modèle

    print("=" * 80)
    print()


def export_to_csv(suggestions, filepath):
    """Exporte les suggestions dans un fichier CSV."""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Nom", "Description"])
        writer.writerows(suggestions)
    print(f"Export CSV réussi : {filepath}")


def suggest_names(count=5):
    """Fonction principale pour suggérer de nouveaux noms (compatibilité V1)."""
    generator = TileNameGenerator()
    return generator.generate_multiple_names(count)


def main():
    parser = argparse.ArgumentParser(
        description="Générateur de noms pour catalogue de carreaux céramiques."
    )
    parser.add_argument("-n", "--count", type=int, default=20,
                        help="Nombre de noms à générer (défaut : 20)")
    parser.add_argument("-e", "--export", metavar="FICHIER",
                        help="Exporter aussi les résultats en CSV (ex. catalogue.csv)")
    parser.add_argument("--reset", action="store_true",
                        help="Effacer l'historique des noms générés puis quitter")
    args = parser.parse_args()

    generator = TileNameGenerator()

    if args.reset:
        generator.reset_history()
        print("Historique des noms générés effacé.")
        return

    suggestions = generator.generate_multiple_names(args.count)
    print_suggestions(suggestions)

    if args.export:
        export_to_csv(suggestions, args.export)


if __name__ == "__main__":
    main()
