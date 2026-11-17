# -*- coding: utf-8 -*-
"""
TileGen v3 — Générateur de noms pour catalogue de carreaux céramiques.

Nouveautés v3 :
- Interface terminal inspirée d'OpenCode : boîtes arrondies, couleurs, hiérarchie claire
- Noms plus explicites : étymologie affichée (le nom indique de quoi il s'inspire)
- Mode IA (facultatif) : entrez votre clé API pour générer des noms avec un LLM
  compatible OpenAI (OpenAI, DeepSeek, Groq, Mistral...).

Commandes :
  python tilegen.py                     # mode local (aucune clé nécessaire)
  python tilegen.py --count 10          # nombre de noms souhaité
  python tilegen.py --ai                # génération par IA
  python tilegen.py --configure-ai      # configurer la clé API une fois pour toutes
  python tilegen.py --export cat.csv    # export Excel
  python tilegen.py --reset             # effacer l'historique
"""

import argparse
import csv
import getpass
import json
import os
import random
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

GENERATED_NAMES_FILE = Path(__file__).parent / "noms_generes.json"
CONFIG_FILE = Path(__file__).parent / "tilegen_config.json"
MAX_ATTEMPTS = 1000
VERSION = "3.0"

# ============================================================
#  Interface terminal — style OpenCode
#  (boîtes arrondies, gris discret, un seul accent orange)
# ============================================================

class UI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ACCENT = "\033[38;5;208m"    # orange OpenCode
    GREY = "\033[38;5;243m"
    TEXT = "\033[38;5;253m"
    GREEN = "\033[38;5;71m"
    RED = "\033[38;5;167m"

if os.name == "nt":
    os.system("")  # active les couleurs ANSI dans le terminal Windows


def _visible_len(text):
    """Longueur visible d'une chaîne (sans les codes ANSI)."""
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def box(lines, title=None, width=76):
    """Dessine une boîte arrondie façon OpenCode."""
    out = []
    top = f"╭─ {title} " if title else "╭"
    out.append(UI.GREY + top + "─" * (width - _visible_len(top) - 1) + "╮" + UI.RESET)
    for line in lines:
        pad = width - _visible_len(line) - 2
        out.append(UI.GREY + "│ " + UI.RESET + line + " " * max(pad, 0) + UI.GREY + " │" + UI.RESET)
    out.append(UI.GREY + "╰" + "─" * (width - 2) + "╯" + UI.RESET)
    return "\n".join(out)


def wrap_text(text, width):
    """Coupe un texte en lignes de `width` caractères max."""
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = (current + " " + word).strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def ui_header(mode):
    """Bannière d'accueil TileGen."""
    lines = [
        f"{UI.BOLD}{UI.ACCENT}TileGen{UI.RESET}{UI.GREY}  v{VERSION}{UI.RESET}",
        f"{UI.TEXT}Générateur de noms de carreaux céramiques{UI.RESET}",
        f"{UI.GREY}mode : {mode}{UI.RESET}",
    ]
    print(box(lines, title="tilegen"))
    print()


def ui_results(suggestions, mode):
    """Affiche les suggestions dans une boîte façon OpenCode."""
    lines = []
    for i, (name, desc) in enumerate(suggestions):
        num = f"{UI.GREY}{i + 1:>2}.{UI.RESET} "
        label = f"{UI.BOLD}{UI.ACCENT}{name:<9}{UI.RESET} "
        first, *rest = wrap_text(desc, 58)
        lines.append(f"{num}{label}{UI.TEXT}{first}{UI.RESET}")
        for extra in rest:
            lines.append(f"{UI.GREY}    {UI.RESET}{UI.GREY}{extra}{UI.RESET}")
        if i < len(suggestions) - 1:
            lines.append(f"{UI.GREY}    ····························································{UI.RESET}")
    print(box(lines, title=f"suggestions · {len(suggestions)}"))


def ui_footer(count, mode, history_file):
    """Ligne d'état en bas, comme une barre d'état OpenCode."""
    parts = [
        f"{UI.GREEN}{count} noms{UI.RESET}",
        f"{UI.GREY}mode {mode}{UI.RESET}",
        f"{UI.GREY}historique : {history_file.name}{UI.RESET}",
    ]
    print("\n" + "  ".join(parts))


def ui_error(message):
    print(box([f"{UI.RED}{message}{UI.RESET}"], title="erreur"))


def ui_info(message):
    print(f"{UI.GREY}{message}{UI.RESET}")

# ============================================================
#  Données
# ============================================================

