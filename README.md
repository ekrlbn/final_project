# Retirement Planning Tool

This project is a comprehensive, data-driven, and personalized retirement planning tool. It aims to provide users with insights and recommendations based on their health profile, financial status, and retirement goals, primarily through a conversational interface.

## Scope

The system will include the following core capabilities:

*   Collecting and managing user health profile data through conversational interaction.
*   Analyzing user financial status (savings, income, expenses) via a guided dialogue.
*   Generating and explaining personalized retirement age recommendations and projections.
*   Projecting potential healthcare costs in retirement.
*   Performing longevity risk analysis.
*   Suggesting tailored investment options and pension schemes.
*   Providing a user-friendly conversational chatbot interface.
*   Assessing retirement plan sustainability against desired lifestyle.
*   Integrating financial and health data from trusted external sources.

## Project Structure (Initial)

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app definition, backend service orchestration
│   ├── api/                        # API endpoints
│   │   ├── __init__.py
│   │   └── routers/                # Routers for different API groups
│   │       └── __init__.py
│   ├── core/                       # Core logic, configuration
│   │   ├── __init__.py
│   │   └── config.py
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── authentication_service.py
│   │   ├── conversation_service.py
│   │   ├── data_processing_service.py
│   │   └── external_api_service.py
│   ├── models/                     # Pydantic models
│   │   └── __init__.py
│   └── db/                         # Database interactions
│       ├── __init__.py
│       └── chromadb_manager.py
├── llm_agents/                   # LLM-based agents
│   ├── __init__.py
│   ├── retirement_age_calculator.py
│   ├── health_cost_predictor.py
│   └── longevity_risk_analyzer.py
├── ui/                           # Gradio UI components
│   ├── __init__.py
│   └── app.py                      # Gradio interface main file
├── tests/                        # Test suite
│   └── __init__.py
├── requirements.txt              # Project dependencies
└── README.md                     # This file
```

*(Note: The previous directories: `chatbot_interface/`, `user_profile/`, `analysis_engine/`, `recommendation_engine/`, `external_data_services/`, `utils/` should be manually removed as they are replaced by the new `app/` structure.)*

## Future Development

The initial focus will be on a core set of features, with potential for future expansion based on user feedback.

    virtualenv.exe .venv

    source .venv/Scripts/activate

    pip install -r requirements.txt