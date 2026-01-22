 # Architecture
 
 ## Component overview
 The system is organized into a Flask web layer, a backend services layer, a recommendation engine,
 and a data ingestion pipeline. SQLite databases are used for persistence.
 
 ### System context (Mermaid)
 
 ```mermaid
 flowchart LR
     user[UserBrowser] --> flaskApp[FlaskApp]
     flaskApp --> templates[JinjaTemplates]
     flaskApp --> staticJs[StaticJS]
 
     flaskApp --> backendServices[BackendServices]
     backendServices --> usersDb[(users.db)]
     backendServices --> trailsDb[(trails.db)]
     backendServices --> rulesDb[(rules.db)]
 
     flaskApp --> recEngine[RecommendationEngine]
     recEngine --> backendServices
 
     recEngine --> openMeteo[OpenMeteoAPI]
     recEngine --> openAI[OpenAIorOpenRouter]
 
     dataPipeline[DataPipeline] --> trailsDb
     dataPipeline --> openElevation[OpenElevationAPI]
     dataPipeline --> shapefile[TrailShapefile]
 ```
 
 ## Request lifecycle (high level)
 1. Flask route resolves user, context, and inputs.
 2. `adapt_trails()` delegates to `RecommendationEngine`.
 3. Engine applies rule-based filters, scores trails, enriches weather, ranks results.
 4. Explanation layer builds AI summaries and fallback explanations.
 5. Jinja templates render HTML and attach JS for maps/dashboards.
 
 ### Recommendation pipeline (Mermaid)
 
 ```mermaid
 flowchart LR
     request[RequestContext] --> filters[FilterBuilder]
     filters --> candidates[CandidateTrails]
     candidates --> scoring[TrailScorer]
     scoring --> weather[WeatherEnricher]
     weather --> ranking[TrailRanker]
     ranking --> explanations[ExplanationEnricher]
     explanations --> output[ExactMatchesAndSuggestions]
 ```
 
 ## Data boundaries
 - **Web layer**: `adaptive_quiz_system/app/__init__.py` (routes, template binding).
 - **Backend services**: `adaptive_quiz_system/backend/*` (persistence, analytics, uploads, weather).
 - **Recommendation engine**: `adaptive_quiz_system/recommendation_engine/*`.
 - **Data pipeline**: `adaptive_quiz_system/data_pipeline/*` for shapefile ingestion and seeding.
 
 ## Non-functional considerations
 - **Performance**: weather enrichment is limited to top-scored trails; map rendering is client-side.
 - **Reliability**: external API calls have fallbacks and timeouts; AI explanations degrade gracefully.
 - **Data integrity**: SQLite is the single source of truth for users and trails.
 
## See also
- Backend details: `docs/backend.md`
- Recommendation engine: `docs/recommendation_engine.md`
- Data pipeline: `docs/data_pipeline.md`
- Functional documentation: `docs/functional.md`