EXISTING_NAMES = [
    "ARTIC", "ROYAL", "CASTLE", "ROCA", "FAÇADE", "TERRANGA", "AZAR",
    "ARDOISE", "SHERPA", "SAFRAN", "PLATINE", "FUJI", "TIGER",
    "TRAVARTINO", "ASTON", "DYNAMIC", "ELECTRA", "FLASH", "HOGGAR",
    "MIRAGE", "PLAYA", "SINA MARFIL", "STREET", "TECHNO", "VENUS",
    "VINTAGE", "VOYAGE", "ARAR", "BLACKOS", "BREAKING", "CAMEL",
    "COSTA", "DUNE", "ERUPTION"
]

PLACES_INSPIRATION = [
    "PETRA", "ROMA", "CAIRO", "PARIS", "VENICE", "PORTO", "MILAN",
    "VIENNA", "PRAGUE", "SEOUL", "TOKYO", "KYOTO", "DELHI", "DUBAI",
    "SAHARA", "ATLAS", "ANDES", "ALPES", "NILE", "CONGO",
    "AMAZON", "GOBI", "TUNDRA", "SIERRA", "OASIS",
    "CASTLE", "PALACE", "TEMPLE", "TOWER", "OPERA", "PLAZA", "ARENA",
    "SOHO", "MARAIS", "BORGO", "MEDINA", "KASBAH"
]

VINTAGE_ELEMENTS = [
    "DECO", "RETRO", "LOFT", "MANOR", "VILLA", "ROYAL", "NOBLE",
    "MARBLE", "ONYX", "BRASS", "COPPER", "SILVER", "PEARL", "IVORY",
    "ARCADE", "COLUMN", "MOSAIC", "FRESCO", "VAULT", "ARCH",
    "EMPIRE", "REGENT", "LEGACY", "CROWN", "GLORY", "GRAND"
]

REAL_WORDS_TO_AVOID = {
    "CASTLE", "PALACE", "TEMPLE", "TOWER", "OPERA", "PLAZA", "ARENA",
    "OASIS", "RETRO", "LOFT", "VILLA", "NOBLE", "MARBLE", "SILVER",
    "PEARL", "IVORY", "ARCADE", "COLUMN", "MOSAIC", "FRESCO",
    "VAULT", "ARCH", "EMPIRE", "LEGACY", "CROWN", "GLORY", "GRAND",
    "SOHO", "TUNDRA", "SIERRA", "AMAZON", "ROYAL", "VINTAGE",
    "DECO", "REGENT", "MANOR", "ONYX", "BRASS", "COPPER"
}

# Suffixes « céramique italienne » pour des noms élégants et explicites
PREMIUM_SUFFIXES = ["NO", "NA", "RA", "INA", "ANA", "ELLA", "ETTA", "INO", "RIA", "ELLO"]

STYLES = [
    "Collection inspirée de la nature", "Série évoquant la pureté des éléments",
    "Gamme aux tons minéraux", "Collection de style épuré",
    "Série aux lignes élégantes", "Gamme contemporaine raffinée"
]
AMBIANCES = [
    "pour une ambiance sereine", "créant une atmosphère apaisante",
    "apportant douceur et élégance", "pour un style intemporel",
    "offrant une touche de raffinement", "créant un espace harmonieux"
]


def strip_accents(text):
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

# ============================================================
#  Générateur local — noms explicites avec étymologie
# ============================================================

