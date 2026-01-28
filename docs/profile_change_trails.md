# Which trails change profile category?

This doc answers: **for each user, which trail(s) from your dummy data should you add (complete) so that the user's profile category changes** and the "You've evolved!" celebration pops up.

## How to get the full list

From the project root or from `adaptive_quiz_system` run:

```bash
python scripts/find_profile_change_trails.py
```

(or `python -m scripts.find_profile_change_trails` when run from `adaptive_quiz_system`)

The script:

1. Uses only trails that have dummy data in `data/dummy_smartwatch/` (trail_id from each JSON).
2. For each user with at least 2 completed trails, simulates adding one more completed trail.
3. If the detected profile changes, it prints that (user, trail, new profile).

At the end it prints a **quick reference**: one trail per user that causes a profile change.

## Interpretating the output

- **User (id) [current profile]** – User name, ID, and current detected profile.
- **Add trail "…" (id=…)** – Completing this trail (and only this one extra) would change their profile.
- **New profile** – The profile they would get after that completion.

Trails listed are only those that appear in `data/dummy_smartwatch/*.json` (by `trail_id`), so you can complete them using those files.

## Example (illustrative)

From a typical run you might see:

| User   | Current profile   | Add this trail (from dummy data)      | New profile         |
|--------|-------------------|----------------------------------------|---------------------|
| Alice  | explorer          | Via Alpina Red R113                    | performance_athlete |
| Bob    | casual            | Marchastel - Lac Saint-Andéol          | contemplative       |
| …      | …                 | …                                     | …                   |

So for **Bob (casual)**, completing **Marchastel - Lac Saint-Andéol** (using the matching dummy file if you have one) will flip the category to **contemplative** and trigger the celebration.

## Profile names (French labels)

The app shows French labels. Mapping:

- `elevation_lover` → L'Amateur de dénivelé
- `performance_athlete` → Le Sportif de performance
- `contemplative` → Le Contemplatif
- `casual` → Le Randonneur occasionnel
- `family` → La Famille / Groupe hétérogène
- `explorer` → L'Explorateur / Aventurier
- `photographer` → Le Photographe / Créateur de contenu

## Implementation detail

Profile is derived from **all** completed trails (distance, elevation, difficulty, duration, landscapes, etc.). Adding one trail can move means/medians enough so that another profile wins. The script uses `UserProfiler.detect_profile_from_trail_list()` to simulate "current completed trails + this trail" without writing to the DB.
