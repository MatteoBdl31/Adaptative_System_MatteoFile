#!/usr/bin/env python3
"""
Script d'analyse robuste pour le LOT 7
- Détecte les règles CSS mortes (non utilisées)
- Analyse la spécificité excessive
- Identifie les duplications
"""

import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent
CSS_FILE = PROJECT_ROOT / "adaptive_quiz_system/static/style.css"
TEMPLATES_DIR = PROJECT_ROOT / "adaptive_quiz_system/templates"
STATIC_DIR = PROJECT_ROOT / "adaptive_quiz_system/static"
BACKEND_DIR = PROJECT_ROOT / "adaptive_quiz_system"

# Classes Leaflet à ne jamais considérer comme mortes
LEAFLET_CLASSES = {
    'leaflet-container', 'leaflet-map-pane', 'leaflet-tile-pane', 
    'leaflet-tile', 'leaflet-popup-content-wrapper', 'leaflet-popup-content',
    'leaflet-control', 'leaflet-control-zoom', 'leaflet-control-layers'
}

# Classes générées dynamiquement par JS (à vérifier manuellement)
DYNAMIC_CLASSES = {
    'active', 'hidden', 'loading', 'disabled', 'selected', 'open', 'closed'
}

def extract_css_selectors(css_content: str) -> Tuple[Set[str], Set[str], Dict[str, int]]:
    """Extrait tous les sélecteurs CSS du fichier"""
    classes = set()
    ids = set()
    specificity_map = {}  # classe -> spécificité estimée
    
    # Pattern pour les classes (plus robuste)
    class_pattern = r'\.([a-zA-Z0-9_-]+)(?::[a-zA-Z0-9_-]+)?(?:\s|,|{|\.|#)'
    
    # Pattern pour les IDs
    id_pattern = r'#([a-zA-Z0-9_-]+)'
    
    # Extraire les classes
    for match in re.finditer(class_pattern, css_content):
        class_name = match.group(1)
        # Ignorer les pseudo-classes communes
        if class_name not in ['hover', 'focus', 'active', 'before', 'after', 
                              'first', 'last', 'nth', 'not', 'is', 'where']:
            classes.add(class_name)
    
    # Extraire les IDs
    for match in re.finditer(id_pattern, css_content):
        ids.add(match.group(1))
    
    # Calculer la spécificité (simplifié: compter les sélecteurs dans la chaîne)
    lines = css_content.split('\n')
    current_selector = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('/*') or line.startswith('*'):
            continue
        
        # Détecter un sélecteur (ligne qui se termine par {)
        if '{' in line and not line.startswith('@'):
            selector = line.split('{')[0].strip()
            # Compter la spécificité (nombre de classes/IDs dans le sélecteur)
            specificity = (
                len(re.findall(r'#\w+', selector)) * 100 +  # IDs
                len(re.findall(r'\.\w+', selector)) * 10 +  # Classes
                len(re.findall(r'\w+(?=\s|$)', selector))   # Éléments
            )
            
            # Extraire les classes du sélecteur
            for class_match in re.finditer(r'\.([a-zA-Z0-9_-]+)', selector):
                class_name = class_match.group(1)
                if class_name not in specificity_map or specificity_map[class_name] < specificity:
                    specificity_map[class_name] = specificity
    
    return classes, ids, specificity_map

