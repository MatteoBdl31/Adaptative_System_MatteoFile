# Changelog - LOT 1: Isolation des Overrides Leaflet

## Objectif
Isoler toutes les surcharges CSS pour Leaflet dans une section dédiée et documentée, facilitant la maintenance et réduisant les risques de régression.

## Modifications

### Sections touchées
- **Nouvelle section créée** : `/* LEAFLET OVERRIDES */` (lignes ~591-658)
- **Section supprimée** : Règles Leaflet dispersées dans `.komoot-map-container` (lignes ~4681-4714)
- **Section supprimée** : Règles Leaflet dans `.trail-popup-wrapper` (lignes ~5851-5857)

### Règles regroupées

#### Leaflet Map Container Overrides (komoot-map-container)
- `.komoot-map-container .leaflet-container` - Position relative, dimensions, transform
- `.komoot-map-container .leaflet-map-pane` - Position relative, transform
- `.komoot-map-container .leaflet-tile-pane` - Transform uniquement (position préservée)
- `.komoot-map-container .leaflet-container, .komoot-map-container .leaflet-map-pane` - Duplication consolidée
- `.komoot-map-container .leaflet-tile` - Transform pour tiles individuelles

#### Leaflet Popup Overrides (trail-popup-wrapper)
- `.trail-popup-wrapper .leaflet-popup-content-wrapper` - Padding, border-radius, box-shadow
- `.trail-popup-wrapper .leaflet-popup-content` - Margin, padding, min-width

### Documentation ajoutée
- Section header avec avertissement de zone sensible
- Commentaires expliquant les règles critiques
- Liste des classes Leaflet natives à ne pas renommer
- Instructions de validation avant modification

### Tokens ajoutés/modifiés
Aucun (ce lot ne concerne que la réorganisation)

### Nouveaux composants/utilitaires créés
Aucun (isolation uniquement)

### Suppressions
- **Aucune suppression de code** - Toutes les règles ont été déplacées, pas supprimées
- Suppression des duplications (règles Leaflet maintenant centralisées)

## Risques à vérifier

### ⚠️ VALIDATION OBLIGATOIRE AVANT MERGE

1. **Cartes Leaflet**
   - [ ] Carte principale (page all_trails, demo) : affichage correct, scroll fonctionnel
   - [ ] Carte détail sentier : positionnement, zoom, pan fonctionnels
   - [ ] Carte komoot-map-container : scroll avec container, pas fixé au viewport

2. **Popups Leaflet**
   - [ ] Popups sur carte : affichage, positionnement, fermeture
   - [ ] Style `.trail-popup-wrapper` : padding, border-radius, ombre
   - [ ] Contenu popup : min-width respecté, pas de débordement

3. **Contrôles Leaflet**
   - [ ] Contrôles zoom : visibles, fonctionnels
   - [ ] Contrôles layers : si présents, fonctionnels
   - [ ] Responsive mobile : contrôles accessibles

4. **Z-index et superposition**
   - [ ] Modales vs carte : modales au-dessus de la carte
   - [ ] Tooltips vs carte : tooltips visibles
   - [ ] Dropdowns vs carte : dropdowns au-dessus

5. **Responsive mobile**
   - [ ] Cartes sur mobile : dimensions correctes, scroll fonctionnel
   - [ ] Popups sur mobile : taille adaptée, pas de débordement

6. **Transform et position**
   - [ ] Tiles Leaflet : positionnement correct, pas de décalage
   - [ ] Map pane : scroll avec container, pas fixé
   - [ ] Pas de "pinning" des tiles au viewport

## Ordre de cascade
✅ **Aucun changement** - Les règles ont été déplacées mais l'ordre de spécificité reste identique :
- `.komoot-map-container .leaflet-*` (spécificité: 0,2,0)
- `.trail-popup-wrapper .leaflet-popup-*` (spécificité: 0,2,0)

## Fichiers impactés
- `adaptive_quiz_system/static/style.css` uniquement

## Sélecteurs impactés
- `.komoot-map-container .leaflet-container`
- `.komoot-map-container .leaflet-map-pane`
- `.komoot-map-container .leaflet-tile-pane`
- `.komoot-map-container .leaflet-tile`
- `.trail-popup-wrapper .leaflet-popup-content-wrapper`
- `.trail-popup-wrapper .leaflet-popup-content`

**Aucun sélecteur renommé ou supprimé** - Tous les sélecteurs existants sont préservés.

## Notes techniques
- Tous les `!important` sont préservés (nécessaires pour surcharger Leaflet)
- Les commentaires critiques sont conservés et enrichis
- La section est placée après les utilitaires et avant le responsive (ordre ITCSS)
