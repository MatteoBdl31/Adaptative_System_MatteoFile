#!/bin/bash
# Script wrapper pour exécuter l'application avec l'environnement virtuel

# Obtenir le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
RUN_PY="$SCRIPT_DIR/run.py"

# Vérifier si l'environnement virtuel existe
if [ -f "$VENV_PYTHON" ]; then
    echo "Utilisation de l'environnement virtuel: $VENV_PYTHON"
    exec "$VENV_PYTHON" "$RUN_PY" "$@"
else
    echo "Erreur: Environnement virtuel non trouvé à $PROJECT_ROOT/.venv"
    echo "Veuillez créer l'environnement virtuel avec:"
    echo "  cd $PROJECT_ROOT && python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  pip install -r adaptive_quiz_system/requirements.txt"
    exit 1
fi
