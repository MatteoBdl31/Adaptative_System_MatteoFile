# Changelog - LOT 3: Extraction Composants Récurrents

## Objectif
Créer de nouveaux composants selon la convention BEM avec préfixe `.c-*` pour améliorer la maintenabilité et la cohérence, en parallèle des classes existantes (sans les modifier).

## Modifications

### Sections touchées
- **Nouvelle section créée** : `/* COMPONENTS (BEM Convention - .c-*) */` (lignes ~698-900)
- **Placement** : Après la section Leaflet Overrides, avant Responsive Design

### Nouveaux composants créés

#### Component: Button (`.c-Button`)
- `.c-Button` - Base button component
- `.c-Button--primary` - Primary variant (gradient)
- `.c-Button--secondary` - Secondary variant
- `.c-Button--ghost` - Ghost variant (transparent)
- `.c-Button--sm` - Small size variant
- États: `.is-disabled`, `.is-loading`

**Basé sur** : `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn--sm`

#### Component: Card (`.c-Card`)
- `.c-Card` - Base card component
- `.c-Card--elevated` - Elevated variant (more shadow)
- `.c-Card__header` - Card header element
- `.c-Card__title` - Card title element
- `.c-Card__description` - Card description element
- `.c-Card__body` - Card body element
- `.c-Card__footer` - Card footer element

**Basé sur** : `.card`, `.card__header`, `.card__title`, `.card__description`

#### Component: Badge (`.c-Badge`)
- `.c-Badge` - Base badge component
- `.c-Badge--primary` - Primary variant
- `.c-Badge--success` - Success variant (green)
- `.c-Badge--warning` - Warning variant (yellow)
- `.c-Badge--error` - Error variant (red)
- `.c-Badge--collaborative` - Collaborative variant (red)
- `.c-Badge--recommended` - Recommended variant (blue)
- `.c-Badge--sm` - Small size variant

**Basé sur** : `.badge`, `.badge-primary`, `.badge-success`, `.badge-warning`, `.badge--collaborative`, `.badge--sm`

#### Component: Form (`.c-Form`)
- `.c-Form` - Form container
- `.c-Form__group` - Form group wrapper
- `.c-Form__label` - Form label
- `.c-Form__input` - Text input
- `.c-Form__select` - Select dropdown
- `.c-Form__textarea` - Textarea
- `.c-Form__help` - Help text
- `.c-Form__error` - Error message

**Basé sur** : `.form-group`, `.form-label`, `.form-input`, `.form-select`

### Tokens ajoutés/modifiés
Aucun nouveau token (utilisation des tokens existants créés dans LOT 2)

### Classes existantes préservées
✅ **Toutes les classes existantes restent intactes** :
- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`
- `.card`, `.card__header`, `.card__title`, `.card__description`
- `.badge`, `.badge-primary`, `.badge-success`, `.badge-warning`
- `.form-group`, `.form-label`, `.form-input`, `.form-select`

**Aucune classe existante n'a été modifiée ou supprimée.**

### Suppressions
Aucune suppression - Tous les composants sont créés en parallèle

## Risques à vérifier

### ⚠️ VALIDATION OBLIGATOIRE AVANT UTILISATION

**Note importante** : Ces nouveaux composants sont créés mais **non encore utilisés** dans les templates. Ils sont disponibles pour une migration progressive future.

1. **Compatibilité**
   - [ ] Les classes existantes fonctionnent toujours (`.btn`, `.card`, `.badge`, `.form-*`)
   - [ ] Aucune régression visuelle sur les pages existantes

2. **Nouveaux composants (si utilisés dans le futur)**
   - [ ] `.c-Button` et variantes : affichage correct, hover, disabled
   - [ ] `.c-Card` et variantes : ombres, hover, structure
   - [ ] `.c-Badge` et variantes : couleurs, tailles
   - [ ] `.c-Form` et éléments : focus, disabled, erreurs

3. **États**
   - [ ] `.is-disabled`, `.is-loading` fonctionnent correctement
   - [ ] Hover states fonctionnent sur tous les composants

## Ordre de cascade
✅ **Aucun changement** - Les nouveaux composants sont ajoutés après les sections existantes, donc :
- Les classes existantes gardent leur spécificité
- Les nouveaux composants `.c-*` ont une spécificité équivalente mais ne remplacent pas les anciens
- Pas de conflit de cascade

## Fichiers impactés
- `adaptive_quiz_system/static/style.css` uniquement

## Sélecteurs créés
**Nouveaux sélecteurs créés** (non utilisés encore) :
- `.c-Button` et variantes (7 sélecteurs)
- `.c-Card` et variantes (7 sélecteurs)
- `.c-Badge` et variantes (8 sélecteurs)
- `.c-Form` et éléments (9 sélecteurs)

**Total** : ~31 nouveaux sélecteurs de composants

## Migration future (optionnelle)

Si migration progressive souhaitée dans les templates :
1. Remplacer progressivement `.btn` → `.c-Button`
2. Remplacer progressivement `.card` → `.c-Card`
3. Remplacer progressivement `.badge` → `.c-Badge`
4. Remplacer progressivement `.form-*` → `.c-Form__*`

**Important** : La migration doit être faite template par template, avec tests à chaque étape.

## Notes techniques
- Tous les composants utilisent les tokens CSS créés dans LOT 2
- Convention BEM respectée : `.c-Component`, `.c-Component--variant`, `.c-Component__element`
- États utilisent la convention `.is-*` (pas `.c-Component.is-*` pour éviter la spécificité excessive)
- Les composants sont basés sur les styles existants mais avec une structure plus claire
- Aucun changement de comportement - seulement création de nouvelles classes en parallèle
