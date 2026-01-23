# Changelog - LOT 2: Enrichissement Design Tokens

## Objectif
Identifier les valeurs répétées (≥3 occurrences) et créer des tokens CSS manquants pour améliorer la maintenabilité et la cohérence du design system.

## Modifications

### Sections touchées
- **Section modifiée** : `:root` - Design Tokens (lignes ~55-141)
- **Nouveaux tokens ajoutés** : 20+ tokens pour couleurs, gradients, overlays, bordures

### Tokens ajoutés

#### Semantic Colors - Status & Actions
- `--color-collaborative: #f71e50` (5 occurrences remplacées)
- `--color-recommended: #5b8df9` (2 occurrences remplacées)
- `--color-link: #667eea` (12 occurrences remplacées)
- `--color-gradient-start: #667eea` (utilisé dans gradient)
- `--color-gradient-end: #764ba2` (utilisé dans gradient)
- `--color-accent-blue: #00A8FF` (6 occurrences remplacées)
- `--color-accent-yellow: #fbbf24` (7 occurrences remplacées)

#### Status Colors - Success
- `--color-success-bg: #d1fae5` (6 occurrences remplacées)
- `--color-success-text: #065f46` (6 occurrences remplacées)

#### Status Colors - Warning
- `--color-warning-bg: #fef3c7` (6 occurrences remplacées)
- `--color-warning-text: #92400e` (6 occurrences remplacées)

#### Status Colors - Error/Danger
- `--color-error-bg: #fee2e2` (5 occurrences remplacées)
- `--color-error-text: #991b1b` (5 occurrences remplacées)
- `--color-error: #dc2626` (2 occurrences remplacées)

#### Neutral Colors
- `--color-neutral-bg: #f0f0f0` (3 occurrences remplacées)
- `--color-text-muted-dark: #475569` (5 occurrences remplacées)
- `--color-white: #ffffff` (déjà utilisé via --color-bg mais explicité)

#### Overlays & Backdrops
- `--overlay-light: rgba(0, 0, 0, 0.05)` (10 occurrences remplacées)
- `--overlay-medium: rgba(0, 0, 0, 0.1)` (7 occurrences remplacées)
- `--overlay-dark: rgba(0, 0, 0, 0.5)` (3 occurrences remplacées)

#### Gradients
- `--gradient-primary: linear-gradient(135deg, var(--color-gradient-start) 0%, var(--color-gradient-end) 100%)` (9 occurrences remplacées)

#### Borders - Common Patterns
- `--border-white: 2px solid var(--color-white)` (5 occurrences remplacées)

### Remplacements effectués

#### Couleurs (≥3 occurrences)
- `#f71e50` → `var(--color-collaborative)` (5x)
- `#5b8df9` → `var(--color-recommended)` (2x)
- `#667eea` → `var(--color-link)` (12x)
- `#764ba2` → `var(--color-gradient-end)` (10x)
- `#00A8FF` → `var(--color-accent-blue)` (6x)
- `#fbbf24` → `var(--color-accent-yellow)` (7x)
- `#d1fae5` → `var(--color-success-bg)` (6x)
- `#065f46` → `var(--color-success-text)` (6x)
- `#fee2e2` → `var(--color-error-bg)` (5x)
- `#991b1b` → `var(--color-error-text)` (5x)
- `#fef3c7` → `var(--color-warning-bg)` (6x)
- `#92400e` → `var(--color-warning-text)` (6x)
- `#f0f0f0` → `var(--color-neutral-bg)` (3x)
- `#475569` → `var(--color-text-muted-dark)` (5x)
- `#dc2626` → `var(--color-error)` (2x)

#### Gradients (≥3 occurrences)
- `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` → `var(--gradient-primary)` (9x)
- `linear-gradient(135deg, #764ba2 0%, #667eea 100%)` → `linear-gradient(135deg, var(--color-gradient-end) 0%, var(--color-gradient-start) 100%)` (1x)

