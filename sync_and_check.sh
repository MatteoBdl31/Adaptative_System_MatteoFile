#!/bin/bash
# Synchronise main avec origin et vérifie que l'application démarre correctement.

set -e
cd "$(dirname "$0")"

echo "=== 1. Branche actuelle ==="
git branch --show-current
echo ""

echo "=== 2. Récupération des dernières modifications (Narek / origin) ==="
git fetch origin
git pull origin main
echo ""

echo "=== 3. Derniers commits sur main ==="
git log --oneline -5
echo ""

echo "=== 4. Vérification de l'application (import Flask + app) ==="
if [ -f .venv/bin/python ]; then
  .venv/bin/python -c "
import sys
sys.path.insert(0, 'adaptive_quiz_system')
from app import app
print('OK: Flask app importée avec succès.')
print('Port configuré dans run.py: 5001')
"
else
  echo "ATTENTION: .venv non trouvé. Lancez: python3 -m venv .venv && .venv/bin/pip install -r adaptive_quiz_system/requirements.txt"
  exit 1
fi
echo ""

echo "=== 5. Pour lancer l'application ==="
echo "  cd adaptive_quiz_system && ../.venv/bin/python run.py"
echo "  Puis ouvrez: http://127.0.0.1:5001/demo"
echo ""
