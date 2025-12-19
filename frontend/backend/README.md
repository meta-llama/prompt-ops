# Prompt Ops Frontend Backend

This is a FastAPI backend for the prompt-ops frontend interface. It provides API endpoints for optimizing prompts using OpenAI's GPT models and the prompt-ops library.

## Setup

1. **Install the prompt-ops package in development mode** (from the repository root):
```bash
cd /path/to/prompt-ops  # Navigate to the repo root
pip install -e .
```

2. **Install backend-specific dependencies**:
```bash
cd frontend/backend
pip install -r requirements.txt
```

3. **Set up your environment variables**:
   - Copy `.env.example` to `.env` (if available)
   - Add your OpenAI API key and OpenRouter API key to the `.env` file

## Running the Server

Start the FastAPI server with:
```bash
uvicorn main:app --reload --port 8001
```

The API will be available at http://localhost:8001

## API Endpoints

### POST /api/enhance-prompt

Enhances a prompt using OpenAI's GPT model.

**Request Body:**
```json
{
  "prompt": "Your prompt text here"
}
```

**Response:**
```json
{
  "optimizedPrompt": "Enhanced prompt text"
}
```

### POST /api/migrate-prompt

Optimizes a prompt using the prompt-ops library.

**Request Body:**
```json
{
  "prompt": "Your prompt text here",
  "config": {
    "taskModel": "Llama 3.3 70B",
    "proposerModel": "Llama 3.1 8B",
    "optimizer": "MiPro",
    "dataset": "Q&A",
    "metrics": "Exact Match",
    "useLlamaTips": true
  }
}
```

**Response:**
```json
{
  "optimizedPrompt": "Optimized prompt text"
}
```

## Integration with prompt-ops

This backend serves as a development interface for the prompt-ops library, providing web API access to prompt optimization features. When this frontend is eventually integrated into the main prompt-ops repository, this backend functionality will be incorporated into the library's core API structure.

## Development Notes

- The backend automatically adds the `src/` directory to the Python path to ensure local imports work correctly
- The `prompt_ops` package should be installed in editable mode (`pip install -e .`) from the repo root for development