class TileNameGenerator:
    def __init__(self, persistence_file=GENERATED_NAMES_FILE):
        self.persistence_file = Path(persistence_file)
        self.vowels = set('AEIOU')
        self.consonants = set('BCDFGHLMNPRSTVZ')
        self.sources_pool = PLACES_INSPIRATION + VINTAGE_ELEMENTS
        self.existing_names = set(EXISTING_NAMES) | self._load_generated_names()

    # ----- persistance -----
    def _load_generated_names(self):
        if self.persistence_file.exists():
            try:
                return set(json.loads(self.persistence_file.read_text(encoding="utf-8")).get("names", []))
            except (json.JSONDecodeError, OSError):
                return set()
        return set()

    def _save_generated_names(self):
        generated = self.existing_names - set(EXISTING_NAMES)
        try:
            self.persistence_file.write_text(
                json.dumps({"names": sorted(generated)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def reset_history(self):
        self.existing_names = set(EXISTING_NAMES)
        if self.persistence_file.exists():
            self.persistence_file.unlink()

    # ----- outils de découpe -----
    def _stem(self, word, min_len=3, max_len=7, at_vowel=True):
        """Coupe un mot à la fin d'une voyelle pour un nom élégant (ex. VENICE -> VENI)."""
        w = strip_accents(word)
        if at_vowel:
            positions = [i for i, ch in enumerate(w[:max_len]) if ch in self.vowels]
            if len(positions) >= 2:
                cut = positions[-2] + 1  # avant-dernière voyelle (garde une syllabe de marge)
                if cut >= min_len:
                    return w[:cut]
            if positions and positions[-1] + 1 >= min_len:
                return w[:positions[-1] + 1]
        return w[:min(max_len, len(w))]

    def is_valid(self, name):
        return (name not in self.existing_names
                and name not in REAL_WORDS_TO_AVOID
                and self.is_pronounceable(name))

    def is_pronounceable(self, name):
        if len(name) < 3:
            return False
        count = 0
        for ch in name:
            if ch in self.consonants:
                count += 1
                if count > 3:
                    return False
            else:
                count = 0
        if not any(ch in self.vowels for ch in name):
            return False
        return name[-1] in self.vowels  # se termine par une voyelle => sonorité élégante

    # ----- génération -----
    def generate_name(self):
        """Retourne (nom, sources) : le nom et les mots qui l'inspirent."""
        for _ in range(MAX_ATTEMPTS):
            method = random.choice([self._from_single_source, self._from_two_sources])
            result = method()
            if result and self.is_valid(result[0]):
                name, sources = result
                self.existing_names.add(name)
                self._save_generated_names()
                return name, sources
        raise RuntimeError(
            f"Aucun nom valide trouvé après {MAX_ATTEMPTS} tentatives. "
            "Utilisez --reset ou enrichissez les listes d'inspiration."
        )

    def _from_single_source(self):
        """SAHARA -> SAHANA / PETRA -> PETRINA : un lieu + un suffixe noble."""
        source = random.choice(self.sources_pool)
        stem = self._stem(source, min_len=3, max_len=6)
        if stem == strip_accents(source):
            stem = self._stem(source, min_len=3, max_len=6, at_vowel=False)
        # Évite les doubles voyelles (PETRA+ELLO) et les noms trop longs
        candidates = [
            s for s in PREMIUM_SUFFIXES
            if len(stem + s) <= 9 and not (stem[-1] in self.vowels and s[0] in self.vowels)
        ]
        if not candidates:
            return None
        name = stem + random.choice(candidates)
        return name, [source]

    def _from_two_sources(self):
        """VENICE + MARBLE -> VENMAR : fusion de deux racines explicites."""
        s1 = random.choice(self.sources_pool)
        s2 = random.choice(self.sources_pool)
        if s1 == s2:
            return None
        part1 = self._stem(s1, min_len=2, max_len=4)
        part2 = strip_accents(s2)[:random.randint(3, 4)].lower()
        # Évite les jonctions en double lettre (SEO+OWE -> SEOO...)
        if part1[-1].lower() == part2[0].lower():
            return None
        name = (part1 + part2).upper()[:9]
        return name, [s1, s2]

    def generate_meaning(self, sources):
        """Description explicite : cite les mots à l'origine du nom."""
        if sources:
            origin = f"Évoque {sources[0].capitalize()}"
            if len(sources) > 1:
                origin += f" et {sources[1].capitalize()}"
            origin += ". "
        else:
            origin = ""
        return f"{origin}{random.choice(STYLES)}, {random.choice(AMBIANCES)}."

    def generate_multiple_names(self, count=5):
        suggestions = []
        for _ in range(count):
            name, sources = self.generate_name()
            suggestions.append((name, self.generate_meaning(sources)))
        return suggestions

# ============================================================
#  Mode IA — compatible OpenAI (OpenAI, DeepSeek, Groq, Mistral...)
# ============================================================

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def configure_ai():
    """Configuration interactive de la clé API (sauvegardée localement)."""
    print(box([
        f"{UI.TEXT}Configurez votre accès à l'IA (compatible OpenAI).{UI.RESET}",
        f"{UI.GREY}Exemples de base_url :{UI.RESET}",
        f"{UI.GREY}  OpenAI  : https://api.openai.com/v1   (modèle gpt-4o-mini){UI.RESET}",
        f"{UI.GREY}  DeepSeek: https://api.deepseek.com/v1 (modèle deepseek-chat){UI.RESET}",
        f"{UI.GREY}  Groq    : https://api.groq.com/openai/v1 (modèle llama-3.3-70b-versatile){UI.RESET}",
        f"{UI.GREY}  Mistral : https://api.mistral.ai/v1   (modèle mistral-small-latest){UI.RESET}",
    ], title="configuration IA"))
    print()

    cfg = load_config()
    cfg["api_key"] = getpass.getpass(f"  Clé API {UI.GREY}(entrée masquée){UI.RESET} : ").strip()
    cfg["base_url"] = input(f"  Base URL {UI.GREY}[https://api.openai.com/v1]{UI.RESET} : ").strip() or "https://api.openai.com/v1"
    cfg["model"] = input(f"  Modèle {UI.GREY}[gpt-4o-mini]{UI.RESET} : ").strip() or "gpt-4o-mini"

    if not cfg["api_key"]:
        ui_error("Clé API vide : configuration annulée.")
        sys.exit(1)

    save_config(cfg)
    print()
    print(box([f"{UI.GREEN}Configuration enregistrée dans {CONFIG_FILE.name}.{UI.RESET}",
               f"{UI.GREY}Lancez : python tilegen.py --ai{UI.RESET}"], title="terminé"))


def ai_generate_names(count, cfg):
    """Génère des noms via l'API (format OpenAI /chat/completions)."""
    api_key = os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")
    base_url = (cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("model") or "gpt-4o-mini"

    if not api_key:
        ui_error("Aucune clé API configurée. Lancez : python tilegen.py --configure-ai")
        sys.exit(1)

    existing = ", ".join(sorted(EXISTING_NAMES)[:15]) + "..."
    prompt = (
        f"Tu es un expert en naming de produits céramiques. Génère exactement {count} noms "
        f"de collections de carreaux, inspirés de lieux du monde et de matières nobles. "
        f"Évite ces noms déjà utilisés : {existing}\n"
        f"Contraintes : 4 à 9 lettres, prononçables, sonorité méditerranéenne élégante, "
        f"pas de mots anglais courants, uniques entre eux.\n"
        f"Pour chaque nom, ajoute une description commerciale d'une phrase en français "
        f"qui explique l'inspiration.\n"
        f'Réponds UNIQUEMENT avec un JSON : [{{"name": "...", "description": "..."}}, ...]'
    )

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        detail = " ".join(e.read().decode("utf-8", errors="replace").split())[:150]
        ui_error(f"Erreur API {e.code} : {detail}")
        ui_info("Vérifiez votre clé, votre base_url et votre modèle (python tilegen.py --configure-ai).")
        sys.exit(1)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        ui_error(f"Impossible de joindre l'API : {e}")
        sys.exit(1)

    # Nettoyage de la réponse (l'IA entoure parfois le JSON de ```json ... ```)
    content = re.sub(r"```(?:json)?|```", "", content).strip()
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        ui_error("Réponse IA illisible : le modèle n'a pas renvoyé de JSON.")
        sys.exit(1)

    items = json.loads(match.group(0))
    suggestions = []
    for item in items[:count]:
        name = str(item.get("name", "")).strip().upper()[:12]
        desc = str(item.get("description", "")).strip()
        if name:
            suggestions.append((name, desc or "Nom généré par IA."))
    return suggestions

# ============================================================
#  Export / compatibilité
# ============================================================

def export_to_csv(suggestions, filepath):
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Nom", "Description"])
        writer.writerows(suggestions)
    print(f"{UI.GREEN}Export CSV réussi : {filepath}{UI.RESET}")


def suggest_names(count=5):
    """Compatibilité : import du module dans un script Python."""
    gen = TileNameGenerator()
    return gen.generate_multiple_names(count)


def print_suggestions(suggestions):
    ui_header("local")
    ui_results(suggestions, "local")

# ============================================================
#  Point d'entrée
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="tilegen",
        description="TileGen — Générateur de noms de carreaux céramiques (local ou IA).",
    )
    parser.add_argument("-n", "--count", type=int, default=20,
                        help="Nombre de noms à générer (défaut : 20)")
    parser.add_argument("--ai", action="store_true",
                        help="Générer les noms avec l'IA (clé API requise)")
    parser.add_argument("--configure-ai", action="store_true",
                        help="Configurer la clé API, la base URL et le modèle")
    parser.add_argument("-e", "--export", metavar="FICHIER",
                        help="Exporter les résultats en CSV (ex. catalogue.csv)")
    parser.add_argument("--reset", action="store_true",
                        help="Effacer l'historique des noms générés puis quitter")
    args = parser.parse_args()

    # ----- configuration IA -----
    if args.configure_ai:
        configure_ai()
        return

    generator = TileNameGenerator()

    if args.reset:
        generator.reset_history()
        print(f"{UI.GREEN}Historique des noms générés effacé.{UI.RESET}")
        return

    # ----- génération -----
    if args.ai:
        cfg = load_config()
        ui_header(f"IA · {cfg.get('model', 'à configurer')}")
        ui_info("Génération via l'IA en cours...")
        suggestions = ai_generate_names(args.count, cfg)
        # Mémorise aussi les noms IA pour éviter les doublons futurs
        for name, _ in suggestions:
            generator.existing_names.add(name)
        generator._save_generated_names()
        mode = "IA"
    else:
        ui_header("local")
        suggestions = generator.generate_multiple_names(args.count)
        mode = "local"

    # ----- affichage -----
    print()
    ui_results(suggestions, mode)
    ui_footer(len(suggestions), mode, GENERATED_NAMES_FILE)

    if args.export:
        export_to_csv(suggestions, args.export)


if __name__ == "__main__":
    main()
