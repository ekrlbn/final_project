# RETIREMENT PLANNING TOOL

## Setup on macOS

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.exe

# Set your Google API key (required before running)
export GOOGLE_API_KEY="your-google-api-key"

# Run the application
python3 app.py
```

## Setup on Windows

```bash
# Create a virtual environment
virtualenv.exe .venv

# Activate the virtual environment
source .venv/Scripts/activate

# Install dependencies
pip install -r requirements.exe

# Set your Google API key (required before running)
set GOOGLE_API_KEY=your-google-api-key

# Run the application
python app.py
```