def search_in_files(selectors: Set[str], file_paths: List[Path], file_type: str = "html") -> Dict[str, List[str]]:
    """Recherche l'usage des sélecteurs dans les fichiers"""
    usage_map = defaultdict(list)
    
    for file_path in file_paths:
        if not file_path.exists():
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for selector in selectors:
                # Recherche robuste
                patterns = [
                    f'class="{selector}"',  # class="selector"
                    f'class=\'{selector}\'',  # class='selector'
                    f'class="[^"]*\\b{selector}\\b',  # dans une liste de classes
                    f'class=\'[^\']*\\b{selector}\\b',  # dans une liste de classes
                    f'getElementById\\(["\']{selector}["\']\\)',  # JS: getElementById
                    f'querySelector\\(["\'][^"\']*{selector}',  # JS: querySelector
                    f'querySelectorAll\\(["\'][^"\']*{selector}',  # JS: querySelectorAll
                    f'\\.{selector}\\b',  # JS: .selector
                    f'#{selector}\\b',  # JS: #selector
                    f'classList\\.(add|remove|toggle|contains)\\(["\']{selector}["\']\\)',  # JS: classList
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        usage_map[selector].append(str(file_path))
                        break
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
    
    return usage_map

def find_duplicate_rules(css_content: str) -> List[Tuple[str, List[str]]]:
    """Trouve les règles CSS dupliquées (strictement identiques)"""
    # Extraire toutes les règles CSS
    rule_pattern = r'([^{]+)\{([^}]+)\}'
    rules = {}
    duplicates = []
    
    for match in re.finditer(rule_pattern, css_content, re.MULTILINE | re.DOTALL):
        selector = match.group(1).strip()
        declarations = match.group(2).strip()
        
        # Normaliser (supprimer espaces, commentaires)
        normalized_decls = re.sub(r'/\*.*?\*/', '', declarations, flags=re.DOTALL)
        normalized_decls = re.sub(r'\s+', ' ', normalized_decls).strip()
        
        if normalized_decls:
            key = normalized_decls
            if key in rules:
                if selector not in rules[key]:
                    rules[key].append(selector)
                    duplicates.append((key, rules[key]))
            else:
                rules[key] = [selector]
    
    return duplicates

def analyze_specificity(specificity_map: Dict[str, int]) -> List[Tuple[str, int]]:
    """Identifie les sélecteurs avec spécificité excessive (> 50)"""
    high_specificity = [(cls, spec) for cls, spec in specificity_map.items() if spec > 50]
    return sorted(high_specificity, key=lambda x: x[1], reverse=True)

def main():
    print("=" * 80)
    print("ANALYSE LOT 7 - Détection règles mortes, spécificité, duplications")
    print("=" * 80)
    
    # 1. Lire le CSS
    print("\n1. Lecture du fichier CSS...")
    css_content = CSS_FILE.read_text()
    print(f"   ✓ Fichier CSS lu: {len(css_content)} caractères")
    
    # 2. Extraire les sélecteurs
    print("\n2. Extraction des sélecteurs CSS...")
    classes, ids, specificity_map = extract_css_selectors(css_content)
    print(f"   ✓ Classes trouvées: {len(classes)}")
    print(f"   ✓ IDs trouvés: {len(ids)}")
    
    # 3. Trouver tous les fichiers à analyser
    print("\n3. Recherche des fichiers à analyser...")
    html_files = list(TEMPLATES_DIR.rglob("*.html"))
    js_files = list(STATIC_DIR.rglob("*.js"))
    py_files = list(BACKEND_DIR.rglob("*.py"))
    
    print(f"   ✓ Templates HTML: {len(html_files)}")
    print(f"   ✓ Fichiers JS: {len(js_files)}")
    print(f"   ✓ Fichiers Python: {len(py_files)}")
    
    # 4. Rechercher l'usage des classes
    print("\n4. Recherche de l'usage des classes CSS...")
    all_files = html_files + js_files
    class_usage = search_in_files(classes, all_files, "html")
    
    # 5. Identifier les règles mortes
    print("\n5. Identification des règles mortes...")
    unused_classes = set(classes) - set(class_usage.keys())
    
    # Exclure les classes Leaflet et dynamiques
    unused_classes = unused_classes - LEAFLET_CLASSES
    unused_classes = unused_classes - {c for c in unused_classes if any(dc in c.lower() for dc in DYNAMIC_CLASSES)}
    
    # Exclure les nouvelles classes créées dans les LOTs (c-*, l-*, u-*)
    unused_classes = unused_classes - {c for c in unused_classes if c.startswith(('c-', 'l-', 'u-'))}
    
    print(f"   ✓ Classes utilisées: {len(class_usage)}")
    print(f"   ✓ Classes potentiellement inutilisées: {len(unused_classes)}")
    
    # 6. Analyser la spécificité
    print("\n6. Analyse de la spécificité...")
    high_specificity = analyze_specificity(specificity_map)
    print(f"   ✓ Sélecteurs avec spécificité > 50: {len(high_specificity)}")
    
    # 7. Trouver les duplications
    print("\n7. Recherche des règles dupliquées...")
    duplicates = find_duplicate_rules(css_content)
    print(f"   ✓ Règles dupliquées trouvées: {len(duplicates)}")
    
    # 8. Générer le rapport
    print("\n" + "=" * 80)
    print("RAPPORT D'ANALYSE")
    print("=" * 80)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   - Classes CSS: {len(classes)}")
    print(f"   - IDs CSS: {len(ids)}")
    print(f"   - Classes utilisées: {len(class_usage)}")
    print(f"   - Classes potentiellement inutilisées: {len(unused_classes)}")
    print(f"   - Sélecteurs haute spécificité (>50): {len(high_specificity)}")
    print(f"   - Règles dupliquées: {len(duplicates)}")
    
    if unused_classes:
        print(f"\n⚠️  CLASSES POTENTIELLEMENT INUTILISÉES (premiers 30):")
        for i, cls in enumerate(sorted(list(unused_classes))[:30], 1):
            print(f"   {i:2d}. .{cls}")
        if len(unused_classes) > 30:
            print(f"   ... et {len(unused_classes) - 30} autres")
    
    if high_specificity:
        print(f"\n⚠️  SÉLECTEURS HAUTE SPÉCIFICITÉ (premiers 20):")
        for i, (cls, spec) in enumerate(high_specificity[:20], 1):
            print(f"   {i:2d}. .{cls} (spécificité: {spec})")
    
    if duplicates:
        print(f"\n⚠️  RÈGLES DUPLIQUÉES (premiers 10):")
        for i, (decls, selectors) in enumerate(duplicates[:10], 1):
            print(f"   {i:2d}. {len(selectors)} sélecteurs avec mêmes déclarations:")
            for sel in selectors[:3]:
                print(f"       - {sel}")
            if len(selectors) > 3:
                print(f"       ... et {len(selectors) - 3} autres")
    
    print("\n" + "=" * 80)
    print("Analyse terminée. Vérifiez manuellement les résultats avant suppression.")
    print("=" * 80)

if __name__ == "__main__":
    main()
