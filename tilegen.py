# -*- coding: utf-8 -*-
"""
TileGen v3.1 — Générateur de noms pour catalogue de carreaux céramiques.

Au lancement (python tilegen.py) : page d'accueil interactive façon OpenCode
(logo, menu, paramètres). Les options en ligne de commande restent disponibles
pour l'automatisation :
  python tilegen.py --count 10          # direct, sans menu
  python tilegen.py --ai                # direct, mode IA
  python tilegen.py --configure-ai      # configurer la clé API
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
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

GENERATED_NAMES_FILE = Path(__file__).parent / "noms_generes.json"
CONFIG_FILE = Path(__file__).parent / "tilegen_config.json"
MAX_ATTEMPTS = 1000
VERSION = "3.1"

# ============================================================
#  Interface terminal — style OpenCode
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


def clear_screen():
    print("\033[2J\033[H", end="")


def _visible_len(text):
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def box(lines, title=None, width=76):
    """Dessine une boîte arrondie façon OpenCode."""
    out = []
    top = f"╭─ {title} " if title else "╭"
    out.append(UI.GREY + top + "─" * (width - _visible_len(top) - 1) + "╮" + UI.RESET)
    for line in lines:
        pad = width - _visible_len(line) - 4  # "│ " + contenu + " │" = 4 caractères fixes
        out.append(UI.GREY + "│ " + UI.RESET + line + " " * max(pad, 0) + UI.GREY + " │" + UI.RESET)
    out.append(UI.GREY + "╰" + "─" * (width - 2) + "╯" + UI.RESET)
    return "\n".join(out)


def wrap_text(text, width):
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


LOGO = [
    "████████╗ ██╗     ██╗     ███████╗  ██████╗ ███████╗ ███╗   ██╗",
    "╚══██╔╝   ██║     ██║     ██╔════╝ ██╔════╝ ██╔════╝ ████╗  ██║",
    "   ██║    ██║     ██║     █████╗   ██║  ███╗ █████╗   ██╔██╗ ██║",
    "   ██║    ██║     ██║     ██╔══╝   ██║   ██║ ██╔══╝   ██║╚██╗██║",
    "   ██║    ███████╗███████╗███████╗ ╚██████╔╝ ███████╗ ██║ ╚████║",
    "   ╚═╝    ╚══════╝╚══════╝╚══════╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝",
]


def ui_header(mode):
    """Petit en-tête (mode non interactif)."""
    lines = [
        f"{UI.BOLD}{UI.ACCENT}TileGen{UI.RESET}{UI.GREY}  v{VERSION}{UI.RESET}",
        f"{UI.TEXT}Générateur de noms de carreaux céramiques{UI.RESET}",
        f"{UI.GREY}mode : {mode}{UI.RESET}",
    ]
    print(box(lines, title="tilegen"))
    print()


def home_screen():
    """Page d'accueil interactive façon OpenCode : logo + menu."""
    clear_screen()
    width = 66
    print()
    for line in LOGO:
        pad = (width - len(line)) // 2
        print(" " * pad + UI.ACCENT + UI.BOLD + line + UI.RESET)
    print()
    subtitle = f"{UI.GREY}v{VERSION}  ·  générateur de noms de carreaux céramiques{UI.RESET}"
    print(subtitle.center(width + 10))
    print()
    print(box(
        [f"{UI.GREY}Lancez {UI.RESET}{UI.TEXT}python tilegen.py --help{UI.RESET}{UI.GREY} "
         f"pour les options directes{UI.RESET}"],
        width=width + 4,
    ))
    print()


def ask(prompt, default=""):
    """Entrée utilisateur avec valeur par défaut."""
    suffix = f" {UI.GREY}[{default}]{UI.RESET}" if default != "" else ""
    value = input(f"  {UI.ACCENT}❯{UI.RESET} {prompt}{suffix} : ").strip()
    return value or default


def ask_count():
    while True:
        raw = ask("Nombre de noms à générer", "20")
        try:
            count = int(raw)
            if 1 <= count <= 100:
                return count
        except ValueError:
            pass
        ui_error("Entrez un nombre entre 1 et 100.")


