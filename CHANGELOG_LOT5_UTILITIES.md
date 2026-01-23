# Changelog - LOT 5: Utilitaires

## Objectif
Créer de nouvelles classes utilitaires selon la convention avec préfixe `.u-*` pour améliorer la maintenabilité et la cohérence, en parallèle des classes existantes (sans les modifier).

## Modifications

### Sections touchées
- **Nouvelle section créée** : `/* UTILITIES (Convention - .u-*) */` (lignes ~1130-1500)
- **Placement** : Après la section LAYOUT, avant Responsive Design

### Nouveaux utilitaires créés

#### Display Utilities (6 sélecteurs)
- `.u-hidden` - Display none avec !important
- `.u-block` - Display block
- `.u-inline` - Display inline
- `.u-inline-block` - Display inline-block
- `.u-flex` - Display flex
- `.u-grid` - Display grid

**Basé sur** : `.hidden`, `.flex`, `.grid`

#### Flexbox Utilities (15 sélecteurs)
- `.u-flex-col` - Flex direction column
- `.u-flex-row` - Flex direction row
- `.u-items-center`, `.u-items-start`, `.u-items-end`, `.u-items-stretch` - Align items
- `.u-justify-center`, `.u-justify-between`, `.u-justify-start`, `.u-justify-end`, `.u-justify-around`, `.u-justify-evenly` - Justify content
- `.u-flex-wrap`, `.u-flex-nowrap` - Flex wrap
- `.u-flex-1` - Flex: 1
- `.u-flex-shrink-0` - Flex shrink: 0

**Basé sur** : `.flex`, `.flex-col`, `.items-center`, `.justify-between`

#### Gap Utilities (5 sélecteurs)
- `.u-gap-xs`, `.u-gap-sm`, `.u-gap-md`, `.u-gap-lg`, `.u-gap-xl` - Gap spacing

**Basé sur** : `.gap-sm`, `.gap-md`, `.gap-lg`, `.gap-xl`

#### Margin Utilities (15 sélecteurs)
- `.u-m-0` - Margin: 0
- `.u-mt-0`, `.u-mt-xs`, `.u-mt-sm`, `.u-mt-md`, `.u-mt-lg`, `.u-mt-xl` - Margin top
- `.u-mb-0`, `.u-mb-xs`, `.u-mb-sm`, `.u-mb-md`, `.u-mb-lg`, `.u-mb-xl` - Margin bottom
- `.u-ml-auto`, `.u-mr-auto`, `.u-mx-auto` - Margin auto

**Basé sur** : `.mt-sm`, `.mt-md`, `.mt-lg`, `.mt-xl`, `.mb-sm`, `.mb-md`, `.mb-lg`, `.mb-xl`

#### Padding Utilities (15 sélecteurs)
- `.u-p-0` - Padding: 0
- `.u-p-xs`, `.u-p-sm`, `.u-p-md`, `.u-p-lg`, `.u-p-xl` - Padding all sides
- `.u-px-xs`, `.u-px-sm`, `.u-px-md`, `.u-px-lg` - Padding horizontal
- `.u-py-xs`, `.u-py-sm`, `.u-py-md`, `.u-py-lg` - Padding vertical

**Basé sur** : `.p-sm`, `.p-md`, `.p-lg`, `.p-xl`

#### Text Utilities (18 sélecteurs)
- `.u-text-center`, `.u-text-left`, `.u-text-right` - Text align
- `.u-text-muted`, `.u-text-secondary`, `.u-text-primary` - Text color
- `.u-text-bold`, `.u-text-semibold`, `.u-text-medium`, `.u-text-normal` - Font weight
- `.u-text-xs`, `.u-text-sm`, `.u-text-base`, `.u-text-lg`, `.u-text-xl`, `.u-text-2xl`, `.u-text-3xl`, `.u-text-4xl` - Font size
- `.u-text-uppercase`, `.u-text-lowercase`, `.u-text-capitalize` - Text transform
- `.u-text-nowrap` - White space nowrap
- `.u-text-truncate` - Text truncate with ellipsis

**Basé sur** : `.text-center`, `.text-muted`

#### Width & Height Utilities (4 sélecteurs)
- `.u-w-full`, `.u-w-auto` - Width
- `.u-h-full`, `.u-h-auto` - Height

#### Position Utilities (4 sélecteurs)
- `.u-relative` - Position relative
- `.u-absolute` - Position absolute
- `.u-fixed` - Position fixed
- `.u-sticky` - Position sticky

#### Overflow Utilities (5 sélecteurs)
- `.u-overflow-hidden` - Overflow hidden
- `.u-overflow-auto` - Overflow auto
- `.u-overflow-scroll` - Overflow scroll
- `.u-overflow-x-auto` - Overflow-x auto
- `.u-overflow-y-auto` - Overflow-y auto

#### Visibility Utilities (2 sélecteurs)
- `.u-visible` - Visibility visible
- `.u-invisible` - Visibility hidden

#### Screen Reader Only (1 sélecteur)
- `.u-sr-only` - Screen reader only (accessibilité)

**Basé sur** : `.sr-only`

#### Pointer Events Utilities (2 sélecteurs)
- `.u-pointer-events-none` - Pointer events none
- `.u-pointer-events-auto` - Pointer events auto

