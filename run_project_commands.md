# How to Run the Retirement Planning Tool Project

This guide provides the terminal commands to set up and run the backend (FastAPI) and frontend (Gradio) components of the Retirement Planning Tool.

## Prerequisites

1.  **Python 3.x installed.**
2.  **Manually delete old directories** (if you haven't already):
    `chatbot_interface/`, `user_profile/`, `analysis_engine/`, `recommendation_engine/`, `external_data_services/`, `utils/`.

## Setup and Running

Follow these steps in your terminal, from the project's root directory:

1.  **Set Up a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    ```

2.  **Activate the Virtual Environment:**
    *   **Windows (Command Prompt/PowerShell):**
        ```bash
        .venv\Scripts\activate
        ```
    *   **macOS/Linux (bash/zsh):**
        ```bash
        source .venv/bin/activate
        ```
    *(You should see `(.venv)` at the beginning of your terminal prompt.)*

3.  **Install Dependencies:**
    (Ensure your virtual environment is activated)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` File (Optional but Recommended for Configuration):**
    Create a file named `.env` in the root of your project. Add necessary configurations, especially the `SECRET_KEY`.
    Example content for `.env`:
    ```env
    SECRET_KEY="your_very_strong_and_unique_secret_key_here_32_bytes_long"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    # CHROMA_DB_PATH="./chroma_db_data"
    # CHROMA_COLLECTION_NAME="retirement_knowledge"
    ```

5.  **Run the Backend (FastAPI Application):**
    (Open a terminal, activate virtual environment)
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   The backend API will typically be accessible at `http://localhost:8000`.
    *   API documentation (Swagger UI) at `http://localhost:8000/docs`.

6.  **Run the Frontend (Gradio UI):**
    (Open a **new** terminal window or tab, activate virtual environment)
    ```bash
    python ui/app.py
    ```
    *   The Gradio UI will typically be accessible at a local URL like `http://127.0.0.1:7860` (check the terminal output from this command for the exact URL).

## Summary of Running Commands (after setup):

*   **Terminal 1 (Backend):**
    (Activate `.venv`)
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
*   **Terminal 2 (Frontend):**
    (Activate `.venv`)
    ```bash
    python ui/app.py
    ```

``` 