def ui_menu():
    """Menu principal, sélection par numéro."""
    items = [
        ("1", "Générer des noms", "mode local, aucune clé nécessaire"),
        ("2", "Générer avec l'IA", "clé API requise (OpenAI, Gemini...)"),
        ("3", "Configurer l'IA", "fournisseur, clé API, modèle"),
        ("4", "Tester l'API", "vérifier que la connexion IA marche"),
        ("5", "Effacer l'historique", "repartir de zéro"),
        ("q", "Quitter", ""),
    ]
    lines = []
    for key, label, hint in items:
        lines.append(f"  {UI.ACCENT}{UI.BOLD}{key}{UI.RESET}. {UI.TEXT}{label:<22}{UI.RESET}"
                     f"{UI.GREY}{hint}{UI.RESET}")
    print(box(lines, title="menu"))
    return input(f"\n  {UI.ACCENT}❯{UI.RESET} ").strip().lower()


def ui_results(suggestions, mode):
    lines = []
    for i, (name, desc) in enumerate(suggestions):
        num = f"{UI.GREY}{i + 1:>2}.{UI.RESET} "
        label = f"{UI.BOLD}{UI.ACCENT}{name:<9}{UI.RESET} "
        first, *rest = wrap_text(desc, 58)
        lines.append(f"{num}{label}{UI.TEXT}{first}{UI.RESET}")
        for extra in rest:
            lines.append(f"{UI.GREY}    {UI.GREY}{extra}{UI.RESET}")
        if i < len(suggestions) - 1:
            lines.append(f"{UI.GREY}    ····························································{UI.RESET}")
    print(box(lines, title=f"suggestions · {len(suggestions)}"))


def ui_footer(count, mode, history_file):
    parts = [
        f"{UI.GREEN}{count} noms{UI.RESET}",
        f"{UI.GREY}mode {mode}{UI.RESET}",
        f"{UI.GREY}historique : {history_file.name}{UI.RESET}",
    ]
    print("\n" + "  ".join(parts))


def post_generation(suggestions):
    """Actions après génération : exporter, menu, quitter."""
    print()
    print(box([
        f"{UI.TEXT}{UI.BOLD}Entrée{UI.RESET}{UI.GREY} retour au menu   "
        f"{UI.TEXT}{UI.BOLD}e{UI.RESET}{UI.GREY} exporter en CSV   "
        f"{UI.TEXT}{UI.BOLD}q{UI.RESET}{UI.GREY} quitter{UI.RESET}"
    ], width=60))
    choice = input(f"  {UI.ACCENT}❯{UI.RESET} ").strip().lower()
    if choice == "e":
        filepath = ask("Nom du fichier", "catalogue.csv")
        export_to_csv(suggestions, filepath)
        input(f"\n  {UI.GREY}Entrée pour continuer...{UI.RESET}")


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

    def _stem(self, word, min_len=3, max_len=7, at_vowel=True):
        w = strip_accents(word)
        if at_vowel:
            positions = [i for i, ch in enumerate(w[:max_len]) if ch in self.vowels]
            if len(positions) >= 2:
                cut = positions[-2] + 1
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
        return name[-1] in self.vowels

    def generate_name(self):
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
        source = random.choice(self.sources_pool)
        stem = self._stem(source, min_len=3, max_len=6)
        if stem == strip_accents(source):
            stem = self._stem(source, min_len=3, max_len=6, at_vowel=False)
        candidates = [
            s for s in PREMIUM_SUFFIXES
            if len(stem + s) <= 9 and not (stem[-1] in self.vowels and s[0] in self.vowels)
        ]
        if not candidates:
            return None
        name = stem + random.choice(candidates)
        return name, [source]

    def _from_two_sources(self):
        s1 = random.choice(self.sources_pool)
        s2 = random.choice(self.sources_pool)
        if s1 == s2:
            return None
        part1 = self._stem(s1, min_len=2, max_len=4)
        part2 = strip_accents(s2)[:random.randint(3, 4)].lower()
        if part1[-1].lower() == part2[0].lower():
            return None
        name = (part1 + part2).upper()[:9]
        return name, [s1, s2]

    def generate_meaning(self, sources):
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
#  Mode IA — compatible OpenAI
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


