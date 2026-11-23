# TileGen — Quick Start (Windows PowerShell)
# Usage : ouvrez un terminal dans le dossier de TileGen puis : .\quickstart.ps1
# Le script est idempotent : il peut être relancé sans risque à tout moment.

$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "  TileGen - Quick Start" -ForegroundColor Yellow
Write-Host "  ======================" -ForegroundColor DarkGray

# ---------------------------------------------------------------
# 1. Verifier la presence de Python (>= 3.8)
# ---------------------------------------------------------------
$pythonCmd = $null
foreach ($candidate in @("python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}
if (-not $pythonCmd) {
    Write-Host ""
    Write-Host "  [X] Python est introuvable sur cet ordinateur." -ForegroundColor Red
    Write-Host "      Installez-le depuis https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "      IMPORTANT : cochez 'Add Python to PATH' pendant l'installation." -ForegroundColor White
    exit 1
}

# Verifier la version (>= 3.8)
& $pythonCmd -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  [X] Python 3.8 ou plus recent est requis." -ForegroundColor Red
    & $pythonCmd --version
    exit 1
}
$version = (& $pythonCmd --version) 2>&1
Write-Host "  [OK] Python trouve : $version" -ForegroundColor Green

# ---------------------------------------------------------------
# 2. Aucune dependance a installer (TileGen n'utilise que la
#    bibliotheque standard de Python). Verifions-le tout de meme :
#    le script ne copie aucun fichier de configuration — TileGen
#    n'en necessite pas (tilegen_config.json est cree
#    automatiquement si vous branchez le mode IA plus tard).
# ---------------------------------------------------------------
Write-Host "  [OK] Aucune dependance externe requise (bibliotheque standard Python)" -ForegroundColor Green

# ---------------------------------------------------------------
# 3. Verifier que TileGen fonctionne : generation d'un nom
# ---------------------------------------------------------------
Write-Host ""
Write-Host "  Verification du demarrage..." -ForegroundColor DarkGray
& $pythonCmd tilegen.py --count 1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  [X] TileGen n'a pas demarre correctement." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------
# 4. Proposer la commande globale 'tilegen' (optionnel, idempotent)
# ---------------------------------------------------------------
Write-Host ""
& $pythonCmd -m pip install -e . --quiet --disable-pip-version-check 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Commande globale 'tilegen' installee (taper 'tilegen' depuis n'importe quel terminal)" -ForegroundColor Green
} else {
    Write-Host "  [!] La commande globale n'a pas pu etre installee (non bloquant)" -ForegroundColor DarkYellow
    Write-Host "      Lancez simplement TileGen avec : python tilegen.py" -ForegroundColor White
}

# ---------------------------------------------------------------
# Resume
# ---------------------------------------------------------------
Write-Host ""
Write-Host "  ============================== DEMARRAGE ==============================" -ForegroundColor Yellow
Write-Host ""
Write-Host "    Tout est pret ! Lancez TileGen avec :" -ForegroundColor White
Write-Host ""
Write-Host "      python tilegen.py        (ou simplement :  tilegen)" -ForegroundColor Cyan
Write-Host ""
Write-Host "    Console : tapez un nombre pour generer, '/' pour les commandes." -ForegroundColor Gray
Write-Host "    Direct  : python tilegen.py --count 10 --export catalogue.csv" -ForegroundColor Gray
Write-Host ""
