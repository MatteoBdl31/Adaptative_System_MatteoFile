#!/usr/bin/env python3
"""
Run script for the adaptive quiz system.
Automatically uses the virtual environment if available.
"""
import sys
import os
from pathlib import Path

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
VENV_DIR = PROJECT_ROOT / ".venv"
# Windows uses Scripts/python.exe, Unix uses bin/python
if os.name == 'nt':  # Windows
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:  # Unix/Linux/Mac
    VENV_PYTHON = VENV_DIR / "bin" / "python"

# Si l'environnement virtuel existe et qu'on n'utilise pas déjà son Python, se réexécuter avec
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    # Réexécuter avec le Python du venv
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# Add the parent directory to Python path so imports work correctly
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Try to import Flask and show helpful error if not available
try:
    from app import app
except ModuleNotFoundError as e:
    if "flask" in str(e).lower() or "flask" in str(e):
        print("=" * 60)
        print("ERREUR: Flask n'est pas installé dans l'environnement virtuel.")
        print("=" * 60)
        print(f"\nVous utilisez: {sys.executable}")
        if not VENV_PYTHON.exists():
            print(f"\nEnvironnement virtuel non trouvé à: {VENV_DIR}")
            print("\nPour créer et configurer l'environnement virtuel:")
            print(f"  cd {PROJECT_ROOT}")
            print(f"  python3 -m venv .venv")
            print(f"  source .venv/bin/activate")
            print(f"  pip install -r requirements.txt")
            print(f"  pip install -r adaptive_quiz_system/requirements.txt")
        else:
            print(f"\nEnvironnement virtuel trouvé: {VENV_PYTHON}")
            print("\nPour installer les dépendances:")
            print(f"  {VENV_PYTHON} -m pip install -r {PROJECT_ROOT}/requirements.txt")
            print(f"  {VENV_PYTHON} -m pip install -r {SCRIPT_DIR}/requirements.txt")
        print("=" * 60)
        sys.exit(1)
    else:
        raise

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5001)