# Presets de fournisseurs compatibles OpenAI (nom, base_url, modèle par défaut)
AI_PRESETS = [
    ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("Google AI Studio (Gemini)", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash"),
    ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("Groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("Mistral", "https://api.mistral.ai/v1", "mistral-small-latest"),
    ("Autre / personnalisé", "", ""),
]


def configure_ai():
    """Configuration interactive : choix du fournisseur, clé API, puis test."""
    lines = [
        f"{UI.TEXT}Choisissez votre fournisseur IA (compatible OpenAI) :{UI.RESET}",
        "",
    ]
    for i, (name, _, model) in enumerate(AI_PRESETS, 1):
        hint = f"{UI.GREY}{model}{UI.RESET}" if model else f"{UI.GREY}base URL et modèle libres{UI.RESET}"
        lines.append(f"  {UI.ACCENT}{UI.BOLD}{i}{UI.RESET}. {UI.TEXT}{name:<28}{UI.RESET}{hint}")
    print(box(lines, title="configuration IA"))
    print()

    choice = ask("Fournisseur", "1")
    try:
        preset = AI_PRESETS[int(choice) - 1]
    except (ValueError, IndexError):
        ui_error("Choix invalide : configuration annulée.")
        return False

    name, base_url, model = preset
    print()

    if name == "Google AI Studio (Gemini)":
        ui_info(f"Clé gratuite sur {UI.RESET}{UI.TEXT}https://aistudio.google.com/apikey{UI.RESET}"
                f"{UI.GREY} (Get API key → Create API key){UI.RESET}")
        print()

    cfg = load_config()
    cfg["api_key"] = getpass.getpass(f"  {UI.ACCENT}❯{UI.RESET} Clé API {UI.GREY}(entrée masquée){UI.RESET} : ").strip()
    if not cfg["api_key"]:
        ui_error("Clé API vide : configuration annulée.")
        return False

    if base_url:
        cfg["base_url"] = ask(f"Base URL {UI.GREY}[{base_url}]{UI.RESET}", base_url)
        cfg["model"] = ask(f"Modèle {UI.GREY}[{model}]{UI.RESET}", model)
    else:
        cfg["base_url"] = ask("Base URL", "https://api.openai.com/v1")
        cfg["model"] = ask("Modèle", "gpt-4o-mini")

    save_config(cfg)
    print()
    print(box([f"{UI.GREEN}Configuration enregistrée dans {CONFIG_FILE.name}.{UI.RESET}"],
              title="terminé"))
    print()

    # Test immédiat de la connexion
    if ask("Tester la connexion maintenant ?", "O").lower() in ("o", "oui", "y", "yes"):
        ok, message = test_api(cfg)
        if ok:
            print(box([f"{UI.GREEN}{message}{UI.RESET}"], title="test API · succès"))
        else:
            print(box([f"{UI.RED}{message}{UI.RESET}",
                       f"{UI.GREY}Vérifiez la clé, la base URL et le modèle, puis reconfigurez.{UI.RESET}"],
                      title="test API · échec"))
    return True


def test_api(cfg=None):
    """Envoie une requête minimale pour vérifier que l'API répond.

    Retourne (True, message) ou (False, message d'erreur).
    """
    cfg = cfg or load_config()
    api_key = os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")
    base_url = (cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("model") or "gpt-4o-mini"

    if not api_key:
        return False, "Aucune clé API configurée."

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Réponds uniquement par : OK"}],
        "max_tokens": 10,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            reply = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        latency = time.monotonic() - start
        return True, f"Connexion réussie · {model} · {latency:.1f}s · réponse : « {reply.strip()[:30]} »"
    except urllib.error.HTTPError as e:
        detail = " ".join(e.read().decode("utf-8", errors="replace").split())[:120]
        return False, f"Erreur {e.code} : {detail}"
    except urllib.error.URLError as e:
        return False, f"Impossible de joindre {base_url} : {e.reason}"
    except (KeyError, json.JSONDecodeError) as e:
        return False, f"Réponse inattendue de l'API : {e}"


def ai_generate_names(count, cfg):
    """Génère des noms via l'API (format OpenAI /chat/completions)."""
    api_key = os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")
    base_url = (cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("model") or "gpt-4o-mini"

    if not api_key:
        ui_error("Aucune clé API configurée. Choisissez « Configurer l'IA » dans le menu.")
        return None

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
        ui_info("Vérifiez votre clé, votre base_url et votre modèle (menu « Configurer l'IA »).")
        return None
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        ui_error(f"Impossible de joindre l'API : {e}")
        return None

    content = re.sub(r"```(?:json)?|```", "", content).strip()
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        ui_error("Réponse IA illisible : le modèle n'a pas renvoyé de JSON.")
        return None

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
#  Session interactive (page d'accueil façon OpenCode)
# ============================================================

def interactive_session():
    home_screen()
    generator = TileNameGenerator()
    cfg = load_config()

    while True:
        choice = ui_menu()

        if choice == "q":
            print(f"\n{UI.GREY}À bientôt — TileGen v{VERSION}{UI.RESET}\n")
            break

        elif choice == "1":
            count = ask_count()
            print()
            try:
                suggestions = generator.generate_multiple_names(count)
            except RuntimeError as e:
                ui_error(str(e))
                continue
            print()
            ui_results(suggestions, "local")
            ui_footer(len(suggestions), "local", GENERATED_NAMES_FILE)
            post_generation(suggestions)

        elif choice == "2":
            count = ask_count()
            print()
            ui_info("Génération via l'IA en cours...")
            suggestions = ai_generate_names(count, cfg)
            if suggestions:
                for name, _ in suggestions:
                    generator.existing_names.add(name)
                generator._save_generated_names()
                print()
                ui_results(suggestions, "IA")
                ui_footer(len(suggestions), "IA", GENERATED_NAMES_FILE)
                post_generation(suggestions)

        elif choice == "3":
            print()
            configure_ai()
            cfg = load_config()
            input(f"\n  {UI.GREY}Entrée pour revenir au menu...{UI.RESET}")

        elif choice == "4":
            print()
            ui_info("Test de la connexion IA en cours...")
            ok, message = test_api(cfg)
            if ok:
                print()
                print(box([f"{UI.GREEN}{message}{UI.RESET}"], title="test API · succès"))
            else:
                print()
                print(box([f"{UI.RED}{message}{UI.RESET}",
                           f"{UI.GREY}Configurez l'IA (option 3) puis retestez.{UI.RESET}"],
                          title="test API · échec"))
            input(f"\n  {UI.GREY}Entrée pour revenir au menu...{UI.RESET}")

        elif choice == "5":
            generator.reset_history()
            print()
            print(box([f"{UI.GREEN}Historique des noms générés effacé.{UI.RESET}"], title="terminé"))
            input(f"\n  {UI.GREY}Entrée pour revenir au menu...{UI.RESET}")

        else:
            ui_error("Choix invalide : tapez 1, 2, 3, 4, 5 ou q.")

# ============================================================
#  Point d'entrée
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="tilegen",
        description="TileGen — Générateur de noms de carreaux céramiques (local ou IA).",
    )
    parser.add_argument("-n", "--count", type=int, default=None,
                        help="Nombre de noms à générer (mode direct, sans menu)")
    parser.add_argument("--ai", action="store_true",
                        help="Générer les noms avec l'IA (clé API requise)")
    parser.add_argument("--configure-ai", action="store_true",
                        help="Configurer le fournisseur, la clé API et le modèle")
    parser.add_argument("--test-ai", action="store_true",
                        help="Tester la connexion à l'API configurée puis quitter")
    parser.add_argument("-e", "--export", metavar="FICHIER",
                        help="Exporter les résultats en CSV (ex. catalogue.csv)")
    parser.add_argument("--reset", action="store_true",
                        help="Effacer l'historique des noms générés puis quitter")
    args = parser.parse_args()

    # ----- actions directes (sans page d'accueil) -----
    if args.configure_ai:
        configure_ai()
        return

    if args.test_ai:
        ui_header("test API")
        ok, message = test_api()
        if ok:
            print(box([f"{UI.GREEN}{message}{UI.RESET}"], title="test API · succès"))
        else:
            print(box([f"{UI.RED}{message}{UI.RESET}"], title="test API · échec"))
            sys.exit(1)
        return

    generator = TileNameGenerator()

    if args.reset:
        generator.reset_history()
        print(f"{UI.GREEN}Historique des noms générés effacé.{UI.RESET}")
        return

    # ----- mode direct : options fournies en ligne de commande -----
    if args.count is not None or args.ai or args.export:
        count = args.count or 20
        if args.ai:
            cfg = load_config()
            ui_header(f"IA · {cfg.get('model', 'à configurer')}")
            ui_info("Génération via l'IA en cours...")
            suggestions = ai_generate_names(count, cfg)
            if suggestions is None:
                sys.exit(1)
            for name, _ in suggestions:
                generator.existing_names.add(name)
            generator._save_generated_names()
            mode = "IA"
        else:
            ui_header("local")
            suggestions = generator.generate_multiple_names(count)
            mode = "local"

        print()
        ui_results(suggestions, mode)
        ui_footer(len(suggestions), mode, GENERATED_NAMES_FILE)
        if args.export:
            export_to_csv(suggestions, args.export)
        return

    # ----- mode interactif : page d'accueil (défaut) -----
    try:
        interactive_session()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{UI.GREY}Session interrompue — à bientôt !{UI.RESET}\n")


if __name__ == "__main__":
    main()