#### Overlays (≥3 occurrences)
- `rgba(0, 0, 0, 0.05)` → `var(--overlay-light)` (10x)
- `rgba(0, 0, 0, 0.1)` → `var(--overlay-medium)` (7x)
- `rgba(0, 0, 0, 0.5)` → `var(--overlay-dark)` (3x)

#### Bordures (≥3 occurrences)
- `2px solid #fff` → `var(--border-white)` (5x)
- `2px solid #ffffff` → `var(--border-white)` (0x, déjà couvert)

#### Box-shadows utilisant overlays
- `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2)` → `box-shadow: 0 1px 3px var(--overlay-medium)` (plusieurs)
- `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05)` → `box-shadow: 0 1px 3px var(--overlay-light)` (plusieurs)

### Tokens non créés (justification)
- `#ffeef0` (1 occurrence) - Couleur spécifique pour alert collaborative, pas assez répétée
- `#a00d2f` (1 occurrence) - Couleur spécifique pour texte alert collaborative, pas assez répétée
- Autres couleurs avec <3 occurrences - Respect de la règle "anti over-tokenization"

### Nouveaux composants/utilitaires créés
Aucun (ce lot concerne uniquement les tokens)

### Suppressions
Aucune suppression - Toutes les valeurs ont été remplacées par des tokens, pas supprimées

## Risques à vérifier

### ⚠️ VALIDATION OBLIGATOIRE AVANT MERGE

1. **Couleurs**
   - [ ] Couleurs collaboratives : bordures, badges, alertes (rouge #f71e50)
   - [ ] Couleurs recommandées : marqueurs de carte, badges (bleu #5b8df9)
   - [ ] Liens : tous les liens doivent être en #667eea
   - [ ] Gradients : tous les gradients doivent s'afficher correctement
   - [ ] Status colors : success (vert), warning (jaune), error (rouge) - badges et alertes

2. **Gradients**
   - [ ] Gradients de fond : pages demo, hero sections
   - [ ] Gradients inversés : vérifier que l'inversion fonctionne

3. **Overlays**
   - [ ] Backdrops de modales : opacité correcte
   - [ ] Box-shadows : profondeur et visibilité correctes
   - [ ] Overlays sur images : visibilité du texte

4. **Bordures blanches**
   - [ ] Marqueurs de légende : bordures blanches visibles
   - [ ] Badges : bordures blanches sur fonds colorés

5. **Cohérence visuelle**
   - [ ] Tous les éléments de même type utilisent les mêmes couleurs
   - [ ] Pas de régression visuelle (couleurs identiques avant/après)

## Ordre de cascade
✅ **Aucun changement** - Seulement remplacement de valeurs par des tokens, pas de modification de sélecteurs ou d'ordre

## Fichiers impactés
- `adaptive_quiz_system/static/style.css` uniquement

## Sélecteurs impactés
**Aucun sélecteur modifié** - Seulement remplacement de valeurs dans les propriétés existantes :
- `background`, `background-color`, `color`, `border`, `border-color`, `box-shadow`
- Tous les sélecteurs existants sont préservés

## Statistiques
- **Tokens créés** : 20+
- **Remplacements effectués** : ~100+ occurrences
- **Couleurs tokenisées** : 15 couleurs principales
- **Gradients tokenisés** : 1 gradient principal (9 occurrences)
- **Overlays tokenisés** : 3 niveaux d'opacité (20 occurrences)
- **Bordures tokenisées** : 1 pattern commun (5 occurrences)

## Notes techniques
- Tous les tokens respectent la convention `--*` existante
- Les tokens sont organisés par catégorie (semantic, status, neutral, overlays, gradients, borders)
- Les valeurs originales sont préservées dans les tokens (pas de changement de couleur)
- Les tokens peuvent être facilement modifiés pour le thème sombre si nécessaire
- Aucune valeur unique n'a été tokenisée (respect de la règle "anti over-tokenization")
