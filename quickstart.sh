#!/usr/bin/env bash
# TileGen — Quick Start (Linux / macOS / Git Bash)
# Usage : ./quickstart.sh
# Le script est idempotent : il peut être relancé sans risque à tout moment.

set -e

echo ""
echo "  TileGen — Quick Start"
echo "  ====================="

# ---------------------------------------------------------------
# 1. Vérifier la présence de Python (>= 3.8)
# ---------------------------------------------------------------
PYTHON_CMD=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_CMD="$candidate"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "  [X] Python est introuvable sur cet ordinateur." >&2
    echo "      Installez-le avec votre gestionnaire de paquets :" >&2
    echo "        Debian/Ubuntu : sudo apt install python3" >&2
    echo "        macOS         : brew install python3" >&2
    exit 1
fi

"$PYTHON_CMD" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
    echo ""
    echo "  [X] Python 3.8 ou plus récent est requis." >&2
    "$PYTHON_CMD" --version >&2
    exit 1
}
echo "  [OK] Python trouvé : $("$PYTHON_CMD" --version 2>&1)"

# ---------------------------------------------------------------
# 2. Aucune dépendance à installer : TileGen n'utilise que la
#    bibliothèque standard de Python. Aucun fichier de
#    configuration à copier non plus — tilegen_config.json est
#    créé automatiquement si vous branchez le mode IA plus tard.
# ---------------------------------------------------------------
echo "  [OK] Aucune dépendance externe requise (bibliothèque standard Python)"

# ---------------------------------------------------------------
# 3. Vérifier que TileGen fonctionne : génération d'un nom
# ---------------------------------------------------------------
echo ""
echo "  Vérification du démarrage..."
"$PYTHON_CMD" tilegen.py --count 1

# ---------------------------------------------------------------
# 4. Proposer la commande globale 'tilegen' (optionnel, idempotent)
# ---------------------------------------------------------------
echo ""
if "$PYTHON_CMD" -m pip install -e . --quiet --disable-pip-version-check >/dev/null 2>&1; then
    echo "  [OK] Commande globale 'tilegen' installée (taper 'tilegen' depuis n'importe quel terminal)"
else
    echo "  [!] La commande globale n'a pas pu être installée (non bloquant)"
    echo "      Lancez simplement TileGen avec : $PYTHON_CMD tilegen.py"
fi

# ---------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------
echo ""
echo "  ============================== DÉMARRAGE =============================="
echo ""
echo "    Tout est prêt ! Lancez TileGen avec :"
echo ""
echo "      $PYTHON_CMD tilegen.py        (ou simplement :  tilegen)"
echo ""
echo "    Console : tapez un nombre pour générer, '/' pour les commandes."
echo "    Direct  : $PYTHON_CMD tilegen.py --count 10 --export catalogue.csv"
echo ""
