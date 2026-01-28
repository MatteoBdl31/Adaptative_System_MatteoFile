# CSS Refactor Rules — Non-regression + Controlled Deep Refactor

## CONTEXTE PROJET
- Flask + Jinja2 (rendu serveur), JS vanilla, Leaflet.
- Un unique `style.css` (~5100 lignes) avec design system (variables CSS).
- Objectif : refactor “en profondeur” pour maintenabilité et cohérence, sans casser le rendu.

---

## RÈGLES DE NON-RÉGRESSION (CRITIQUES)

1) Ne pas renommer ni supprimer aucun sélecteur potentiellement utilisé par :
   - templates Jinja (`*.html`)
   - JS vanilla (`querySelector`, `classList`, toggles)
   - Leaflet (classes `.leaflet-*`, `.marker-*`, etc.)
   - attributs `data-*` et `aria-*` utilisés comme hooks

2) Ne pas modifier les valeurs comportementales sans preuve :
   - `display` / `position` / `z-index` / `overflow` (risque layout)
   - interactions (`hover` / `focus` / `active`), transitions/animations
   - règles responsives `@media` (conditions et breakpoints)

3) Ne pas “optimiser” via des shorthands risqués (`background`, `font`, `border`) si overrides partiels existent.

4) Toute suppression (règle, propriété, media query) doit être justifiée par :
   - recherche d’usage (grep)
   - report (où c’était utilisé / pourquoi c’est supprimable)

---

## MÉTHODE DE REFACTOR (OBLIGATOIRE, PAR LOTS)

- Refactoriser par petites PR/logiques (ou sections), jamais “big bang”.
- Après chaque lot : fournir un changelog et une liste de fichiers/sélecteurs impactés.
- Ne jamais déplacer des blocs si cela change l’ordre de cascade.
  - Si déplacement nécessaire : l’indiquer explicitement et expliquer pourquoi c’est équivalent.

---

## CIBLE D’ARCHITECTURE CSS (RECOMMANDÉE POUR FLASK/JINJA)
Adopter une structure de type ITCSS légère + conventions BEM :

### A) SETTINGS / TOKENS
- `:root` tokens existants (couleurs, espaces, radius, shadow, z-index, durées)
- ajouter tokens manquants si répétitions ≥ 3

### B) GENERIC / BASE
- reset minimal, typographie, éléments HTML (`a`, `button`, `input`, `table`)

### C) LAYOUT
- wrappers, grids, containers, page shells, sidebar/header/footer

### D) COMPONENTS (BEM)
- `.c-Button`, `.c-Card`, `.c-Filter`, `.c-Modal`, `.c-Toast`, `.c-MapPanel`, etc.
- variantes : `.c-Button--primary`, états : `.is-active`, `.is-loading`

### E) UTILITIES
- `.u-hidden`, `.u-flex`, `.u-gap-*`, `.u-text-center`, etc. (très petites, réutilisables)

### F) OVERRIDES / PAGES (en dernier)
- correctifs spécifiques, idéalement à réduire progressivement

---

## CONVENTIONS DE NOMMAGE (POUR ÉVITER LES COLLISIONS)
- Composants : `.c-*`
- Layout : `.l-*`
- Utilitaires : `.u-*`
- États : `.is-*` / `.has-*`
- JS hooks (si existants) : `.js-*`
  - ne jamais styliser `.js-*`; hooks uniquement
- Conserver les classes historiques ; si création de nouvelles classes, suivre ces préfixes.

---

## PRIORITÉS DE REFACTOR (DANS CET ORDRE)

1) CARTOGRAPHIE LEAFLET (ZONE SENSIBLE)
- Isoler toutes les surcharges Leaflet dans une section “Leaflet overrides”
- Ne pas toucher aux classes Leaflet natives ; seulement ajouter des surcharges ciblées et documentées
- Vérifier z-index, popups, tooltips, contrôles (zoom, layers), responsive mobile

2) DESIGN SYSTEM / TOKENS
- Normaliser tokens : `--color-*`, `--space-*`, `--radius-*`, `--shadow-*`, `--z-*`, `--duration-*`
- Remplacer uniquement les répétitions évidentes (≥ 3) par `var()`
- Éviter de transformer des valeurs uniques en tokens (anti “over-tokenization”)

3) COMPOSANTS UI RÉCURRENTS
- Identifier (par recherche) les patterns répétés : boutons, cartes sentier, badges météo, filtres, formulaires, pagination, modales, toasts
- Extraire en composants `.c-*` sans casser :
  - créer nouvelles classes en parallèle
  - appliquer les nouvelles classes dans templates progressivement (si autorisé)
  - garder les anciennes règles jusqu’à migration complète

4) SPÉCIFICITÉ ET CASCADE
- Réduire la spécificité excessive (chaînes profondes)
- Bannir l’ajout de `!important` ; réduire l’existant si possible, mais seulement si rendu prouvé identique
- Utiliser `:where()` uniquement pour réduire spécificité quand c’est explicitement voulu et testé

5) RESPONSIVE
- Choisir une stratégie et l’appliquer partout :
  - option recommandée : regrouper par composant avec ses `@media` à proximité
- Standardiser les breakpoints (commentés ou tokens), sans changer leurs valeurs

6) NETTOYAGE / DETTES
- Détecter règles mortes (seulement avec preuve d’absence d’usage)
- Dédupliquer règles strictement identiques en utilitaires ou composants, sans changer l’ordre d’application

---

## CE QUI EST AUTORISÉ (REFACTOR “PROFOND” MAIS CONTRÔLÉ)
- Réorganisation par sections (si l’ordre final respecte la cascade et/ou si les overrides restent en dernier)
- Extraction de composants (BEM) et utilitaires
- Introduction de tokens raisonnables
- Simplification de sélecteurs quand équivalence prouvée
- Ajout de commentaires structurants

---

## CE QUI EST INTERDIT (OU NÉCESSITE UN STOP + JUSTIFICATION)
- Renommer/supprimer sélecteurs existants sans migration et preuve d’usage
- Changer conditions `@media` / `@supports`
- Remplacer massivement longhand ↔ shorthand (surtout `background` / `font`)
- “Optimiser” en minifiant ou en réordonnant des propriétés pour esthétique

---

## LIVRABLES À CHAQUE LOT
1) CSS refactorisé pour le lot
2) Changelog (bullet points) incluant :
   - sections touchées
   - tokens ajoutés/modifiés
   - nouveaux composants/utilitaires créés
   - suppressions avec preuve d’absence d’usage
3) Liste “risques à vérifier” (map, popups, formulaires, états hover/focus, responsive)

---

## VALIDATION (À EXÉCUTER AVANT DE CONCLURE)
- Vérifier pages clés :
  - page carte Leaflet + popups + contrôles
  - page recommandations + cartes sentiers + filtres
  - login/profil + formulaires
  - mode démo côte à côte
- Vérifier états : `hover` / `focus` / `active` / `disabled`, erreurs formulaire, loading, mobile
- Vérifier z-index (modales vs carte), overflow, scroll
- Vérifier contraste et accessibilité focus visible

---

## OUTILS (SI AUTORISÉS)
- Stylelint (config standard) pour cohérence + erreurs
- Interdire l’auto-fix destructif (pas de tri de propriétés si ça change le comportement)
