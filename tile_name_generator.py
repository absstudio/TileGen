import random
from collections import defaultdict

# Liste des noms existants
EXISTING_NAMES = [
    "ARTIC", "ROYAL", "CASTLE", "ROCA", "FAÇADE", "TERRANGA", "AZAR",
    "ARDOISE", "SHERPA", "SAFRAN", "PLATINE", "FUJI", "TIGER",
    "TRAVARTINO", "ASTON", "DYNAMIC", "ELECTRA", "FLASH", "HOGGAR",
    "MIRAGE", "PLAYA", "SINA MARFIL", "STREET", "TECHNO", "VENUS",
    "VINTAGE", "VOYAGE", "ARAR", "BLACKOS", "BREAKING", "CAMEL",
    "COSTA", "DUNE", "ERUPTION", "FLASH"
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

class TileNameGenerator:
    def __init__(self):
        self.existing_names = set(EXISTING_NAMES)
        self.vowels = set('AEIOU')
        self.consonants = set('BCDFGHLMNPRSTVZ')
        self.places = PLACES_INSPIRATION
        self.vintage = VINTAGE_ELEMENTS

    def generate_name(self):
        """Génère un nouveau nom inspiré de lieux et d'éléments vintage."""
        while True:
            method = random.choice([
                self.generate_from_place,
                self.generate_from_vintage,
                self.generate_mixed_name
            ])
            name = method()
            
            if name not in self.existing_names and self.is_pronounceable(name):
                self.existing_names.add(name)
                return name

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
        """Vérifie si le nom est prononçable."""
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
        has_vowel = False
        for char in name:
            if char in self.vowels:
                has_vowel = True
                break
        
        return has_vowel

    def generate_meaning(self):
        """Génère une définition conceptuelle du carreau"""
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
        """Génère plusieurs noms uniques avec leurs significations"""
        suggestions = []
        for _ in range(count):
            name = self.generate_name()
            meaning = self.generate_meaning()
            suggestions.append((name, meaning))
        return suggestions

def print_suggestions(suggestions):
    print("\nCATALOGUE DE CARREAUX CÉRAMIQUES")
    print("=" * 80)
    print("NOM        | DESCRIPTION")
    print("-" * 80)
    
    for name, description in suggestions:
        print(f"{name:<10} | {description}")
        print("-" * 80)  # Ligne de séparation entre chaque modèle
    
    print("=" * 80)
    print()

def suggest_names(count=5):
    """Fonction principale pour suggérer de nouveaux noms"""
    generator = TileNameGenerator()
    return generator.generate_multiple_names(count)

if __name__ == "__main__":
    suggestions = suggest_names(20)
    print_suggestions(suggestions)
