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
import textwrap
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

GENERATED_NAMES_FILE = Path(__file__).parent / "noms_generes.json"
CONFIG_FILE = Path(__file__).parent / "tilegen_config.json"
MAX_ATTEMPTS = 1000
VERSION = "3.2"

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


# Logo ASCII (police ANSI Shadow) — construit lettre par lettre pour
# garantir l'alignement vertical de chaque lettre (le I doit avoir son
# corps ET son pied sur toutes les lignes, sinon on lit "TLLEGEN").
_LOGO_LETTERS = {
    "T": ["████████╗", "╚══██╔╝  ", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚═════╝ "],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚═════╝ "],
    "G": [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "N": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
}
LOGO = [" ".join(parts) for parts in zip(*(_LOGO_LETTERS[c] for c in "TILEGEN"))]


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
    """Splash screen façon OpenCode : logo pixel, ligne d'accent, invite."""
    clear_screen()
    print()

    # ----- logo pixel "tilegen" (gris "tile" + blanc "gen", comme opencode) -----
    logo = build_pixel_logo()
    logo_width = max(_visible_len(l) for l in logo)
    pad = max((logo_width + 8 - logo_width) // 2, 0)
    for line in logo:
        print(" " * pad + line)
    print()

    # ----- ligne d'accent orange (comme "/update to install v2.3.2") -----
    hint = (f"{UI.ACCENT}{UI.BOLD}/help{UI.RESET}{UI.GREY} pour les commandes{UI.RESET}"
            f"{UI.GREY}  ·  v{VERSION}{UI.RESET}")
    print(" " * max((logo_width + 8 - _visible_len(hint)) // 2, 0) + hint)
    print()
    print()

    # ----- boîte d'invite avec barre d'accent à gauche -----
    bar = f"{UI.ACCENT}▌{UI.RESET}"
    print(f"  {bar}   {UI.GREY}Générez des noms... « 10 », {UI.RESET}{UI.TEXT}/model{UI.RESET}"
          f"{UI.GREY}, {UI.RESET}{UI.TEXT}/help{UI.RESET}{UI.GREY} — Tab pour compléter{UI.RESET}")
    print(f"  {bar}   {UI.TEXT}Local{UI.RESET}{UI.GREY} · mode sans clé · "
          f"{UI.RESET}{UI.TEXT}/model{UI.RESET}{UI.GREY} pour l'IA{UI.RESET}")
    print()

    # ----- raccourcis en bas à droite (comme "shift+tab agents  ctrl+p commands") -----
    shortcuts = (f"{UI.TEXT}{UI.BOLD}/help{UI.RESET}{UI.GREY} commandes{UI.RESET}   "
                 f"{UI.TEXT}{UI.BOLD}/model{UI.RESET}{UI.GREY} IA{UI.RESET}   "
                 f"{UI.TEXT}{UI.BOLD}/exit{UI.RESET}{UI.GREY} quitter{UI.RESET}")
    print(" " * max(72 - _visible_len(shortcuts), 0) + shortcuts)
    print()


# ----- police pixel 3x5 pour le splash (comme le logo d'OpenCode) -----
_PIXEL_LETTERS = {
    "t": ["###", ".#.", ".#.", ".#.", ".##"],
    "i": [".#.", "...", ".#.", ".#.", ".#."],
    "l": ["#..", "#..", "#..", "#..", "###"],
    "e": ["###", "#..", "###", "#..", "###"],
    "g": ["###", "#..", "#.#", "#.#", "###"],
    "n": ["#.#", "###", "#.#", "#.#", "#.#"],
}


def _pixel_rows(word):
    """Assemble les 5 lignes de pixels d'un mot (1 colonne vide entre lettres)."""
    rows = [""] * 5
    for c in word:
        for r in range(5):
            rows[r] += _PIXEL_LETTERS[c][r] + "."
    return [row[:-1] for row in rows]  # retire la séparation finale


def build_pixel_logo():
    """Construit le logo 'tilegen' : 'tile' en gris, 'gen' en blanc (façon opencode)."""
    tile = _pixel_rows("tile")
    gen = _pixel_rows("gen")
    lines = []
    for r in range(5):
        left = (UI.GREY + UI.BOLD + tile[r].replace("#", "██").replace(".", "  ") + UI.RESET)
        right = (UI.TEXT + UI.BOLD + gen[r].replace("#", "██").replace(".", "  ") + UI.RESET)
        lines.append(left + "  " + right)
    return lines


def ia_status_line():
    """Ligne d'état IA façon OpenCode (fournisseur · modèle · clé)."""
    cfg = load_config()
    if not cfg.get("model"):
        return f"{UI.GREY}ia : non configurée  ({UI.RESET}{UI.TEXT}/model{UI.RESET}{UI.GREY} pour démarrer){UI.RESET}"
    key_ok = "clé ok" if (os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")) else "clé manquante"
    return (f"{UI.GREY}ia : {UI.RESET}{UI.TEXT}{cfg.get('model')}{UI.RESET}"
            f"{UI.GREY} · {key_ok}  ({UI.RESET}{UI.TEXT}/model{UI.RESET}{UI.GREY} pour changer){UI.RESET}")


HELP_ITEMS = [
    ("/model", "choisir le fournisseur et le modèle d'IA"),
    ("/key", "saisir ou changer la clé API"),
    ("/test", "tester la connexion à l'API"),
    ("/gen [n]", "générer n noms en local (aucune clé requise)"),
    ("/ai [n]", "générer n noms avec l'IA"),
    ("/export", "exporter les derniers résultats en CSV"),
    ("/reset", "effacer l'historique des noms générés"),
    ("/clear", "nettoyer l'écran"),
    ("/help", "afficher cette aide"),
    ("/exit", "quitter TileGen"),
]


def show_help():
    lines = []
    for cmd, desc in HELP_ITEMS:
        lines.append(f"  {UI.ACCENT}{UI.BOLD}{cmd:<10}{UI.RESET} {UI.GREY}{desc}{UI.RESET}")
    print(box(lines, title="commandes"))


# Noms de commandes simples (sans "[n]") pour l'autocomplétion
COMMAND_BASES = [cmd.split()[0] for cmd, _ in HELP_ITEMS]
COMMAND_DESCRIPTIONS = {cmd.split()[0]: desc for cmd, desc in HELP_ITEMS}
_COMMANDS_WITH_ARG = {"/gen", "/ai"}


def _popup_suggestions(matches):
    """Liste de suggestions façon OpenCode (au-dessus de l'invite)."""
    for cmd, desc in HELP_ITEMS:
        base = cmd.split()[0]
        if base in matches:
            print(f"  {UI.ACCENT}{UI.BOLD}{base:<9}{UI.RESET} {UI.GREY}{desc}{UI.RESET}")


_PROMPT = f"  {UI.ACCENT}❯{UI.RESET} "
_PROMPT_VISIBLE_LEN = 4  # «  » + « ❯ » + « »


def _matches_for(buffer):
    """Commandes correspondant à ce qui est tapé (popup en direct)."""
    token = buffer.strip().lower()
    if not token.startswith("/") or " " in token:
        return []
    return [c for c in COMMAND_BASES if c.startswith(token)]


def _redraw_line(buffer, matches, prev_popup):
    """Réaffiche l'invite + le buffer + le popup live sous la ligne (façon OpenCode).

    Le curseur est replacé sur la ligne d'invite après le popup. Renvoie le
    nombre de lignes de popup affichées (pour l'effacement suivant).
    """
    count = max(len(matches), prev_popup)
    sys.stdout.write("\x1b[2K\r" + _PROMPT + buffer)
    for i in range(count):
        sys.stdout.write("\n\x1b[2K")
        if i < len(matches):
            base = matches[i]
            sys.stdout.write(f"  {UI.ACCENT}{UI.BOLD}{base:<9}{UI.RESET} "
                             f"{UI.GREY}{COMMAND_DESCRIPTIONS[base]}{UI.RESET}")
    if count:
        sys.stdout.write(f"\x1b[{count}A")       # remonter sur la ligne d'invite
    sys.stdout.write(f"\r\x1b[{_PROMPT_VISIBLE_LEN + len(buffer)}C")
    sys.stdout.flush()
    return len(matches)


def _read_line_tab():
    """Lecture clavier temps réel (Windows) avec popup live dès que « / » est tapé.

    Tapez « / » : les commandes s'affichent immédiatement et se filtrent
    pendant la frappe. Tab complète un nom unique ; Entrée valide.
    """
    import msvcrt
    sys.stdout.write(_PROMPT)
    sys.stdout.flush()
    buffer = ""
    popup = 0                                    # lignes de popup actuellement affichées
    while True:
        ch = msvcrt.getwch()
        if ch in ("\r", "\n"):                   # Entrée : valider
            sys.stdout.write("\n\x1b[2K" * popup)
            sys.stdout.write("\n")
            sys.stdout.flush()
            return buffer.strip()
        if ch in ("\x00", "\xe0"):               # flèches / touches spéciales
            msvcrt.getwch()
            continue
        if ch == "\x03":                         # Ctrl+C
            raise KeyboardInterrupt
        if ch == "\x08":                         # Retour arrière
            if buffer:
                buffer = buffer[:-1]
            popup = _redraw_line(buffer, _matches_for(buffer), popup)
            continue
        if ch == "\t":                           # Tab : complète un nom unique
            matches = _matches_for(buffer)
            if len(matches) == 1:
                buffer = matches[0] + (" " if matches[0] in _COMMANDS_WITH_ARG else "")
            elif len(matches) > 1:
                # préfixe commun le plus long entre les correspondances
                prefix = matches[0]
                for m in matches[1:]:
                    while not m.startswith(prefix):
                        prefix = prefix[:-1]
                buffer = prefix
            popup = _redraw_line(buffer, _matches_for(buffer), popup)
            continue
        if ch.isprintable():                     # caractère normal → popup live
            buffer += ch
            popup = _redraw_line(buffer, _matches_for(buffer), popup)


def command_prompt():
    """Invite façon OpenCode : barre d'accent + statut IA + autocomplétion Tab."""
    print()
    print(f"  {UI.ACCENT}▌{UI.RESET}   {ia_status_line()}")
    if sys.stdin.isatty() and os.name == "nt":
        try:
            return _read_line_tab()
        except ImportError:
            pass
    return input(f"  {UI.ACCENT}❯{UI.RESET} ").strip()


def ask(prompt, default=""):
    """Entrée utilisateur avec valeur par défaut."""
    suffix = f" {UI.GREY}[{default}]{UI.RESET}" if default != "" else ""
    value = input(f"  {UI.ACCENT}❯{UI.RESET} {prompt}{suffix} : ").strip()
    return value or default


def ask_secret(prompt):
    """Saisie masquée si l'entrée est un vrai terminal, saisie normale sinon.

    getpass peut bloquer indéfiniment lorsque stdin n'est pas un TTY
    (entrée canalisée, lanceur automatisé) : on détecte ce cas et on
    retombe sur input() pour éviter tout blocage.
    """
    if sys.stdin is not None and sys.stdin.isatty():
        return getpass.getpass(prompt)
    # Fallback : saisie visible (mais sans écho du prompt en double)
    return input(prompt)


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


def show_test_result(ok, message):
    """Affiche le résultat d'un test API (succès ou échec + indice) dans une boîte."""
    color = UI.GREEN if ok else UI.RED
    lines = []
    for part in message.split("\n"):
        lines.extend(f"{color}{seg}{UI.RESET}" for seg in wrap_text(part, 68))
    print(box(lines, title="test API · succès" if ok else "test API · échec"))


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
# Fournisseurs compatibles OpenAI : base_url + modèles proposés par /model
AI_PROVIDERS = {
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        "key_url": "https://platform.openai.com/api-keys",
    },
    "Google AI Studio (Gemini)": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.8-flash"],
        "key_url": "https://aistudio.google.com/apikey",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_url": "https://platform.deepseek.com",
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "key_url": "https://console.groq.com/keys",
    },
    "Mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "models": ["mistral-small-latest", "mistral-medium-latest"],
        "key_url": "https://console.mistral.ai/api-keys",
    },
    "Autre / personnalisé": {
        "base_url": "",
        "models": [],
        "key_url": "",
    },
}


# Modèles à écarter de la liste "autorités" : non conversationnels
_NON_CHAT_HINTS = ("embedding", "aio", "imagen", "veo", "tts", "whisper", "moderation", "dprim")


def fetch_models(api_key, base_url):
    """Interroge GET {base_url}/models : liste des modèles autorisés par la clé.

    Endpoint standard du protocole OpenAI, supporté par Google AI Studio,
    OpenAI, DeepSeek, Groq, Mistral... Les modèles non conversationnels
    (embeddings, images, audio) sont écartés de la liste.
    """
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ids = [str(m.get("id", "")).strip() for m in data.get("data", []) if m.get("id")]
        # Google renvoie des id du type "models/gemini-..." : on nettoie le préfixe
        ids = [m.replace("models/", "") for m in ids]
        chat = sorted(m for m in ids if not any(h in m.lower() for h in _NON_CHAT_HINTS))
        return chat, None
    except urllib.error.HTTPError as e:
        detail = " ".join(e.read().decode("utf-8", errors="replace").split())[:120]
        return None, f"Erreur {e.code} : {detail}\n{_api_error_hint(e.code, detail)}"
    except TimeoutError:
        return None, "Délai dépassé (30 s) : le serveur n'a pas répondu."
    except urllib.error.URLError as e:
        return None, f"Impossible de joindre {url} : {e.reason}"
    except (KeyError, json.JSONDecodeError) as e:
        return None, f"Réponse illisible : {e}"


def pick_from_box(items, title, format_item):
    """Affiche une liste sélectionnable par numéro (popup façon OpenCode)."""
    lines = [format_item(i + 1, item) for i, item in enumerate(items)]
    print(box(lines, title=title))
    choice = input(f"  {UI.ACCENT}❯{UI.RESET} numéro : ").strip()
    try:
        return items[int(choice) - 1]
    except (ValueError, IndexError):
        return None


def select_model():
    """Commande /model : choix du fournisseur puis du modèle, étape par étape."""
    cfg = load_config()
    current_model = cfg.get("model", "")
    current_provider = cfg.get("provider", "")

    # ----- étape 1 : fournisseur -----
    providers = list(AI_PROVIDERS.keys())
    def fmt_provider(i, name):
        marker = f"{UI.GREEN}●{UI.RESET} " if name == current_provider else "  "
        models = AI_PROVIDERS[name]["models"]
        hint = f"{UI.GREY}{models[0]} (+{len(models) - 1}){UI.RESET}" if models else ""
        return f"{marker}{UI.ACCENT}{UI.BOLD}{i}{UI.RESET}. {UI.TEXT}{name:<28}{UI.RESET}{hint}"
    print(box([f"{UI.TEXT}Étape 1/2 — choisissez le fournisseur{UI.RESET}"], title="/model"))
    provider = pick_from_box(providers, "fournisseurs", fmt_provider)
    if provider is None:
        ui_error("Choix invalide : /model annulé.")
        return False

    info = AI_PROVIDERS[provider]
    cfg["provider"] = provider
    print()

    # ----- étape 2 : modèle -----
    LIST_MODELS = "📋 Lister les modèles autorisés par ma clé (API)"
    OTHER_MODEL = "Autre modèle (à taper)"

    def fmt_model(i, model):
        marker = f"{UI.GREEN}●{UI.RESET} " if model == current_model else "  "
        return f"{marker}{UI.ACCENT}{UI.BOLD}{i}{UI.RESET}. {UI.TEXT}{model}{UI.RESET}"

    print(box([f"{UI.TEXT}Étape 2/2 — choisissez le modèle{UI.RESET}"], title=provider))
    choices = (info["models"] + [LIST_MODELS, OTHER_MODEL]) if info["models"] else [LIST_MODELS]
    model = pick_from_box(choices, "modèles", fmt_model)
    if model is None:
        ui_error("Choix invalide : /model annulé.")
        return False

    if model == LIST_MODELS:
        # Clé requise pour interroger le compte (demandée si absente)
        api_key = os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")
        if not api_key:
            print()
            if info["key_url"]:
                ui_info(f"Clé sur {UI.RESET}{UI.TEXT}{info['key_url']}{UI.RESET}")
            api_key = ask_secret(f"  {UI.ACCENT}❯{UI.RESET} Clé API {UI.GREY}(entrée masquée){UI.RESET} : ")
            api_key = api_key.strip().strip('"').strip("'").strip()
            if not api_key:
                ui_error("Clé manquante : /model annulé.")
                return False
            cfg["api_key"] = api_key
            print()

        probe_url = (info["base_url"] or cfg.get("base_url") or "").rstrip("/")
        if not probe_url:
            probe_url = ask("Base URL")

        ui_info("Interrogation de votre compte...")
        models, error = fetch_models(api_key, probe_url)
        if error:
            lines = []
            for j, part in enumerate(error.splitlines()):
                color = UI.RED if j == 0 else UI.GREY
                lines.extend(color + l + UI.RESET
                             for l in textwrap.fill(part, width=72).splitlines())
            print()
            print(box(lines, title="liste des modèles · échec"))
            return False
        if not models:
            ui_error("Votre compte n'a renvoyé aucun modèle conversationnel.")
            return False

        # Affiche au plus 20 modèles ; le reste accessible via "Autre modèle"
        display = models[:20]
        if len(models) > 20:
            ui_info(f"{len(models)} modèles autorisés — 20 affichés, les autres via « Autre modèle »")
        picked = pick_from_box(display + [OTHER_MODEL], f"{len(models)} modèles autorisés", fmt_model)
        if picked is None:
            ui_error("Choix invalide : /model annulé.")
            return False
        if picked == OTHER_MODEL:
            picked = ask("Nom exact du modèle")
            if not picked:
                ui_error("Modèle vide : /model annulé.")
                return False
        model = picked

    elif model == OTHER_MODEL:
        model = ask("Nom exact du modèle")
        if not model:
            ui_error("Modèle vide : /model annulé.")
            return False

    cfg["model"] = model
    print()

    # ----- base URL (pré-remplie, modifiable) -----
    default_url = info["base_url"] or cfg.get("base_url", "https://api.openai.com/v1")
    cfg["base_url"] = ask("Base URL", default_url or "https://api.openai.com/v1")

    # ----- clé API : demandée seulement si absente -----
    if not (os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")):
        print()
        if info["key_url"]:
            ui_info(f"Clé sur {UI.RESET}{UI.TEXT}{info['key_url']}{UI.RESET}")
        raw_key = ask_secret(f"  {UI.ACCENT}❯{UI.RESET} Clé API {UI.GREY}(entrée masquée){UI.RESET} : ")
        cfg["api_key"] = raw_key.strip().strip('"').strip("'").strip()
        if not cfg["api_key"]:
            ui_error("Clé manquante : utilisez /key plus tard.")
    elif cfg.get("provider") != provider:
        ui_info("Clé API conservée — si elle vient d'un autre fournisseur, changez-la avec /key.")

    save_config(cfg)
    print()
    print(box([
        f"{UI.GREEN}Modèle actif : {cfg['model']}{UI.RESET}",
        f"{UI.GREY}{cfg['base_url']}{UI.RESET}",
        f"{UI.GREY}Testez avec {UI.RESET}{UI.TEXT}/test{UI.RESET}{UI.GREY} · générez avec {UI.RESET}{UI.TEXT}/ai 10{UI.RESET}",
    ], title="terminé"))
    return True


def set_api_key():
    """Commande /key : saisie ou remplacement de la clé API."""
    cfg = load_config()
    provider = cfg.get("provider", "")
    key_url = AI_PROVIDERS.get(provider, {}).get("key_url", "")
    if key_url:
        ui_info(f"Clé {provider or 'du fournisseur'} sur {UI.RESET}{UI.TEXT}{key_url}{UI.RESET}")
    raw_key = ask_secret(f"  {UI.ACCENT}❯{UI.RESET} Clé API {UI.GREY}(entrée masquée){UI.RESET} : ")
    cfg["api_key"] = raw_key.strip().strip('"').strip("'").strip()
    if not cfg["api_key"]:
        ui_error("Clé vide : rien n'a changé.")
        return False
    save_config(cfg)
    print()
    print(box([f"{UI.GREEN}Clé API enregistrée dans {CONFIG_FILE.name}.{UI.RESET}",
               f"{UI.GREY}Testez avec {UI.RESET}{UI.TEXT}/test{UI.RESET}"], title="terminé"))
    return True


def configure_ai():
    """Compatibilité --configure-ai : délègue au sélecteur /model."""
    return select_model()


def _api_error_hint(code, detail):
    """Indice de diagnostic selon le type d'erreur API."""
    detail_lower = detail.lower()
    if "invalid" in detail_lower and ("key" in detail_lower or "auth" in detail_lower):
        return ("La clé est refusée par le service. Recréez-en une neuve sur le site du "
                "fournisseur et copiez-la ENTIÈRE (souvent très longue, sans espaces ni guillemets).")
    if code == 401:
        return "Clé incorrecte ou expirée. Recréez une clé sur le site du fournisseur."
    if code == 404:
        return "Base URL ou nom de modèle incorrect. Vérifiez-les dans /model."
    if code == 429:
        return "Quota dépassé ou trop de requêtes. Attendez un peu ou vérifiez votre offre."
    if code == 503 or "high demand" in detail_lower or "overload" in detail_lower:
        return ("Le modèle est surchargé en ce moment : ce n'est NI votre clé NI votre "
                "configuration. Réessayez dans quelques minutes, ou choisissez un autre "
                "modèle avec /model (ex. gemini-flash-lite-latest).")
    if code == 400:
        return "Requête refusée : vérifiez le nom du modèle et la clé dans /model."
    return "Vérifiez la clé, la base URL et le modèle dans /model."


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
        return False, f"Erreur {e.code} : {detail}\n{_api_error_hint(e.code, detail)}"
    except urllib.error.URLError as e:
        return False, f"Impossible de joindre {base_url} : {e.reason}"
    except TimeoutError:
        return False, ("Délai dépassé (30 s) : le serveur n'a pas répondu. "
                       "Vérifiez votre connexion internet ou réessayez plus tard "
                       "(le modèle est peut-être surchargé).")
    except OSError as e:
        return False, f"Problème réseau : {e}"
    except (KeyError, json.JSONDecodeError) as e:
        return False, f"Réponse inattendue de l'API : {e}"


def ai_generate_names(count, cfg):
    """Génère des noms via l'API (format OpenAI /chat/completions)."""
    api_key = os.environ.get("TILEGEN_API_KEY") or cfg.get("api_key")
    base_url = (cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("model") or "gpt-4o-mini"

    if not api_key:
        ui_error("Aucune clé API configurée. Tapez /model pour démarrer.")
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
        hint = _api_error_hint(e.code, detail)
        message = textwrap.fill(f"Erreur API {e.code} : {detail}", width=72)
        lines = [UI.RED + l + UI.RESET for l in message.splitlines()]
        if hint:
            lines.append("")
            lines.extend(UI.GREY + l + UI.RESET for l in textwrap.fill(hint, width=72).splitlines())
        print(box(lines, title="erreur IA"))
        return None
    except TimeoutError:
        print(box([
            f"{UI.RED}Délai dépassé (60 s) : le serveur n'a pas répondu.{UI.RESET}",
            "",
            f"{UI.GREY}Le modèle ({model}) est peut-être surchargé en ce moment.{UI.RESET}",
            f"{UI.GREY}Réessayez, ou choisissez un autre modèle avec /model.{UI.RESET}",
        ], title="erreur IA"))
        return None
    except OSError as e:
        ui_error(f"Problème réseau : {e}")
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
#  Session interactive — console de commandes façon OpenCode
# ============================================================

def interactive_session():
    home_screen()
    generator = TileNameGenerator()
    last_suggestions = None

    while True:
        raw = command_prompt()

        if raw == "":
            continue

        # « / » seul : popup des commandes disponibles (façon OpenCode)
        if raw == "/":
            print()
            _popup_suggestions(COMMAND_BASES)
            continue

        # Un simple nombre = /gen n (raccourci le plus utilisé)
        if raw.isdigit():
            raw = f"/gen {raw}"

        parts = raw.split()
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        cfg = load_config()

        # ----- /exit, /quit -----
        if cmd in ("/exit", "/quit", "/q"):
            print(f"\n{UI.GREY}À bientôt — TileGen v{VERSION}{UI.RESET}\n")
            break

        # ----- /help -----
        elif cmd in ("/help", "/?"):
            show_help()

        # ----- /model -----
        elif cmd == "/model":
            print()
            select_model()

        # ----- /key -----
        elif cmd == "/key":
            print()
            set_api_key()

        # ----- /test -----
        elif cmd == "/test":
            print()
            ui_info("Test de la connexion IA en cours...")
            ok, message = test_api(cfg)
            print()
            show_test_result(ok, message)

        # ----- /gen [n] -----
        elif cmd == "/gen":
            try:
                count = int(arg) if arg else 20
                if not 1 <= count <= 100:
                    raise ValueError
            except ValueError:
                ui_error("Usage : /gen [nombre entre 1 et 100]  — ex. /gen 10")
                continue
            print()
            try:
                suggestions = generator.generate_multiple_names(count)
            except RuntimeError as e:
                ui_error(str(e))
                continue
            print()
            ui_results(suggestions, "local")
            ui_footer(len(suggestions), "local", GENERATED_NAMES_FILE)
            last_suggestions = suggestions

        # ----- /ai [n] -----
        elif cmd == "/ai":
            try:
                count = int(arg) if arg else 20
                if not 1 <= count <= 100:
                    raise ValueError
            except ValueError:
                ui_error("Usage : /ai [nombre entre 1 et 100]  — ex. /ai 10")
                continue
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
                last_suggestions = suggestions

        # ----- /export -----
        elif cmd == "/export":
            if not last_suggestions:
                ui_error("Rien à exporter : générez d'abord des noms avec /gen ou /ai.")
            else:
                print()
                filepath = ask("Nom du fichier", "catalogue.csv")
                export_to_csv(last_suggestions, filepath)

        # ----- /reset -----
        elif cmd == "/reset":
            generator.reset_history()
            print()
            print(box([f"{UI.GREEN}Historique des noms générés effacé.{UI.RESET}"], title="terminé"))

        # ----- /clear -----
        elif cmd == "/clear":
            home_screen()

        # ----- commande inconnue -----
        else:
            lines = [f"{UI.RED}Commande inconnue : {cmd}{UI.RESET}"]
            # Suggestions : commandes commençant par ce qui a été tapé
            close = [c for c in COMMAND_BASES if c.startswith(cmd)]
            if close:
                lines.append("")
                lines.append(f"{UI.GREY}Vouliez-vous dire :{UI.RESET}")
                lines.extend(f"  {UI.ACCENT}{UI.BOLD}{c:<9}{UI.RESET}"
                             f"{UI.GREY}{COMMAND_DESCRIPTIONS[c]}{UI.RESET}"
                             for c in close)
            else:
                lines.append(f"{UI.GREY}Tapez {UI.RESET}{UI.TEXT}/help{UI.RESET}"
                             f"{UI.GREY} pour la liste des commandes.{UI.RESET}")
            print(box(lines, title="erreur"))

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
        show_test_result(ok, message)
        if not ok:
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