#### Cursor Utilities (3 sélecteurs)
- `.u-cursor-pointer` - Cursor pointer
- `.u-cursor-not-allowed` - Cursor not-allowed
- `.u-cursor-default` - Cursor default

#### Opacity Utilities (3 sélecteurs)
- `.u-opacity-0` - Opacity 0
- `.u-opacity-50` - Opacity 0.5
- `.u-opacity-100` - Opacity 1

#### Z-index Utilities (6 sélecteurs)
- `.u-z-0`, `.u-z-10`, `.u-z-20`, `.u-z-30`, `.u-z-40`, `.u-z-50` - Z-index values

### Tokens ajoutés/modifiés
Aucun nouveau token (utilisation des tokens existants créés dans LOT 2)

### Classes existantes préservées
✅ **Toutes les classes existantes restent intactes** :
- `.flex`, `.flex-col`, `.items-center`, `.justify-between`
- `.gap-sm`, `.gap-md`, `.gap-lg`, `.gap-xl`
- `.mt-sm`, `.mt-md`, `.mt-lg`, `.mt-xl`
- `.mb-sm`, `.mb-md`, `.mb-lg`, `.mb-xl`
- `.p-sm`, `.p-md`, `.p-lg`, `.p-xl`
- `.hidden`, `.sr-only`, `.text-center`, `.text-muted`
- `.grid`, `.grid-cols-1`, `.grid-cols-2`, `.grid-cols-3`, `.grid-cols-4`

**Aucune classe existante n'a été modifiée ou supprimée.**

### Suppressions
Aucune suppression - Tous les utilitaires sont créés en parallèle

## Risques à vérifier

### ⚠️ VALIDATION OBLIGATOIRE AVANT UTILISATION

**Note importante** : Ces nouvelles classes utilitaires sont créées mais **non encore utilisées** dans les templates. Elles sont disponibles pour une migration progressive future.

1. **Compatibilité**
   - [ ] Les classes existantes fonctionnent toujours (`.flex`, `.hidden`, `.text-center`, etc.)
   - [ ] Aucune régression visuelle sur les pages existantes

2. **Nouveaux utilitaires (si utilisés dans le futur)**
   - [ ] Display utilities : fonctionnent correctement
   - [ ] Flexbox utilities : alignement et justification corrects
   - [ ] Spacing utilities : marges et paddings corrects
   - [ ] Text utilities : alignement, couleur, taille corrects
   - [ ] Position utilities : positionnement correct
   - [ ] Overflow utilities : scroll et overflow corrects
   - [ ] Visibility utilities : visibilité correcte
   - [ ] Cursor utilities : curseurs corrects
   - [ ] Opacity utilities : opacité correcte
   - [ ] Z-index utilities : superposition correcte

3. **Spécificité**
   - [ ] Les utilitaires ont une spécificité basse (0,1,0)
   - [ ] Pas de conflit avec les composants ou layout

## Ordre de cascade
✅ **Aucun changement** - Les nouveaux utilitaires sont ajoutés après les sections existantes, donc :
- Les classes existantes gardent leur spécificité
- Les nouveaux utilitaires `.u-*` ont une spécificité équivalente mais ne remplacent pas les anciens
- Pas de conflit de cascade

## Fichiers impactés
- `adaptive_quiz_system/static/style.css` uniquement

## Sélecteurs créés
**Nouveaux sélecteurs créés** (non utilisés encore) :
- Display utilities (6 sélecteurs)
- Flexbox utilities (15 sélecteurs)
- Gap utilities (5 sélecteurs)
- Margin utilities (15 sélecteurs)
- Padding utilities (15 sélecteurs)
- Text utilities (18 sélecteurs)
- Width & Height utilities (4 sélecteurs)
- Position utilities (4 sélecteurs)
- Overflow utilities (5 sélecteurs)
- Visibility utilities (2 sélecteurs)
- Screen Reader Only (1 sélecteur)
- Pointer Events utilities (2 sélecteurs)
- Cursor utilities (3 sélecteurs)
- Opacity utilities (3 sélecteurs)
- Z-index utilities (6 sélecteurs)

**Total** : ~104 nouveaux sélecteurs utilitaires

## Migration future (optionnelle)

Si migration progressive souhaitée dans les templates :
1. Remplacer progressivement `.flex` → `.u-flex`
2. Remplacer progressivement `.hidden` → `.u-hidden`
3. Remplacer progressivement `.text-center` → `.u-text-center`
4. Remplacer progressivement `.text-muted` → `.u-text-muted`
5. Remplacer progressivement `.gap-*` → `.u-gap-*`
6. Remplacer progressivement `.mt-*`, `.mb-*` → `.u-mt-*`, `.u-mb-*`
7. Remplacer progressivement `.p-*` → `.u-p-*`

**Important** : La migration doit être faite template par template, avec tests à chaque étape.

## Notes techniques
- Tous les utilitaires utilisent les tokens CSS créés dans LOT 2
- Convention respectée : `.u-*` pour toutes les classes utilitaires
- Spécificité basse (0,1,0) pour permettre l'override facile
- Une responsabilité unique par classe (principe utilitaire)
- Les utilitaires sont très petites et réutilisables
- Aucun changement de comportement - seulement création de nouvelles classes en parallèle
- Les valeurs sont basées sur les tokens existants (--space-*, --font-size-*, etc.)
