from fastapi import FastAPI

app = FastAPI(title="Retirement Planning Tool API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Retirement Planning Tool API"}

# Placeholder for application initialization logic
def initialize_app():
    print("Retirement Planning Tool - Backend Initializing...")
    # TODO: Initialize database connections (e.g., ChromaDB)
    # TODO: Load models or configurations
    # TODO: Setup external API clients
    pass

if __name__ == "__main__":
    # This part is more for local development/testing of the FastAPI app directly.
    # In production, you'd use Uvicorn from the command line.
    import uvicorn
    initialize_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Previous main.py content (can be adapted or removed):
# def main():
#     print("Retirement Planning Tool - Initializing...")
#     # TODO: Initialize application components
#     # TODO: Start the chatbot interface or API server

# if __name__ == "__main__":
#     main() 