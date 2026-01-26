 # Recommendation Engine
 
 ## Purpose
 The recommendation engine scores and ranks trails based on user profile, context, and a rule-driven
 filter system. It produces two lists: exact matches and suggestions.
 
## Core modules
- `recommendation_engine/engine.py`: Orchestrates the pipeline, including collaborative recommendations integration.
- `recommendation_engine/filters.py`: Rule evaluation and filter building.
- `recommendation_engine/scorer.py`: Criteria-based scoring.
- `recommendation_engine/ranker.py`: Ranking, hard filters, and exact-match checks.
- `recommendation_engine/weather.py`: Parallel weather enrichment.
- `recommendation_engine/explanation.py`: AI explanation caching and fallback.
- `recommendation_engine/config.py`: Environment-driven tuning (includes `DEFAULT_MAX_COLLABORATIVE`).
- `recommendation_engine/debug.py`: Pipeline instrumentation.
- `backend/collaborative_recommendation_service.py`: Collaborative filtering service (queries similar users' completions).
 
## Pipeline
1. Build filters from user and context using rules in `rules.db`.
2. Fetch candidates from `trails.db` (via `backend.db.filter_trails()`).
3. Score candidates with weighted criteria.
4. Enrich top-scored trails with weather forecasts (parallel fetch).
5. Rank into exact matches and suggestions with hard filters.
6. Retrieve collaborative recommendations from similar users (same profile).
7. Integrate collaborative trails: mark overlaps, add top collaborative to suggestions, create dedicated section.
8. Generate explanations (AI or rule-based fallback).
 
### Pipeline diagram (Mermaid)

```mermaid
flowchart LR
    context[ContextAndUser] --> ruleFilters[FilterBuilder]
    ruleFilters --> candidates[CandidateTrails]
    candidates --> scoring[TrailScorer]
    scoring --> weather[WeatherEnricher]
    weather --> ranking[TrailRanker]
    ranking --> collaborative[CollaborativeService]
    collaborative --> explanations[ExplanationEnricher]
    explanations --> result[ExactMatchesSuggestionsCollaborative]
```
 
 ## Filters and rules
 - Rules are stored in `rules.db` and seeded by `backend/init_db.py`.
 - Each rule has a condition and adaptation (e.g., max difficulty, display mode).
 - Rules are evaluated against user attributes, context, and performance fields.
 
 ## Scoring
 - `TrailScorer` evaluates multiple criteria from `criteria.py`.
 - Each criterion emits a `CriterionResult` with a score (0-1) and a match flag.
 - Weighted scores are aggregated into `relevance_percentage`.
 
 Common criteria include:
 - difficulty vs experience/fitness
 - duration vs time available
 - distance, elevation, landscapes, weather match, and safety
 
 ## Ranking and hard filters
 - `TrailRanker` applies hard filters first (season closures, fear of heights, storm risk).
 - Exact matches require a minimum relevance threshold and critical criteria.
 - Suggestions include trails below threshold or failing strict criteria.
 
 ## Weather enrichment
 - `WeatherEnricher` fetches forecasts in parallel for top trails only.
 - Uses Open-Meteo and caches by `(lat, lon, date)` for performance.
 
## Collaborative recommendations
- `CollaborativeRecommendationService` queries trails completed by users with the same profile.
- Filters by minimum rating threshold (default: 3.5/5) and minimum user count (default: 2 users).
- Excludes trails already completed by the current user.
- Integration logic:
  - Trails in exact/suggestions that are also collaborative → marked with `is_collaborative=True` and collaborative metadata.
  - Top 5 collaborative trails (not in exact/suggestions) → added to suggestions with collaborative markers.
  - Remaining collaborative trails → appear in dedicated "collaborative" section.
- Collaborative trails are enriched with metadata: `collaborative_avg_rating`, `collaborative_user_count`, `collaborative_completion_count`.

## Explanation generation
- `ExplanationEnricher` builds prompts via `ContextBuilder`.
- Uses `ExplanationService` to call OpenAI/OpenRouter when API keys are set.
- Falls back to rule-based explanations on errors.
- LRU cache with TTL avoids repeated calls.
 
## Configurable knobs (env)
From `recommendation_engine/config.py`:
- `REC_EXACT_MATCH_THRESHOLD`
- `REC_MIN_CANDIDATES`
- `REC_MAX_FALLBACK_LEVELS`
- `REC_DEBUG`
- `REC_SOFT_FILTER`
- `REC_ALWAYS_RETURN`
- `REC_MIN_RESULTS`
- `REC_MAX_TRAILS`
- `DEFAULT_MAX_COLLABORATIVE` (default: 10) - maximum number of collaborative recommendations to return
 
 ## Debugging
 - `RecommendationDebugger` captures stages, warnings, errors, and fallback usage.
 - Debug info is attached to the metadata returned by the engine.
 
## See also
- Backend routes: `docs/backend.md`
- Architecture: `docs/architecture.md`
- Functional documentation: `docs/functional.md`
